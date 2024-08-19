# vip_agent.py
from volttron.platform.vip.agent.utils import build_agent
# from volttrontesting.utils.platformwrapper.
# import build_agent
from volttron.platform import get_address
import gevent
from datetime import datetime
import socket
import threading


def main_publish():
    pass
    print("somehitng")
    # agent = build_agent(address="tcp://127.0.0.4:22916", identity="foo") # not work
    # agent = build_agent(address="tcp://127.0.0.4:22916") # not work
    # agent = build_agent(address="127.0.0.4:22916") # not work
    agent = build_agent(
        #address="tcp://127.0.0.4:22916",
                        address="tcp://127.0.0.1:20000",
                        publickey="zD3g13hXedDznJeCTt8rvtd_LRjEEaQeyk8HQW68Tzc", 
                        secretkey="aqaxgdZ-Noh8HuIQcg369kDb2adH92wnuY44n895wiY",
                        serverkey="vXN1ZieG3J-TkAIxWKtVXojFWgwwx45ObbWayf_z_mo") # this works
    # agent = build_agent(address="ipc://@/home/kefei/.volttron/run/vip.socket") # this works
    # agent = build_agent(identity="foo") # this works
    # agent = build_agent() # this works
    agent.vip.pubsub.publish(peer="pubsub", topic="devices/campus/building/something", headers=None,
                             message="+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n"
                                     "+++++++++++something very important+++++++++++++++++\n", bus='')
    # print(agent.vip.peerlist.list().get(5))
   

def handle_heartbeat(peer, sender, bus, topic: str, headers, message):
    print(f"==== evoke from handle_heartbeat====111111111 with {peer=}, {sender=}, {topic=}, {headers=}, {message=}")
    
def handle_heartbeat_2(peer, sender, bus, topic: str, headers, message):
    print(f"==== evoke from handle_heartbeat====222222222 with {peer=}, {sender=}, {topic=}, {headers=}, {message=}")
        
def send_message_with_identifier(address, identifier, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(address)
        full_message = f"{identifier}:{message}"
        sock.sendall(full_message.encode('utf-8'))
        response = sock.recv(1024)
        print("Received:", response.decode('utf-8'))

def main_subscribe():
    pass
    address = ("127.0.0.1", 20000)
    identifier = "foo"  # or "bar"
    message = "Some very important message"
    send_message_with_identifier(address, identifier, message)
    agent = build_agent(
        # address="tcp://127.0.0.4:22916",
        address="tcp://127.0.0.1:20000/foo",  # Change to /bar as needed
                        # address="tcp://WE44933:20000",
                        publickey="zD3g13hXedDznJeCTt8rvtd_LRjEEaQeyk8HQW68Tzc", 
                        secretkey="aqaxgdZ-Noh8HuIQcg369kDb2adH92wnuY44n895wiY",
                        serverkey="vXN1ZieG3J-TkAIxWKtVXojFWgwwx45ObbWayf_z_mo") # this works
    
    agent.vip.pubsub.subscribe(peer='pubsub',
                          prefix='heartbeat',
                          callback=handle_heartbeat)
    
    # agent_2 = build_agent(
    #     #address="tcp://127.0.0.4:22916",
    #                     address="tcp://WE44933:20000",
    #                     publickey="zD3g13hXedDznJeCTt8rvtd_LRjEEaQeyk8HQW68Tzc", 
    #                     secretkey="aqaxgdZ-Noh8HuIQcg369kDb2adH92wnuY44n895wiY",
    #                     serverkey="FQGRVhWVid057PZwLgIz8LTmo9pIm0iAuCbW4OnQJRo") # this works
    
    # agent_2.vip.pubsub.subscribe(peer='pubsub',
    #                       prefix='heartbeat',
    #                       callback=handle_heartbeat_2)
    
    count = 0
    while True:
        gevent.sleep(5)
        print(f"{count=}, {datetime.now()}")
        count += 1


if __name__ == "__main__":
    # main_publish()
    main_subscribe()
    