"""
A demo to test dnp3-driver get_point method using rpc call.
Pre-requisite:
- install platform-driver
- configure dnp3-driver
- a dnp3 outstation/server is up and running
- platform-driver is up and running
"""

import random
from volttron.platform.vip.agent.utils import build_agent
from time import sleep
import datetime


def main():
    a = build_agent()

    peer = "test-agent"
    peer_method = "outstation_apply_update_analog_input"

    rs = a.vip.rpc.call(peer, peer_method, 0.4532, 0).get(timeout=10)
    print(datetime.datetime.now(), "rs: ", rs)
    rs = a.vip.rpc.call(peer, peer_method, 1.412, 1).get(timeout=10)
    print(datetime.datetime.now(), "rs: ", rs)

    peer = "test-agent"
    peer_method = "rpc_demo_config_list_set_get"
    rs = a.vip.rpc.call(peer, peer_method).get(timeout=10)
    print(datetime.datetime.now(), "rs: ", rs)



    # while True:
    #     sleep(5)
    #     print("============")
    #     try:
    #         peer = "test-agent"
    #         peer_method = "outstation_display_db"
    #
    #         rs = a.vip.rpc.call(peer, peer_method).get(timeout=10)
    #         print(datetime.datetime.now(), "rs: ", rs)
    #
    #         # rs = a.vip.rpc.call(peer, peer_method, arg1="173", arg2="arg2222",
    #         #                     something="something-else"
    #         #                     ).get(timeout=10)
    #
    #         # rs = a.vip.rpc.call(peer, peer_method, "173", "arg2222",
    #         #                     "something-else"
    #         #                     ).get(timeout=10)
    #         # print(datetime.datetime.now(), "rs: ", rs)
    #         # reg_pt_name = "AnalogInput_index1"
    #         # rs = a.vip.rpc.call("platform.driver", rpc_method,
    #         #                     device_name,
    #         #                     reg_pt_name).get(timeout=10)
    #         # print(datetime.datetime.now(), "point_name: ", reg_pt_name, "value: ", rs)
    #     except Exception as e:
    #         print(e)


if __name__ == "__main__":
    main()
