import functools
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta

import pandas as pd
import zeep
from zeep import Settings
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken


def paginated_api_call(
    api_entry_name,
    data_section_name,
    start_record_key="startRecord",
    more_flag_key="MoreFlag",
    max_iterations=100,
):
    def decorator_api_call(func):
        @functools.wraps(func)
        def wrapper(client, *args, **kwargs):
            responses = []
            more_flag = True
            start_record = 1
            iterations = 0

            while more_flag and iterations < max_iterations:
                # Add or update the start record in the kwargs before calling the function
                kwargs[start_record_key] = start_record

                # Get the response from the API via the wrapped function
                # response = func(client, *args, **kwargs)
                response = func(client, **kwargs)

                if response["responseCode"] != "100":
                    raise Exception(f"API error with response: {response}")

                response = serialize_object(response)
                # Process the response data
                data = response.get(data_section_name, [])
                responses.extend(data)

                # Check if more data is available
                more_flag = response.get(more_flag_key, "NotExist") == 1
                # print(
                #     f"========{more_flag = }, {response.get(more_flag_key, 'NotExist') = }"
                # )
                if more_flag:
                    start_record += len(data)

                iterations += 1
                if iterations >= max_iterations:
                    raise Exception(
                        f"Warning: Maximum iterations reached ({max_iterations})"
                    )

            return responses

        return wrapper

    return decorator_api_call


def parse_time_duration(prior_to):
    """
    Parses a time duration string into its numeric and unit parts.

    Args:
    prior_to (str): A string representing the duration, such as "1h", "4.5h", "34d".

    Returns:
    tuple: A tuple containing the numeric part (float) and the unit (str), or None if invalid.
    """
    # Define a regular expression to match valid inputs
    pattern = r"^(\d+(?:\.\d+)?)([hdw])$"

    # Match the input string against the pattern
    match = re.match(pattern, prior_to)

    if match:
        # Extract the numeric part and the unit
        value = float(match.group(1))
        unit = match.group(2)
        return (value, unit)
    else:
        # Return None or raise an error if the input is invalid
        print("Invalid input. Valid examples include '1h', '4.5h', '34d'.")
        return None


def get_past_timestamp(prior_to):
    """
    # Example Usage
    print(get_past_timestamp("2h"))  # 2 hours from now
    print(get_past_timestamp("5d"))  # 5 days from now
    """
    amount, unit = parse_time_duration(prior_to)

    now = datetime.now()
    if unit == "h":
        return now - timedelta(hours=amount)
    elif unit == "d":
        return now - timedelta(days=amount)
    elif unit == "w":
        return now - timedelta(weeks=amount)
    # elif unit == "m":
    #     # Approximate month as 30 days
    #     return now - timedelta(days=amount * 30)
    # elif unit == "y":
    #     # Approximate year as 365 days
    #     return now - timedelta(days=amount * 365)
    else:
        raise ValueError("Invalid unit. Only 'h', 'd', 'w' are accepted.")


