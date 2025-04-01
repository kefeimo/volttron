"""
Agent documentation goes here.
"""

__docformat__ = "reStructuredText"

import logging
import os
import re
import sys
from datetime import datetime

import pandas as pd

from volttron.platform.agent import utils
from volttron.platform.vip.agent import RPC, Agent, Core

try:
    from volttron.client.messaging import headers as headers_mod
except ImportError:
    from volttron.platform.messaging import headers as headers_mod

# # from dnp3_python.dnp3station.outstation import MyOutStation as MyOutStationNew
# from dnp3_python.dnp3station.outstation_new import MyOutStationNew
# from pydnp3 import opendnp3
# from typing import Dict
from .chargepoint_api_service import (
    Get15minChargingSessionDataAPI,
    GetChargingSessionDataAPI,
    GetLoadAPI,
    populate_to_db,
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
        if self.config.get("db_type"):
            db_type: str = self.config.get("db_type")
            db_init_args: dict = self.config.get("db_init_args")
            subcommand_modi = "get_load" if subcommand == "get_load_v2" else subcommand
            populate_to_db(db_type, db_init_args, subcommand_modi, api_response)

        # publish control
        if subcommand == "get_load" or subcommand == "get_load_v2":
            api_name = "getLoad"
            primary_keys = ["sessionID", "queryTimeUTC"]
            publish_keys = (
                primary_keys + ["portLoad"]
            )  # ["sessionID", "queryTimeUTC", "portLoad"] #    "portNumber", "stationName"
            # topic_format like "devices/PNNL/chargepoint{getLoad}/{MSL5}/port{2}"
            for row in api_response:
                # row = iter_row[1].to_dict()
                topic = f"devices/PNNL/chargepoint_{api_name}/{_get_cleaned_station_name(row['stationName'])}/port{row['portNumber']}"
                message = {k: row[k] for k in publish_keys}
                self._publish_row(topic, message)

        elif subcommand == "get_15min":
            api_name = "get15min"
            primary_keys = ["sessionID"]
            publish_keys = primary_keys + [
                "stationTime",
                "energyConsumed",
                "peakPower",
                "rollingPowerAvg",
            ]  # plus   "portNumber", "stationName"
            # topic_format like "devices/PNNL/chargepoint_{get15min}/{MSL5}/port{2}"
            # TODO: need to join get_charging_session_result
            for row in api_response:
                # row = iter_row[1].to_dict()
                charging_session_info = (
                    self.get_charging_session_api.getChargingSessionDataAPI(
                        sessionID=row["sessionID"]
                    )
                )
                topic = f"devices/PNNL/chargepoint_{api_name}/{_get_cleaned_station_name(charging_session_info['stationName'])}/port{charging_session_info['portNumber']}"
                message = {k: row[k] for k in publish_keys}
                self._publish_row(topic, message)
        elif subcommand == "get_charging_session":
            ...
        else:
            raise ValueError(f"Invalid subcommand: {self.config.get('subcommand')}")

    def _publish_row(self, topic, message):
        headers = {headers_mod.TIMESTAMP: utils.format_timestamp(datetime.utcnow())}
        # Publish on the TNS namespace:
        _log.info("Publishing data to topic '%s': %s", topic, message)
        try:
            self.vip.pubsub.publish(
                peer="pubsub", topic=topic, headers=headers, message=message
            ).get(timeout=10)
        except Exception as e:
            _log.error("Error publishing data: %s", e)


def _get_cleaned_station_name(original_name: str):
    """EXAMPLE: "PNNL / MSL5" -> MSL5"""
    # Note: the naming convention of PNNL station is like "PNNL / XXXX"
    if "/" in original_name:
        return _strip_special_chars(original_name.split("/")[1])
    else:
        return _strip_special_chars(original_name)


def _strip_special_chars(input_string):
    """
    Removes all special characters from the input string, retaining only alphanumeric characters (letters and numbers).

    Args:
    input_string (str): The string from which to remove special characters.

    Returns:
    str: A new string containing only alphanumeric characters.


    # Example usage:
    test_string = "Hello, World! 123."
    cleaned_string = strip_special_chars(test_string)
    print(cleaned_string)  # Output: 'HelloWorld123'
    """
    # This regular expression replaces any characters that are NOT letters or numbers with an empty string
    cleaned_string = re.sub(r"[^a-zA-Z0-9]", "", input_string)
    return cleaned_string


def main():
    """Main method called to start the agent."""
    utils.vip_main(ChargePointAPIAgent, version=__version__)


if __name__ == "__main__":
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
