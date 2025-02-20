import functools
import logging
import os
import re
import sqlite3
import sys
from datetime import UTC, datetime, timedelta

import pandas as pd
import zeep
from zeep import Settings
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

# Create a file handler and set its level to DEBUG
file_handler = logging.FileHandler("chargepoint_api.log")
file_handler.setLevel(logging.DEBUG)

# Create a stream handler and set its level to INFO
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
_log.addHandler(file_handler)
_log.addHandler(stream_handler)


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
                    # raise Exception(f"API error with response: {response}")
                    _log.error(f"API error with response: {response}.")
                    return None

                response = serialize_object(response)
                # Process the response data
                data = response.get(data_section_name, [])
                responses.extend(data)

                # Check if more data is available
                more_flag = response.get(more_flag_key, "NotExist") == 1
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
        raise ValueError("Invalid input. Valid examples include '1h', '4.5h', '34d'.")


def get_past_timestamp(prior_to):
    """
    Get the timestamp that is a specified duration in the past from the current time.

    Args:
        prior_to (str): A string representing the duration in the past.
                        Examples: "2h" for 2 hours ago, "5d" for 5 days ago.

    Returns:
        datetime: The timestamp that is the specified duration in the past from the current time.

    Raises:
        ValueError: If an invalid unit is provided. Only 'h', 'd', 'w' are accepted.

    Example Usage:
        get_past_timestamp("2h")  # timestamp 2 hours ago
        get_past_timestamp("5d")  # timestamp 5 days ago
    """
    amount, unit = parse_time_duration(prior_to)

    now = datetime.now()
    if unit == "h":
        return now - timedelta(hours=amount)
    elif unit == "d":
        return now - timedelta(days=amount)
    elif unit == "w":
        return now - timedelta(weeks=amount)
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
            _log.info(f"SQLite Database connected successfully at {self.db_path}")
            return conn
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error connecting to database: {e}")

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
            self.conn.execute(query)
            self.conn.commit()
            _log.info("Table created or verified successfully")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error creating table: {e}")

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
        if not df_filtered.empty:
            df_filtered.to_sql(table_name, self.conn, if_exists="append", index=False)
            _log.info(f"Data inserted successfully: {len(df_filtered)} records added.")
        else:
            _log.warning("No new records to insert; all records are duplicates.")

            """Insert data from a pandas DataFrame."""
        return df_filtered

    def get_primary_key_columns(self, table_name):
        """Retrieve the list of primary key columns for a given table."""
        query = f"PRAGMA table_info({table_name})"
        self.cursor.execute(query)
        columns = []
        for row in self.cursor.fetchall():
            # Column info: (cid, name, type, notnull, dflt_value, pk)
            if row[5] > 0:  # pk value is > 0 if the column is part of the primary key
                columns.append(row[1])
        return columns

    def query_data_from_table(self, table_name) -> pd.DataFrame:
        """Query all data from the table (for verification)."""
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            _log.info("Database connection closed")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error closing the database connection: {e}")

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
            _log.info(f"Table {table_name} has been removed successfully.")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error removing table {table_name}: {e}")


class ChargePointApi:
    # Note: this is the template for batching API calls

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
        self._get_charging_session_data_api = GetChargingSessionDataAPI(
            self.username, self.password
        )

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
            if i % 10 == 0:
                _log.info(
                    f"Processing session {i + 1} out of {len(session_ids)}. Current {session_id =}"
                )
            single_session_15min_data: dict = self._get15minChargingSessionData(
                sessionID=session_id,
                energyConsumedInterval=isEnergyConsumedIntervalDelta,
            )
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
                        raise ValueError(f"{fifteen_data = } is not a regular data")
                    for d in fifteen_data:
                        d["sessionID"] = session_id
                    fifteen_min_data_collection += fifteen_data
                except ValueError as e:
                    _log.warning(
                        f"Warning: encoutered and skipped {e = }, {session_id = }"
                    )
        return fifteen_min_data_collection

    def get15minCharginSessionDataAPI(
        self,
        stationID: str = None,
        sessionID: int = None,
        userID=None,
        stationName: str = None,
        Address: str = None,
        City: str = None,
        # State: str = None,  # Note: disable State parameter since the API is not working.
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
        start_period_ago: str = None,
        is_period_auto_defined: bool = False,
    ) -> list[dict]:
        session_data_res = (
            self._get_charging_session_data_api.getChargingSessionDataAPI(
                stationID=stationID,
                sessionID=sessionID,
                userID=userID,
                stationName=stationName,
                Address=Address,
                City=City,
                # State=State,
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
                portNumber=portNumber,
                start_period_ago=start_period_ago,
                is_period_auto_defined=is_period_auto_defined,
            )
        )
        if session_data_res == []:
            return []
        df_session_data = pd.DataFrame(session_data_res)
        session_ids = df_session_data["sessionID"].to_list()
        return self.get15minCharginSessionDataCollection(session_ids)


