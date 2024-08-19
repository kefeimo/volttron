import logging
import sys
import argparse

# from pydnp3 import opendnp3
# from dnp3_python.dnp3station.outstation import MyOutStation

from time import sleep
from volttron.platform.vip.agent.utils import build_agent
# from services.core.DNP3OutstationAgent.dnp3_outstation_agent.agent import Dnp3Agent as Dnp3OutstationAgent  # agent
from services.core.FakeAgent.fake_agent.agent import FakeAgent 
from volttron.platform.vip.agent import Agent, Core, RPC

import logging
import sys
import argparse

# from pydnp3 import opendnp3
# from dnp3_python.dnp3station.outstation_new import MyOutStationNew

from time import sleep

# from volttron.client.vip.agent import build_agent
# from dnp3_outstation.agent import Dnp3OutstationAgent
# from volttron.client.vip.agent import Agent

FAKE_AGENT_ID = "fake-agent"

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
# _log = logging.getLogger("control_workflow_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.INFO)


def input_prompt(display_str=None) -> str:
    if display_str is None:
        display_str = f"""
======== Your Input Here: ==(DNP3 OutStation Agent)======
"""
    return input(display_str)


def setup_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("-aid", "--agent-identity", action="store", default=FAKE_AGENT_ID, type=str,
                        metavar="<peer-name>",
                        help=f"specify agent identity (parsed as peer-name for rpc call), default '{FAKE_AGENT_ID}'.")

    return parser


def print_menu():
    welcome_str = rf"""
========================= MENU ==================================
<rd> - rpc_dummy
<rdp> - rpc_dummy_proxy
<rdwa> - rpc_dummy_wo_auth
=================================================================
"""
    print(welcome_str)


def check_agent_id_existence(agent_id: str, vip_agent: Agent):
    rs = vip_agent.vip.peerlist.list().get(5)
    if agent_id not in rs:
        raise ValueError(f"There is no agent named `{agent_id}` available on the message bus."
                         f"Available peers are {rs}")
        # _log.warning(f"There is no agent named `{agent_id}` available on the message bus."
        #                  f"Available peers are {rs}")


def main(parser=None, *args, **kwargs):
    if parser is None:
        # Initialize parser
        parser = argparse.ArgumentParser(
            prog="fake driver",
            description=f"Run a dnp3 outstation agent. Specify agent identity, by default `{FAKE_AGENT_ID}`",
            # epilog="Thanks for using %(prog)s! :)",
        )
        parser = setup_args(parser)

    # Read arguments from command line
    args = parser.parse_args()
    # create volttron vip agent to evoke dnp3-agent rpc calls
    a = build_agent()
    peer = args.agent_identity  # note: default {DNP3_AGENT_ID} or "test-agent"
    # print(f"========= peer {peer}")
    check_agent_id_existence(peer, a)

    def get_db_helper():
        _peer_method = Dnp3OutstationAgent.display_outstation_db.__name__
        _db_print = a.vip.rpc.call(peer, _peer_method).get(timeout=10)
        return _db_print

    def get_config_helper():
        _peer_method = Dnp3OutstationAgent.get_outstation_config.__name__
        _config_print = a.vip.rpc.call(peer, _peer_method).get(timeout=10)
        _config_print.update({"peer": peer})
        return _config_print

    sleep(2)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    count = 0
    while count < 1000:
        # sleep(1)  # Note: hard-coded, master station query every 1 sec.
        count += 1
        # print(f"=========== Count {count}")
        if True:
            # print("Communication Config", master_application.get_config())
            print_menu()
        else:
            print_menu()
            print("!!!!!!!!! WARNING: The outstation is NOT connected !!!!!!!!!")
            print(get_config_helper())
        # else:
        #     print("Communication error.")
        #     # print("Communication Config", outstation_application.get_config())
        #     print(get_config_helper())
        #     print("Start retry...")
        #     sleep(2)
        #     continue

        # print_menu()
        option = input_prompt()  # Note: one of ["ai", "ao", "bi", "bo",  "dd", "dc"]
        while True:
            if option == "rd":
                try:
                    method = FakeAgent.rpc_dummy
                    peer_method = method.__name__  # i.e., "apply_update_analog_input"
                    response = a.vip.rpc.call(peer, peer_method).get(timeout=10)
                    print(f"{response=}")
                    sleep(2)
                except Exception as e:
                    print(e)
                break
            elif option == "rdp":
                try:
                    method = FakeAgent.rpc_dummy_proxy
                    peer_method = method.__name__  # i.e., "apply_update_analog_input"
                    response = a.vip.rpc.call(peer, peer_method).get(timeout=10)
                    print(f"{response=}")
                    sleep(2)
                except Exception as e:
                    print(e)
                break
            elif option == "rdwa":
                try:
                    method = FakeAgent.rpc_dummy_wo_auth
                    peer_method = method.__name__  # i.e., "apply_update_analog_input"
                    response = a.vip.rpc.call(peer, peer_method).get(timeout=10)
                    print(f"{response=}")
                    sleep(2)
                except Exception as e:
                    print(e)
                break
            else:
                print(f"ERROR- your input `{option}` is not one of the following.")
                sleep(1)
                break

    _log.debug('Exiting.')
    # outstation_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
