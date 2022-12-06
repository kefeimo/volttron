"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

from dnp3_python.dnp3station.outstation_new import MyOutStationNew
from pydnp3 import opendnp3


_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.5"


def tester(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Tester
    :rtype: Tester
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    setting1 = int(config.get('setting1', 1))
    setting2 = config.get('setting2', "some/random/topic")

    return Tester(setting1, setting2, **kwargs)


class Tester(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, setting1=1, setting2="some/random/topic", **kwargs):
        super(Tester, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.setting1 = setting1
        self.setting2 = setting2

        self.default_config = {"setting1": setting1,
                               "setting2": setting2}

        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        self.vip.config.set_default("config", self.default_config)
        # Hook self.configure up to changes to the configuration file "config".
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

        # for dnp3 features
        self.outstation_application = MyOutStationNew()
        self.outstation_application.start()

    @RPC.export
    def demo_config_store(self):
        """
        Example return
        {'config_list': "['config', 'testagent.config']",
        'config': "{'setting1': 2, 'setting2': 'some/random/topic2'}",
        'testagent.config': "{'setting1': 2, 'setting2': 'some/random/topic2',
        'setting3': True, 'setting4': False, 'setting5': 5.1, 'setting6': [1, 2, 3, 4],
        'setting7': {'setting7a': 'a', 'setting7b': 'b'}}"}

        on command line
        vctl config store test-agent testagent.config /home/kefei/project-local/volttron/services/core/DNP3AgentNew/config
        vctl config get test-agent testagent.config
        """

        msg_dict = dict()
        # vip.config.set()
        # config_demo = {"set1": "setting1-xxxxxxxxx",
        #                   "set2": "setting2-xxxxxxxxx"}
        # # Set a default configuration to ensure that self.configure is called immediately to setup
        # # the agent.
        # # self.vip.config.set_default("config", default_config)  # set_default can only be used before onstart
        # self.vip.config.set(config_name="config_2", contents=config_demo,
        #                     trigger_callback=False, send_update=True)

        # vip.config.list()
        config_list = self.vip.config.list()
        msg_dict["config_list"] = str(config_list)

        # vip.config.get()
        if config_list:
            for config_name in config_list:
                config = self.vip.config.get(config_name)
                msg_dict[config_name] = str(config)

        return msg_dict

    @RPC.export
    def outstation_apply_update_analog(self, val):
        pass

        p_val = val
        self.outstation_application.apply_update(
            opendnp3.Analog(value=float(p_val),
                            flags=opendnp3.Flags(24),
                            time=opendnp3.DNPTime(3094)), 0)

        return "return something"

    @RPC.export
    def playground(self, val):
        pass

        p_val = val
        self.outstation_application.apply_update(
            opendnp3.Analog(value=float(p_val),
                            flags=opendnp3.Flags(24),
                            time=opendnp3.DNPTime(3094)), 0)

        return "return something"

    def configure(self, config_name, action, contents):
        """
        Called after the Agent has connected to the message bus. If a configuration exists at startup
        this will be called before onstart.

        Is called every time the configuration in the store changes.
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.debug("Configuring Agent")

        try:
            setting1 = int(config["setting1"])
            setting2 = str(config["setting2"])
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.setting1 = setting1
        self.setting2 = setting2

        self._create_subscriptions(self.setting2)

    def _create_subscriptions(self, topic):
        """
        Unsubscribe from all pub/sub topics and create a subscription to a topic in the configuration which triggers
        the _handle_publish callback
        """
        self.vip.pubsub.unsubscribe("pubsub", None, None)

        topic = "some/topic"
        self.vip.pubsub.subscribe(peer='pubsub',
                                  prefix=topic,
                                  callback=self._handle_publish)

    def _handle_publish(self, peer, sender, bus, topic, headers, message):
        """
        Callback triggered by the subscription setup using the topic from the agent's config file
        """
        _log.debug(f" ++++++handleer++++++++++++++++++++++++++"
                   f"peer {peer}, sender {sender}, bus {bus}, topic {topic}, "
                   f"headers {headers}, message {message}")

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        This is method is called once the Agent has successfully connected to the platform.
        This is a good place to setup subscriptions if they are not dynamic or
        do any other startup activities that require a connection to the message bus.
        Called after any configurations methods that are called at startup.

        Usually not needed if using the configuration store.
        """
        # Example publish to pubsub
        self.vip.pubsub.publish('pubsub', "some/random/topic", message="HI!")

        # Example RPC call
        # self.vip.rpc.call("some_agent", "some_method", arg1, arg2)
        pass
        self._create_subscriptions(self.setting2)

    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        This method is called when the Agent is about to shutdown, but before it disconnects from
        the message bus.
        """
        pass

    @RPC.export
    def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        return self.setting1 + arg1 - arg2

    @RPC.export
    def rpc_test(self, arg1="1111", arg2="22222", kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        # return self.setting1 + arg1 - arg2
        print("++++++++++++++++  look at me, I am important")
        return arg1 + arg2

    @RPC.export
    def rpc_demo_load_config(self):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        try:
            config = utils.load_config("/home/kefei/project-local/volttron/TestAgent/config")
        except Exception:
            config = {}
        return config

    @RPC.export
    def rpc_demo_config_list_set_get(self):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        default_config = {"setting1": "setting1-xxxxxxxxx",
                          "setting2": "setting2-xxxxxxxxx"}

        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        # self.vip.config.set_default("config", default_config)  # set_default can only be used before onstart
        self.vip.config.set(config_name="config_2", contents=default_config,
                            trigger_callback=False, send_update=True)
        get_result = [
            self.vip.config.get(config) for config in self.vip.config.list()
        ]
        return self.vip.config.list(), get_result

    @RPC.export
    def rpc_demo_config_set_default(self):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        default_config = {"setting1": "setting1-xxxxxxxxx",
                          "setting2": "setting2-xxxxxxxxx"}

        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        self.vip.config.set_default("config", default_config)
        return self.vip.config.list()
        # # Hook self.configure up to changes to the configuration file "config".
        # self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

    @RPC.export
    def rpc_demo_pubsub(self):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """

        # pubsub_list = self.vip.pubsub.list('pubsub', 'some/')
        # list(self, peer, prefix='', bus='', subscribed=True, reverse=False, all_platforms=False)
        # # return pubsub_list
        self.vip.pubsub.publish('pubsub', 'some/topic/', message="+++++++++++++++++++++++++ something something")
        # self.vip.pubsub.subscribe('pubsub', 'some/topic/', callable=self._handle_publish)
        # return pubsub_list
        # # Hook self.configure up to changes to the configuration file "config".
        # self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")


def main():
    """Main method called to start the agent."""
    utils.vip_main(tester,
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