class EnergyDataHandler:
    def __init__(self, db_path="energy_data.db"):
        """Initialize the database connection to a persistent SQLite database."""
        self.db_path = db_path
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()

    def create_connection(self):
        """Create and return a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            print(f"SQLite Database connected successfully at {self.db_path}")
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def create_table(self, table_name, schema, primary_keys):
        """
            Create a table if it does not exist, using a defined schema.

            Args:
            table_name (str): Name of the table to create.
            schema (list of tuples): Each tuple contains the column name followed by the SQL type and optionally constraints.

            Example schema:
            table_schema = [
            ("stationTime", "TEXT"),
            ("energyConsumed", "REAL"),
            ("peakPower", "REAL"),
            ("rollingPowerAvg", "REAL"),
            ("sessionID", "INTEGER PRIMARY KEY")
        ]

            primary_keys = ['stationTime', 'sessionID']
        """
        try:
            # Build the column definitions from the schema
            columns = (
                ", ".join([f"{col_name} {data_type}" for col_name, data_type in schema])
                + ","
            )
            # Prepare the PRIMARY KEY clause
            primary_keys_sql = f"PRIMARY KEY ({', '.join(primary_keys)})"

            # Create SQL query for creating the table
            query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
                {primary_keys_sql}
            )
            """
            # print(f"{query = }")
            self.conn.execute(query)
            self.conn.commit()
            print("Table created or verified successfully")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    @staticmethod
    def _filter_duplicates(
        target_df: pd.DataFrame,
        reference_df: pd.DataFrame,
        pk_columns: list[str],
    ):
        """Filter out duplicates based on 'stationTime' and 'sessionID'."""
        target_df_copy = target_df.copy()
        reference_df_copy = reference_df.copy()
        # Force columns to be of type string for comparison
        for column, dtype in reference_df_copy.dtypes.items():
            target_df_copy[column] = target_df_copy[column].astype(str)
            reference_df_copy[column] = reference_df_copy[column].astype(str)
        # Set indices to the columns used for determining duplicates
        # print(f"{pk_columns = }")
        indexed_A = reference_df_copy.set_index(pk_columns)
        indexed_B = target_df_copy.set_index(pk_columns)

        # Filter DataFrameB to only include records that are not in DataFrameA
        # This uses the index created and checks for non-overlapping indices in DataFrameB
        unique_indices = ~indexed_B.index.isin(indexed_A.index)
        target_df_filtered = target_df[unique_indices]
        return target_df_filtered

    def insert_data_to_table(self, table_name, df: pd.DataFrame) -> pd.DataFrame:
        """Insert data from a pandas DataFrame"""
        pk_columns = self.get_primary_key_columns(table_name)
        ref_df = self.query_data_from_table(table_name)
        df_filtered = self._filter_duplicates(
            target_df=df, reference_df=ref_df, pk_columns=pk_columns
        )
        # print(df_filtered)
        if not df_filtered.empty:
            df_filtered.to_sql(table_name, self.conn, if_exists="append", index=False)
            print(f"Data inserted successfully: {len(df_filtered)} records added.")
        else:
            print("No new records to insert; all records are duplicates.")

            """Insert data from a pandas DataFrame."""
        return df_filtered

    def get_primary_key_columns(self, table_name):
        """Retrieve the list of primary key columns for a given table."""
        query = f"PRAGMA table_info({table_name})"
        self.cursor.execute(query)
        columns = []
        for row in self.cursor.fetchall():
            # print(f"{row = }")
            # Column info: (cid, name, type, notnull, dflt_value, pk)
            if row[5] > 0:  # pk value is > 0 if the column is part of the primary key
                columns.append(row[1])
        return columns

    # def insert_data_to_table(self, table_name, df: pd.DataFrame) -> pd.DataFrame:
    #     """Insert data from a pandas DataFrame into the specified table without duplicating primary key entries."""
    #     # Automatically determine primary key columns
    #     primary_key_cols = self.get_primary_key_columns(table_name)

    #     print(f"{primary_key_cols = }")

    #     # Fetch existing primary key values from the database
    #     placeholders = ", ".join("?" for _ in primary_key_cols)
    #     sql_query = f"SELECT {', '.join(primary_key_cols)} FROM {table_name}"
    #     self.cursor.execute(sql_query)
    #     existing_keys = {tuple(row) for row in self.cursor.fetchall()}

    #     # Filter the DataFrame to exclude rows with keys that already exist in the database
    #     mask = df.apply(
    #         lambda row: tuple(row[col] for col in primary_key_cols)
    #         not in existing_keys,
    #         axis=1,
    #     )
    #     df_filtered = df[mask]

    #     print(f"{df_filtered = }")

    #     # Insert new records
    #     if not df_filtered.empty:
    #         df_filtered.to_sql(table_name, self.conn, if_exists="append", index=False)
    #         print(f"Data inserted successfully: {len(df_filtered)} records added.")
    #     else:
    #         print("No new records to insert; all records are duplicates.")

    #     return df_filtered

    def query_data_from_table(self, table_name) -> pd.DataFrame:
        """Query all data from the table (for verification)."""
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            print("Database connection closed")
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {e}")

    def remove_table(self, table_name):
        """
        Remove a specified table from the database.

        Args:
        table_name (str): The name of the table to be removed.
        """
        try:
            # SQL command to drop a table
            query = f"DROP TABLE IF EXISTS {table_name}"
            self.conn.execute(query)
            self.conn.commit()
            print(f"Table {table_name} has been removed successfully.")
        except sqlite3.Error as e:
            print(f"Error removing table {table_name}: {e}")


class ChargePointApi:
    pass

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        SERVICE_WSDL_URL = "https://webservices.fd.chargepoint.com/cp_api_5.1.wsdl"
        settins = Settings()
        self.client = zeep.Client(
            SERVICE_WSDL_URL,
            wsse=UsernameToken(username, password),
            settings=settins,
        )


