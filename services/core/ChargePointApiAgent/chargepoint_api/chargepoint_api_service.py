import functools
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import zeep
from zeep import Settings
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken

from .db_handler import (
    BaseDataHandler,
    EnergyDataHandlerPostGreSQL,
    EnergyDataHandlerSqlite,
)

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


# Function to set logging level for all zeep loggers (e.g. zeep.transports, zeep.xsd.schema, zeep.wsdl.wsdl)
def set_zeep_loggers_level(level):
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("zeep"):
            logging.getLogger(logger_name).setLevel(level)


# Set the logging level to INFO for all zeep loggers
set_zeep_loggers_level(logging.INFO)


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
                    f"Processing session {i + 1} out of {len(session_ids)}. Current {session_id = }"
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

    def getLoadAPI_v2(self, stationIDs: list[str]) -> list[dict]:
        """
        Retrieves load API data for multiple stations.

        Args:
            stationIDs (list[dict]): A list of dictionaries representing the station IDs.

        Returns:
            list[dict]: A list of dictionaries representing the load API data for the specified stations.
        """
        responses = []
        for station_id in stationIDs:
            response = self.getLoadAPI(stationID=station_id)
            if response is not None:
                responses += response
        return responses

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
        # utc_time_from_api = get_utc_time_from_api()
        # if utc_time_from_api:
        #     time_now_utc = utc_time_from_api
        # else:
        #     time_now_utc = datetime.now(
        #         timezone.utc
        #     )  # Note: local clock might be out of sync
        time_now_utc = datetime.now(
            timezone.utc
        )  # Note: local clock might be out of sync
        # _log.debug(
        #     f"{time_now_utc = }, {utc_time_from_api = }, {datetime.now(timezone.utc) = }"
        # )
        df["queryTimeUTC"] = pd.to_datetime(time_now_utc).strftime("%Y-%m-%dT%H:%M:%S")
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


def get_utc_time_from_api() -> str:
    """
    # Example usage
    current_utc_time = get_utc_time_from_api()
    print("Current UTC Time:", current_utc_time)
    """
    url = "http://worldtimeapi.org/api/timezone/Etc/UTC"
    try:
        response = requests.get(url)
        data = response.json()
        utc_time = data[
            "datetime"
        ]  # The datetime key contains the UTC time in ISO 8601 format.
        return utc_time
    except Exception as e:
        print("Failed to get time from API:", e)
        return None


class DbHandler:
    def __init__(self, db_type: str, db_init_args: dict) -> None:
        self.energy_data_handler: BaseDataHandler = None
        if db_type == "sqlite":
            self.energy_data_handler = EnergyDataHandlerSqlite(**db_init_args)
        elif db_type == "postgresql":
            self.energy_data_handler = EnergyDataHandlerPostGreSQL(**db_init_args)
        else:
            raise ValueError(f"Invalid db_type: {db_type}")

    def populate_to_db(
        self,
        subcommand: str,
        api_response: list[dict],
        logger=_log,
    ) -> pd.DataFrame:
        """helper funciton to poulate to db
        db_type in ["sqlite", "postgresql"],
        subcommand in ["get_load", "get_15min", "get_charging_session"]
        db_init_args
            sqlite: {"db_path": str}
            postgresql: {"db_name": str, "user": str, "password": str, "host": str}
        """

        if subcommand == "get_load":
            table_name = "getLoad"
            table_schema = [
                ("portNumber", "TEXT"),
                ("userID", "TEXT"),
                ("credentialID", "TEXT"),
                ("shedState", "INTEGER"),
                ("portLoad", "REAL"),
                ("allowedLoad", "REAL"),
                ("percentShed", "REAL"),
                ("sessionID", "INTEGER"),
                ("lastBatteryPercent", "REAL"),
                ("stationID", "TEXT"),
                ("stationName", "TEXT"),
                ("Address", "TEXT"),
                ("stationLoad", "REAL"),
                ("queryTimeUTC", "TEXT"),
            ]
            primary_keys = ["sessionID", "queryTimeUTC"]
        elif subcommand == "get_15min":
            table_name = "get15minCharginSessionData"
            table_schema = [
                ("stationTime", "TEXT"),
                ("energyConsumed", "REAL"),
                ("peakPower", "REAL"),
                ("rollingPowerAvg", "REAL"),
                ("sessionID", "INTEGER"),
            ]
            primary_keys = ["sessionID", "stationTime"]
        elif subcommand == "get_charging_session":
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
                ),  # PK
                ("Energy", "REAL"),
                ("startTime", "TEXT"),  # Storing as ISO8601 string
                ("endTime", "TEXT"),  # Storing as ISO8601 string
                (
                    "totalChargingDuration",
                    "TEXT",
                ),  # Could be INTEGER if stored as seconds
                (
                    "totalSessionDuration",
                    "TEXT",
                ),  # Could be INTEGER if stored as seconds
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
                (
                    "driverOptedOut",
                    "INTEGER",
                ),  # Assuming this is a boolean flag (0 or 1)
                ("driverOptOutTimestamp", "TEXT"),  # Storing as ISO8601 string
                ("paymentTerminalInfo", "TEXT"),
            ]
            primary_keys = ["sessionID"]
        else:
            raise ValueError(f"Invalid subcommand: {subcommand}")

        # # populate to db
        # # Get the directory of the current script
        # script_directory = os.path.dirname(os.path.abspath(__file__))
        # volttron_home_path = os.environ.get("VOLTTRON_HOME")
        # # print("Script is running in:", script_directory)
        # default_db_path = os.path.join(volttron_home_path, "chargePoint_testing.db")
        # db_path_from_config = self.config.get("db_path")
        # if db_path_from_config:
        #     db_path = db_path_from_config
        # else:
        #     db_path = default_db_path

        # _log.info(f"{db_path = }, {default_db_path = }")

        # Initialize the handler
        # db_handler = EnergyDataHandler(db_path)

        # db_handler.remove_table(table_name)
        self.energy_data_handler.create_table(table_name, table_schema, primary_keys)
        # Insert data
        inserted_data = self.energy_data_handler.insert_data_to_table(
            table_name,
            pd.DataFrame(api_response),
        )

        logger.info(f"Inserted data to {table_name = }, {inserted_data = }")
        return inserted_data