class GetChargingSessionDataAPI(ChargePointApi):
    def __init__(self, username, password):
        super().__init__(username, password)
        # Note: mechanism to poll historical data: first time, get all data,
        # then get the later later data defined by start_period_ago.
        # flag to check if all historical data has been polled
        # three states: None, False, True
        self._has_tried_to_poll_all_history: None | bool = None

    # Wrap the actual data-fetching function
    @paginated_api_call(
        api_entry_name="_getChargingSessionData",
        data_section_name="ChargingSessionData",
    )
    def _getChargingSessionDataAll(self, **kwargs):
        # Pass the client and parameters to the `_getChargingSessionData`
        # Note: need to handle stationIDs specifically
        if kwargs["stationIDs"] is not None:
            station_id_list_type = self.client.get_type("ns0:stationIdListBound")
            # Create an instance of this type
            station_ids = station_id_list_type(stationID=kwargs["stationIDs"])
            kwargs["stationIDs"] = station_ids
        return self.client.service.getChargingSessionData(kwargs)

    def getChargingSessionDataAPI(
        self,
        stationID: str = None,
        sessionID: int = None,
        userID=None,
        stationName: str = None,
        Address: str = None,
        City: str = None,
        # State: str = None,  # Note: disable State parameter since the API is not working.
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
        start_period_ago: str = None,
        is_period_auto_defined: bool = False,
    ) -> list[dict]:
        """
        Example fromTimeStamp: 2024-12-01T00:00:00, 2024-12-01, "2024/12/01"
        """
        # Note: mechanism to poll historical data: first time, get all data,
        # then get the later later data defined by start_period_ago
        # Note: keep the code workflow as it is, for readability
        if is_period_auto_defined and self._has_tried_to_poll_all_history != True:
            start_period_ago = None
        # print(f"========{self._has_tried_to_poll_all_history}")
        if fromTimeStamp is not None:
            fromTimeStamp = pd.to_datetime(fromTimeStamp).strftime("%Y-%m-%dT%H:%M:%S")
        if toTimeStamp is not None:
            toTimeStamp = pd.to_datetime(toTimeStamp).strftime("%Y-%m-%dT%H:%M:%S")
        if (
            fromTimeStamp is not None or toTimeStamp is not None
        ) and start_period_ago is not None:
            _log.warning(
                f"Warning: Overwrite {fromTimeStamp = } with {start_period_ago = }"
            )
        if start_period_ago is not None:
            fromTimeStamp = get_past_timestamp(start_period_ago).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

        # Can have values: M (Miles), N (Nautical miles), K (Kilometer), F (Feet), I (Inches)
        if proximityUnit is not None and proximityUnit not in ["M", "N", "K", "F", "I"]:
            raise ValueError("Invalid proximity unit. Valid units are: M, N, K, F, I")

        # searchQuery = client.get_type("ns0:sessionSearchdata")()
        searchQuery = {
            "stationID": stationID,
            "sessionID": sessionID,
            "userID": userID,
            "stationName": stationName,
            "Address": Address,
            "City": City,
            # "State": State,  # Note: disable State parameter since the API is not working.
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
        # print(f"{searchQuery = }")
        session_data_res = self._getChargingSessionDataAll(**searchQuery)
        if portNumber is not None:
            session_data_res = [
                d for d in session_data_res if d["portNumber"] == portNumber
            ]
        if is_period_auto_defined:
            self._has_tried_to_poll_all_history = True  # set the flag
        return session_data_res


class GetLoadAPI(ChargePointApi):
    """
    Represents a class for interacting with the GetLoad API of the ChargePoint API service.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
    """

    def __init__(self, username, password):
        super().__init__(username, password)

    def getLoadAPI(self, stationID=None, sgID=None, sessionID=None):
        """
        Retrieves the load information from the ChargePoint API.

        Args:
            stationID (str, optional): The ID of the station. Defaults to None.
            sgID (str, optional): The ID of the station group. Defaults to None.
            sessionID (str, optional): The ID of the session. Defaults to None.

        Returns:
            dict: The response from the API containing the load information.
                  Returns None if there is an API error.
        """
        # Note: 'Search by either sgID, sessionID or stationID', one and only one of them should be provided.
        searchQuery = {}
        if sgID is not None:
            searchQuery.update({"sgID": sgID})
        if stationID is not None:
            searchQuery.update({"stationID": stationID})
        if sessionID is not None:
            searchQuery.update({"sessionID": sessionID})

        response = self.client.service.getLoad(searchQuery)

        if response["responseCode"] != "100":
            # raise Exception(f"API error with response: {response}")
            _log.warning(f"Warning: API error with response: {response}.")
            return None

        serialized_res = serialize_object(response)

        # flattern the nested json data
        df = pd.json_normalize(
            serialized_res["stationData"],
            record_path="Port",
            meta=["stationID", "stationName", "Address", "stationLoad"],
        )
        # filter out the sessionID = 0 (invalid sessionID)
        df = df[df["sessionID"] != 0]
        # add "queryTime" column
        df["queryTimeUTC"] = pd.to_datetime(datetime.now(UTC))
        # parse xml type to general python type (i.e., decimal.Decimal to float)
        for col in [
            "portLoad",
            "allowedLoad",
            "percentShed",
            "lastBatteryPercent",
            "stationLoad",
        ]:
            # df[col] = df[col].apply(lambda x: float(x) if x is not None else None)
            df[col] = df[col].astype(float)
        # convert the dataframe to a list of dictionaries
        return df.to_dict(orient="records")
