"""
A demo to test dnp3-driver get_point method using rpc call.
Pre-requisite:
- install platform-driver
- configure dnp3-driver
- a dnp3 outstation/server is up and running
- platform-driver is up and running
"""

import argparse
import datetime
from time import sleep

from services.core.FakeAgent.fake_agent.agent import FakeAgent
from volttron.platform.vip.agent.utils import build_agent


def main():
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")

    parser.add_argument(
        "--point-name",
        "-p ",
        type=str,
        help="driver point name",
        required=True,
        default="Energy",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    point_name = args.point_name

    a = build_agent()

    # peer = "test-agent"
    # peer_method = "outstation_get_config"
    #
    # rs = a.vip.rpc.call(peer, peer_method, ).get(timeout=10)
    # print(datetime.datetime.now(), "rs: ", rs)

    peer = "agent-a"
    # peer = "platform.driver2"

    rs = a.vip.peerlist.list().get(5)
    if peer not in rs:
        raise ValueError(
            f"There is no agent named `{peer}` available on the message bus."
            f"Available peers are {rs}"
        )
    # print(datetime.datetime.now(), "rs: ", rs)

    # peer_method = "rpc_dummy_wo_auth"
    peer_method = "rpc_call_driver"
    # # method = FakeAgent.bar
    # # peer_method = method.__name__
    rs = a.vip.rpc.call(peer, peer_method, point_name).get(timeout=10)
    # # rs = a.vip.rpc.call(peer, "get_point", "chargepoint/MSL5/port2", "Energy").get(
    # #     timeout=10
    # # )
    print(datetime.datetime.now(), f"{point_name=}: ", rs)


if __name__ == "__main__":
    main()
