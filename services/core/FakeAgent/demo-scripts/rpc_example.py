"""
A demo to test dnp3-driver get_point method using rpc call.
Pre-requisite:
- install platform-driver
- configure dnp3-driver
- a dnp3 outstation/server is up and running
- platform-driver is up and running
"""

import datetime
from time import sleep

from services.core.FakeAgent.fake_agent.agent import FakeAgent
from volttron.platform.vip.agent.utils import build_agent


def main():
    a = build_agent()

    # peer = "test-agent"
    # peer_method = "outstation_get_config"
    #
    # rs = a.vip.rpc.call(peer, peer_method, ).get(timeout=10)
    # print(datetime.datetime.now(), "rs: ", rs)

    peer = "agent-a"

    rs = a.vip.peerlist.list().get(5)
    if peer not in rs:
        raise ValueError(
            f"There is no agent named `{peer}` available on the message bus."
            f"Available peers are {rs}"
        )

    peer_method = "rpc_dummy"
    # method = FakeAgent.bar
    # peer_method = method.__name__
    rs = a.vip.rpc.call(peer, peer_method).get(timeout=10)
    print(datetime.datetime.now(), "rs: ", rs)


if __name__ == "__main__":
    main()
