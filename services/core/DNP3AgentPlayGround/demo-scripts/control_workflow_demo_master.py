import logging
import random
import sys

from pydnp3 import opendnp3

from dnp3_python.dnp3station.master_new import MyMasterNew

import datetime
from time import sleep
import time


stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("data_retrieval_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)

# logging.basicConfig(filename='demo.log', level=logging.DEBUG)


def main(duration=300):
    master_application = MyMasterNew()
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')
    # outstation_application = MyOutStationNew()
    # _log.debug('Initialization complete. OutStation in command loop.')

    start = time.time()
    end = time.time()

    count = 0
    while count < 1000 and (end - start) < duration:
        end = time.time()
        # sleep(10)  # Note: hard-coded, master station query every 1 sec.

        count += 1

        print(f"====== input <set_point_value> and <point_index>.e.g., 3.14332 4")
        print(int(end - start) % 10 == 0)

        input_str = input()

        if input_str is None and int(end - start) % 10 == 0:
            print(datetime.datetime.now(), "============count ", count, )
            # print(f"====== master database: {master_application.soe_handler.gv_ts_ind_val_dict}")
            print(f"====== master database: {master_application.soe_handler.gv_index_value_nested_dict}")
            continue
        else:
            val_str = input_str.split(" ")[0]
            index_str = input_str.split(" ")[-1]
            try:
                val = float(val_str)
                index = int(index_str)
            except Exception as e:
                print(e)

    _log.debug('Exiting.')
    master_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
