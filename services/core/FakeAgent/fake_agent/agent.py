"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

# # from dnp3_python.dnp3station.outstation import MyOutStation as MyOutStationNew
# from dnp3_python.dnp3station.outstation_new import MyOutStationNew
# from pydnp3 import opendnp3
# from typing import Dict



_log = logging.getLogger("Fake-agent")
utils.setup_logging()
__version__ = "0.2.0"

_log.level=logging.DEBUG
_log.addHandler(logging.StreamHandler(sys.stdout))  # Note: redirect stdout from dnp3 lib

class FakeAgent(Agent):
    """This is class is a subclass of the Volttron Agent;
            This agent is an implementation of a DNP3 outstation;
            The agent overrides @Core.receiver methods to modify agent life cycle behavior;
            The agent exposes @RPC.export as public interface utilizing RPC calls.
        """

    def __init__(self, config_path: str, **kwargs) -> None:
        super(FakeAgent, self).__init__(**kwargs)

        # default_config, mainly for developing and testing purposes.
        default_config: dict = {}
        # agent configuration using volttron config framework
        # self._dnp3_outstation_config = default_config
        config_from_path = self._parse_config(config_path)

        # TODO: improve this logic by refactoring out the MyOutstationNew init,
        #  and add config from "config store"
        try:
            _log.info("Using config_from_path {config_from_path}")

        except Exception as e:
            _log.error(e)
            _log.info(f"Failed to use config_from_path {config_from_path}"
                      f"Using default_config {default_config}")


        # SubSystem/ConfigStore
        self.vip.config.set_default("config", default_config)
        self.vip.config.subscribe(
            self._config_callback_dummy,  # TODO: cleanup: used to be _configure_ven_client
            actions=["NEW", "UPDATE"],
            pattern="config",
        )  # TODO: understand what vip.config.subscribe does


    def _config_callback_dummy(self, config_name: str, action: str,
                               contents: dict) -> None:
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
        pass

    # ***************** Helper methods ********************
    def _parse_config(self, config_path: str) -> dict:
        """Parses the agent's configuration file.

        :param config_path: The path to the configuration file
        :return: The configuration
        """
        # TODO: added capability to configuration based on tabular config file (e.g., csv)
        try:
            config = utils.load_config(config_path)
        except NameError as err:
            _log.exception(err)
            raise err
        except Exception as err:
            _log.error("Error loading configuration: {}".format(err))
            config = {}
        # print(f"============= def _parse_config config {config}")
        if not config:
            raise Exception("Configuration cannot be empty.")
        return config

    # @RPC.allow('CAP_RPC_DUMMY')
    @RPC.export
    def rpc_dummy(self) -> str:
        """
        For testing rpc call
        """
        return "This is from def rpc_dummy"
    
    @RPC.export
    def rpc_dummy_proxy(self) -> str:
        """
        a proxy funnction to call rpc_dummy
        """
        return self.rpc_dummy()
    
    @RPC.export
    def rpc_dummy_wo_auth(self) -> str:
        """
        a proxy funnction to call rpc_dummy
        """
        return "This is from def rpc_dummy_wo_auth"


def main():
    """Main method called to start the agent."""
    utils.vip_main(FakeAgent,
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
