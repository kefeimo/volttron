# def tryyield():
#   # yield \
#   #   "Welcome to Guru99 Python Tutorials"
#   print("inside tryyield")
# from volttron.platform import jsonapi
import json
from volttron.platform.vip.agent.utils import build_agent


# def main():
#     keystore_file = "~/.volttron_debug/keystores/listener4/keystore.json"
#     with open(keystore_file, 'r') as fout:
#         output = fout.read()
#     json_obj = jsonapi.loads(output)
#     print(json_obj)

# def main2():
#     keystore_file = "home/kefei/.volttron_debug/keystores/listener5/keystore_write.json"
#     output = str({"public": "FvtL97M31lcKB2sEEB1vFnMOLQ-IPZ7NAIiO6Q1GVmA",
#               "secret": "UPZkHgTaeMaKPcL6keypYQOQY1CTYdVnIKDyzRkv768"})
#     with open(keystore_file, 'w') as fout:
#         fout.write(output)
#     # json_obj = json.loads(output)
#     print(output)

# def main3():
#     import os
#     agent_keystore_path = "~/.volttron_debug/keystores/listener5/keystore.json"
#     if os.path.exists(agent_keystore_path):  # keystore.json file exist only read
#         with open(agent_keystore_path, 'r') as fout:
#             output = fout.read()
#         print(output)

from volttron.platform.vip.agent.utils import build_agent


def main():
    agent = build_agent()
    agent.vip.pubsub.publish(peer="pubsub", topic="somedevices/campus/building/something", headers=None,
                             message="+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n", bus='')


if __name__ == "__main__":
    main()