class Get15minChargingSessionDataAPI(ChargePointApi):
    def __init__(self, username, password):
        super().__init__(username, password)

    def _get15minChargingSessionData(
        self, sessionID: int, energyConsumedInterval: bool = False
    ) -> dict:
        """
        energyConsumedInterval=False, use Cumulative by default
        """
        response = self.client.service.get15minChargingSessionData(
            sessionID=sessionID, energyConsumedInterval=energyConsumedInterval
        )
        serialized_response: dict = serialize_object(response)  # type: ignore
        return serialized_response

    def get15minCharginSessionDataCollection(
        self, session_ids: list[int], isEnergyConsumedIntervalDelta: bool = False
    ) -> list[dict]:
        fifteen_min_data_collection = []
        for i, session_id in enumerate(session_ids):
            single_session_15min_data: dict = self._get15minChargingSessionData(
                sessionID=session_id,
                energyConsumedInterval=isEnergyConsumedIntervalDelta,
            )
            # print(f"{i =} out of {len(session_ids)}, {session_id = }")
            if single_session_15min_data["responseCode"] == "100":
                single_session_15min_data_serial = serialize_object(
                    single_session_15min_data
                )
                try:
                    fifteen_data: list[dict] = single_session_15min_data_serial[
                        "fifteenminData"
                    ]  # type: ignore
                    if isinstance(fifteen_data, list):
                        pass
                    elif isinstance(fifteen_data, dict):
                        fifteen_data = [fifteen_data]
                    else:
                        raise Exception(f"{fifteen_data = } is not a regular data")
                    for d in fifteen_data:
                        d["sessionID"] = session_id
                    fifteen_min_data_collection += fifteen_data
                except Exception as e:
                    print(f"{e = }, {session_id = }")
        return fifteen_min_data_collection

    def get15minCharginSessionDataAPI(
        self,
        stationID: str = None,
        sessionID: int = None,
        userID=None,
        stationName: str = None,
        Address: str = None,
        City: str = None,
        State: str = None,
        Country=None,
        postalCode=None,
        Proximity=None,
        proximityUnit=None,
        fromTimeStamp: str = None,
        toTimeStamp: str = None,
        startRecord: int = None,
        Geo=None,
        stationIDs: list[str] = None,
        activeSessionsOnly=None,
        portNumber: str = None,
    ):
        session_data_res = GetChargingSessionDataAPI(
            self.username, self.password
        ).getChargingSessionDataAPI(
            stationID=stationID,
            sessionID=sessionID,
            userID=userID,
            stationName=stationName,
            Address=Address,
            City=City,
            State=State,
            Country=Country,
            postalCode=postalCode,
            Proximity=Proximity,
            proximityUnit=proximityUnit,
            fromTimeStamp=fromTimeStamp,
            toTimeStamp=toTimeStamp,
            startRecord=startRecord,
            Geo=Geo,
            stationIDs=stationIDs,
            activeSessionsOnly=activeSessionsOnly,
        )
        df_session_data = pd.DataFrame(session_data_res)
        if portNumber is not None:
            df_session_data = df_session_data[
                df_session_data["portNumber"] == portNumber
            ]
        session_ids = df_session_data["sessionID"].to_list()
        print(f"{session_ids = }")
        return self.get15minCharginSessionDataCollection(session_ids)


class GetChargingSessionDataAPI(ChargePointApi):
    def __init__(self, username, password):
        super().__init__(username, password)

    # Wrap the actual data-fetching function
    @paginated_api_call(
        api_entry_name="_getChargingSessionData",
        data_section_name="ChargingSessionData",
    )
    def _getChargingSessionDataAll(self, **kwargs):
        # Pass the client and parameters to the `_getChargingSessionData`
        return self.client.service.getChargingSessionData(kwargs)

    def getChargingSessionDataAPI(
        self,
        stationID: str = None,
        sessionID: int = None,
        userID=None,
        stationName: str = None,
        Address: str = None,
        City: str = None,
        State: str = None,
        Country=None,
        postalCode=None,
        Proximity=None,
        proximityUnit=None,
        fromTimeStamp: str = None,
        toTimeStamp: str = None,
        startRecord: int = None,
        Geo=None,
        stationIDs: list[str] = None,
        activeSessionsOnly=None,
    ):
        """
        Example fromTimeStamp: 2024-12-01T00:00:00, 2024-12-01, "2024/12/01"
        """
        if fromTimeStamp is not None:
            fromTimeStamp = pd.to_datetime(fromTimeStamp).strftime("%Y-%m-%dT%H:%M:%S")
        if toTimeStamp is not None:
            toTimeStamp = pd.to_datetime(toTimeStamp).strftime("%Y-%m-%dT%H:%M:%S")
        # searchQuery = client.get_type("ns0:sessionSearchdata")()
        searchQuery = {
            "stationID": stationID,
            "sessionID": sessionID,
            "userID": userID,
            "stationName": stationName,
            "Address": Address,
            "City": City,
            "State": State,
            "Country": Country,
            "postalCode": postalCode,
            "Proximity": Proximity,
            "proximityUnit": proximityUnit,
            "fromTimeStamp": fromTimeStamp,
            "toTimeStamp": toTimeStamp,
            "startRecord": startRecord,
            "Geo": Geo,
            "stationIDs": stationIDs,
            "activeSessionsOnly": activeSessionsOnly,
        }
        print(f"{searchQuery = }")
        return self._getChargingSessionDataAll(**searchQuery)


