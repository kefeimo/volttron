"""
Agent documentation goes here.
"""

__docformat__ = "reStructuredText"

import logging
import os
import sys

import pandas as pd

from volttron.platform.agent import utils
from volttron.platform.vip.agent import RPC, Agent, Core

# # from dnp3_python.dnp3station.outstation import MyOutStation as MyOutStationNew
# from dnp3_python.dnp3station.outstation_new import MyOutStationNew
# from pydnp3 import opendnp3
# from typing import Dict
from .chargepoint_api_service import (
    EnergyDataHandler,
    Get15minChargingSessionDataAPI,
    GetChargingSessionDataAPI,
    GetLoadAPI,
)

_log = logging.getLogger("ChargePoint-agent")
utils.setup_logging()
__version__ = "0.0.1"

_log.level = logging.DEBUG
_log.addHandler(
    logging.StreamHandler(sys.stdout)
)  # Note: redirect stdout from dnp3 lib


class ChargePointAPIAgent(Agent):
    """This is class is a subclass of the Volttron Agent;
    This agent is an implementation of a DNP3 outstation;
    The agent overrides @Core.receiver methods to modify agent life cycle behavior;
    The agent exposes @RPC.export as public interface utilizing RPC calls.
    """

    def __init__(self, config_path: str, **kwargs) -> None:
        super().__init__(**kwargs)

        # default_config, mainly for developing and testing purposes.
        default_config: dict = {}
        # agent configuration using volttron config framework
        # self._dnp3_outstation_config = default_config
        self.config = utils.load_config(config_path)
        if not self.config:
            raise ValueError(f"No configuration found at {config_path = }")
        #  and add config from "config store"
        # self.vip.config.subscribe(
        #     self._config_callback_dummy,
        #     actions=["NEW", "UPDATE"],
        #     pattern="config",
        # )

        # init from config
        self.publish_interval = int(self.config.get("publish_interval", 10))

        # charge point api init
        username = self.config.get("username")
        password = self.config.get("password")
        self.get_load_api = GetLoadAPI(username, password)
        self.get_15min_api = Get15minChargingSessionDataAPI(username, password)
        self.get_charging_session_api = GetChargingSessionDataAPI(username, password)

        self.charge_point_entry_kwargs: dict = self.config.get(
            "charge_point_entry_kwargs"
        )

    def _config_callback_dummy(
        self, config_name: str, action: str, contents: dict
    ) -> None:
        pass

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        This is method is called once the Agent has successfully connected to the platform.
        This is a good place to setup subscriptions if they are not dynamic or
        do any other startup activities that require a connection to the message bus.
        Called after any configurations methods that are called at startup.
        Usually not needed if using the configuration store.
        """
        # Note: callback func evoked periodically
        self.core.periodic(self.publish_interval, self.periodic_recall)

    def periodic_recall(self):
        # Get subcommand from config and assign method
        subcommand = self.config.get("subcommand")
        if subcommand == "get_load":
            method = self.get_load_api.getLoadAPI
        elif subcommand == "get_load_v2":
            method = self.get_load_api.getLoadAPI_v2
        elif subcommand == "get_15min":
            method = self.get_15min_api.get15minCharginSessionDataAPI
        elif subcommand == "get_charging_session":
            method = self.get_charging_session_api.getChargingSessionDataAPI
        else:
            raise ValueError(f"Invalid subcommand: {self.config.get('subcommand')}")

        # Evoke API call based on subcommand
        kwargs = self.charge_point_entry_kwargs
        api_response: list[dict] = method(**kwargs)

        if not api_response:
            _log.warning(f"No data received for {subcommand = }")
            return
        else:
            _log.info(f"API for {subcommand = }, {api_response = }")

        # populate to db
        if subcommand == "get_load" or subcommand == "get_load_v2":
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
            method = self.get_15min_api.get15minCharginSessionDataAPI
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
            method = self.get_charging_session_api.getChargingSessionDataAPI
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
            raise ValueError(f"Invalid subcommand: {self.config.get('subcommand')}")

        # populate to db
        # Get the directory of the current script
        script_directory = os.path.dirname(os.path.abspath(__file__))
        volttron_home_path = os.environ.get("VOLTTRON_HOME")
        # print("Script is running in:", script_directory)
        default_db_path = os.path.join(volttron_home_path, "chargePoint_testing.db")
        db_path_from_config = self.config.get("db_path")
        if db_path_from_config:
            db_path = db_path_from_config
        else:
            db_path = default_db_path

        _log.info(f"{db_path = }, {default_db_path = }")

        # Initialize the handler
        db_handler = EnergyDataHandler(db_path)

        # db_handler.remove_table(table_name)
        db_handler.create_table(table_name, table_schema, primary_keys)
        # Insert data
        inserted_data = db_handler.insert_data_to_table(
            table_name,
            pd.DataFrame(api_response),
        )

        _log.info(f"Inserted data to {table_name = }, {inserted_data = }")


def main():
    """Main method called to start the agent."""
    utils.vip_main(ChargePointAPIAgent, version=__version__)


if __name__ == "__main__":
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