def main():
    username = "9c2fc57f048fd5c2f740dcf8e0a6f69c677c424289bda1736196674"
    password = "d67f1b3e02ff57fb6d90fc8a770db00b"
    charge_point = Get15minChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    resonse = charge_point.get15minCharginSessionDataCollection(
        session_ids=[101542479, 101268659, 100412719]
    )  # 101268659
    # print(resonse)
    df = pd.DataFrame(resonse)
    # print(df)

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "get15minCharginSessionData"
    table_schema = [
        ("stationTime", "TEXT"),
        ("energyConsumed", "REAL"),
        ("peakPower", "REAL"),
        ("rollingPowerAvg", "REAL"),
        ("sessionID", "INTEGER"),
    ]
    pks = ["stationTime", "sessionID"]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, pks)
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        df,
    )

    # # Query and print the data
    # results = db_handler.query_data_from_table(table_name)
    print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main2():
    username = "9c2fc57f048fd5c2f740dcf8e0a6f69c677c424289bda1736196674"
    password = "d67f1b3e02ff57fb6d90fc8a770db00b"
    charge_point = GetChargingSessionDataAPI(username, password)
    res = charge_point.getChargingSessionDataAPI(
        stationID="5:15504761",
        fromTimeStamp="2024-12-01",
        # toTimeStamp="2024-12-15"
    )
    print(pd.DataFrame(res).info())
    # print(pd.DataFrame(res))

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "getChargingSessionData"
    table_schema = [
        ("stationID", "TEXT"),
        ("stationName", "TEXT"),
        ("portNumber", "TEXT"),
        ("Address", "TEXT"),
        ("City", "TEXT"),
        ("State", "TEXT"),
        ("Country", "TEXT"),
        ("postalCode", "TEXT"),
        (
            "sessionID",
            "INTEGER",
        ),  # ("sessionID", "INTEGER PRIMARY KEY"),  # Assuming sessionID is unique
        ("Energy", "REAL"),
        ("startTime", "TEXT"),  # Storing as ISO8601 string
        ("endTime", "TEXT"),  # Storing as ISO8601 string
        ("totalChargingDuration", "TEXT"),  # Could be INTEGER if stored as seconds
        ("totalSessionDuration", "TEXT"),  # Could be INTEGER if stored as seconds
        ("userID", "TEXT"),
        ("startBatteryPercentage", "REAL"),
        ("stopBatteryPercentage", "REAL"),
        ("recordNumber", "INTEGER"),
        ("credentialID", "TEXT"),
        ("endedBy", "TEXT"),
        ("vehicleMake", "TEXT"),
        ("vehicleModel", "TEXT"),
        ("vehicleModelYear", "INTEGER"),
        ("vehicleType", "TEXT"),
        ("vehiclePortMAC", "TEXT"),
        ("driverOptedOut", "INTEGER"),  # Assuming this is a boolean flag (0 or 1)
        ("driverOptOutTimestamp", "TEXT"),  # Storing as ISO8601 string
        ("paymentTerminalInfo", "TEXT"),
    ]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, ["sessionID"])
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        pd.DataFrame(res),
    )

    # # # Query and print the data
    # # results = db_handler.query_data_from_table(table_name)
    # print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main3():
    username = "9c2fc57f048fd5c2f740dcf8e0a6f69c677c424289bda1736196674"
    password = "d67f1b3e02ff57fb6d90fc8a770db00b"
    charge_point = Get15minChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    resonse = charge_point.get15minCharginSessionDataAPI(
        stationID="5:15504761", portNumber="2"
    )  # 101268659
    # print(resonse)
    df = pd.DataFrame(resonse)
    # print(df)

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "get15minCharginSessionData"
    table_schema = [
        ("stationTime", "TEXT"),
        ("energyConsumed", "REAL"),
        ("peakPower", "REAL"),
        ("rollingPowerAvg", "REAL"),
        ("sessionID", "INTEGER"),
    ]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, ["stationTime", "sessionID"])
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        df,
    )

    # # Query and print the data
    # results = db_handler.query_data_from_table(table_name)
    print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


if __name__ == "__main__":
    # Entry point for script
    try:
        sys.exit(main2())
    except KeyboardInterrupt:
        pass
