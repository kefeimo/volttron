import pytest
import gevent
import logging
import time
import csv
import json
from pathlib import Path
import random

# from volttrontesting.utils.utils import get_rand_ip_and_port
from volttron.platform import get_services_core, jsonapi
# from platform_driver.interfaces.modbus_tk.server import Server
# from platform_driver.interfaces.modbus_tk.maps import Map, Catalog
from volttron.platform.agent.known_identities import PLATFORM_DRIVER

# from services.core.PlatformDriverAgent.platform_driver.interfaces import udd_dnp3
# from services.core.PlatformDriverAgent.platform_driver.interfaces. \
#     udd_dnp3.pydnp3.src.dnp3_python.outstation_new import MyOutStationNew
# from services.core.PlatformDriverAgent.platform_driver.interfaces. \
#     udd_dnp3.pydnp3.src.dnp3_python.master_new import MyMasterNew
from services.core.PlatformDriverAgent.platform_driver.interfaces. \
    udd_dnp3 import UserDevelopRegisterDnp3
from pydnp3 import opendnp3
from services.core.PlatformDriverAgent.platform_driver.interfaces.\
    udd_dnp3.udd_dnp3 import Interface as DNP3Interface

from dnp3_python.dnp3station.master_new import MyMasterNew
from dnp3_python.dnp3station.outstation_new import MyOutStationNew

# TODO: add IP, port pool to avoid conflict


class TestDummy:
    """
    Dummy test to check pytest setup
    """

    def test_dummy(self):
        print("I am a silly dummy test.")




DRIVER_CONFIG = {
    "driver_config": {"master_ip": "0.0.0.0", "outstation_ip": "127.0.0.1",
                      "master_id": 2, "outstation_id": 1,
                      "port": 20000},
    "registry_config": "config://udd-Dnp3.csv",
    "driver_type": "udd_dnp3",
    "interval": 5,
    "timezone": "UTC",
    "campus": "campus-vm",
    "building": "building-vm",
    "unit": "Dnp3",
    "publish_depth_first_all": True,
    "heart_beat_point": "random_bool"
}

# New modbus_tk csv config
REGISTRY_CONFIG_STRING = """Volttron Point Name,Register Name
unsigned short,unsigned_short
unsigned int,unsigned_int
unsigned long,unsigned_long
sample short,sample_short
sample int,sample_int
sample float,sample_float
sample long,sample_long
sample bool,sample_bool
sample str,sample_str"""

REGISTER_MAP = """Register Name,Address,Type,Units,Writable,Default Value,Transform
unsigned_short,0,uint16,None,TRUE,0,scale(10)
unsigned_int,1,uint32,None,TRUE,0,scale(10)
unsigned_long,3,uint64,None,TRUE,0,scale(10)
sample_short,7,int16,None,TRUE,0,scale(10)
sample_int,8,int32,None,TRUE,0,scale(10)
sample_float,10,float,None,TRUE,0.0,scale(10)
sample_long,12,int64,None,TRUE,0,scale(10)
sample_bool,16,bool,None,TRUE,False,
sample_str,17,string[12],None,TRUE,hello world!,"""


# Register values dictionary for testing set_point and get_point
registers_dict = {"unsigned short": 65530,
                  "unsigned int": 4294967290,
                  "unsigned long": 184467440737090,
                  "sample short": -32760,
                  "sample int": -2147483640,
                  "sample float": -12340.0,
                  "sample long": -922337203685470,
                  "sample bool": True,
                  "sample str": "SampleString"}

@pytest.fixture(scope="module")
def outstation_app():
    """
    outstation using default configuration (including default database)
    Note: since outstation cannot shut down gracefully,
    outstation_app fixture need to in "module" scope to prevent interrupting pytest during outstation shut-down
    """

    outstation_appl = MyOutStationNew()
    outstation_appl.start()
    # time.sleep(3)
    yield outstation_appl
    # clean-up
    # note: will cause "Fatal Python error: Aborted" Cannot capture
    outstation_appl.shutdown()


@pytest.fixture
def master_app():
    """
    master station using default configuration
    Note: outstation needs to exist first to make connection.
    """

    master_appl = MyMasterNew(stale_if_longer_than=0.1)
    master_appl.start()
    # Note: add delay to prevent conflict
    # (there is a delay when master shutdown. And all master shares the same config)
    time.sleep(1)
    yield master_appl
    # clean-up
    master_appl.shutdown()
    time.sleep(1)


class TestDummyAgentFixture:
    """
    Dummy test to check pytest setup
    """
    pass

    def test_agent_dummy(self, dnp3_tester_agent):
        print("I am a agent dummy test.")
        # print(f"======agent {agent}")


def test_agent_get(
        dnp3_tester_agent,
        outstation_app,
        # master_app
        ):
    print("I am a agent dummy test.")
    # print(f"======agent {agent}")

    val_update = 4.3221
    outstation_app.apply_update(opendnp3.Analog(value=val_update,
                                                flags=opendnp3.Flags(24),
                                                time=opendnp3.DNPTime(3094)),
                                index=0)

    time.sleep(3)

    res_val = dnp3_tester_agent.vip.rpc.call("platform.driver", "get_point",
                                             "campus-vm/building-vm/Dnp3",
                                             "AnalogInput_index0").get(timeout=20)

    print(f"======res_val {res_val}")

# store
# json_str = '{\n    "driver_config": {"master_ip": "0.0.0.0", "outstation_ip": "127.0.0.1",\n        "master_id": 2, "outstation_id": 1,\n        "port":  20000},\n    "registry_config":"config://udd-Dnp3.csv",\n\t\t"driver_type": "udd_dnp3",\n    "interval": 5,\n    "timezone": "UTC",\n    "campus": "campus-vm",\n    "building": "building-vm",\n    "unit": "Dnp3",\n\t\t"publish_depth_first_all": true,\n    "heart_beat_point": "random_bool"\n}\n'
#
# csv_str = 'Point Name,Volttron Point Name,Group,Variation,Index,Scaling,Units,Writable,Notes\nAnalogInput_index0,AnalogInput_index0,30,6,0,1,NA,FALSE,Double Analogue input without status\nAnalogInput_index1,AnalogInput_index1,30,6,1,1,NA,FALSE,Double Analogue input without status\nAnalogInput_index2,AnalogInput_index2,30,6,2,1,NA,FALSE,Double Analogue input without status\nAnalogInput_index3,AnalogInput_index3,30,6,3,1,NA,FALSE,Double Analogue input without status\nBinaryInput_index0,BinaryInput_index0,1,2,0,1,NA,FALSE,Single bit binary input with status\nBinaryInput_index1,BinaryInput_index1,1,2,1,1,NA,FALSE,Single bit binary input with status\nBinaryInput_index2,BinaryInput_index2,1,2,2,1,NA,FALSE,Single bit binary input with status\nBinaryInput_index3,BinaryInput_index3,1,2,3,1,NA,FALSE,Single bit binary input with status\nAnalogOutput_index0,AnalogOutput_index0,40,4,0,1,NA,TRUE,Double-precision floating point with flags\nAnalogOutput_index1,AnalogOutput_index1,40,4,1,1,NA,TRUE,Double-precision floating point with flags\nAnalogOutput_index2,AnalogOutput_index2,40,4,2,1,NA,TRUE,Double-precision floating point with flags\nAnalogOutput_index3,AnalogOutput_index3,40,4,3,1,NA,TRUE,Double-precision floating point with flags\nBinaryOutput_index0,BinaryOutput_index0,10,2,0,1,NA,TRUE,Binary Output with flags\nBinaryOutput_index1,BinaryOutput_index1,10,2,1,1,NA,TRUE,Binary Output with flags\nBinaryOutput_index2,BinaryOutput_index2,10,2,2,1,NA,TRUE,Binary Output with flags\nBinaryOutput_index3,BinaryOutput_index3,10,2,3,1,NA,TRUE,Binary Output with flags\n'


json_config_path = "./testing_data/udd-Dnp3.config"
with open(json_config_path, "r") as f:
    json_str = f.read()

csv_config_path = "./testing_data/udd-Dnp3.csv"
with open(csv_config_path, "r") as f:
    csv_str = f.read()


# @pytest.fixture(scope="module")
@pytest.fixture
def dnp3_tester_agent(request, volttron_instance):
    """
    Build PlatformDriverAgent, add modbus driver & csv configurations
    """

    # Build platform driver agent
    tester_agent = volttron_instance.build_agent(identity="test_dnp3_agent")
    capabilities = {'edit_config_store': {'identity': PLATFORM_DRIVER}}
    volttron_instance.add_capabilities(tester_agent.core.publickey, capabilities)

    # Clean out platform driver configurations
    # wait for it to return before adding new config
    tester_agent.vip.rpc.call('config.store',
                          'manage_delete_store',
                          PLATFORM_DRIVER).get()

    tester_agent.vip.rpc.call('config.store',
                   method='manage_store',
                   identity=PLATFORM_DRIVER,
                   config_name="udd-Dnp3.csv",
                   raw_contents=csv_str,
                   config_type='csv'
                   ).get(timeout=5)

    tester_agent.vip.rpc.call('config.store',
                   method='manage_store',
                   identity=PLATFORM_DRIVER,
                   config_name="devices/campus-vm/building-vm/Dnp3",
                   raw_contents=json_str,
                   config_type='json'
                   ).get(timeout=5)


    # List platformdriver configurations
    config_lists_pre = tester_agent.vip.rpc.call('config.store',
                                             method='manage_list_configs',
                                             identity=PLATFORM_DRIVER,).get()
    print(f"==========config_lists{config_lists_pre}")

    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={},
        start=True)

    print(f"==========platform_uuid{platform_uuid}")

    # gevent.sleep(10)  # wait for the agent to start and start the devices
    time.sleep(10)  # wait for the agent to start and start the devices

    def stop():
        """
        Stop platform driver agent
        """
        volttron_instance.stop_agent(platform_uuid)
        tester_agent.core.stop()
    #
    # request.addfinalizer(stop)
    # return tester_agent
    yield tester_agent
    request.addfinalizer(stop)


class TestStation:
    """
    Testing the underlying pydnp3 package station-related fuctions.
    """

    def test_station_init(self, master_app, outstation_app):
        # master_app = MyMasterNew()
        # master_app.start()
        driver_wrapper_init_arg = {'driver_config': {}, 'point_name': "", 'data_type': "", 'units': "", 'read_only': ""}
        UserDevelopRegisterDnp3(master_application=master_app, reg_def={},
                                **driver_wrapper_init_arg)

    def test_station_get_val_analog_input_float(self, master_app, outstation_app):

        # outstation update with values
        analog_input_val = [1.2454, 33453.23, 45.21]
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update,
                                                        flags=opendnp3.Flags(24),
                                                        time=opendnp3.DNPTime(3094)),
                                        index=i)
        # Note: group=30, variation=6 is AnalogInputFloat
        for i, val_update in enumerate(analog_input_val):
            val_get = master_app.get_val_by_group_variation_index(group=30, variation=6, index=i)
            # print(f"===val_update {val_update}, val_get {val_get}")
            assert val_get == val_update

        time.sleep(1)  # add delay buffer to pass the "stale_if_longer_than" checking statge

        # outstation update with random values
        analog_input_val_random = [random.random() for i in range(3)]
        for i, val_update in enumerate(analog_input_val_random):
            outstation_app.apply_update(opendnp3.Analog(value=val_update),
                                        index=i)
        # Note: group=30, variation=6 is AnalogInputFloat
        for i, val_update in enumerate(analog_input_val_random):
            val_get = master_app.get_val_by_group_variation_index(group=30, variation=6, index=i)
            # print(f"===val_update {val_update}, val_get {val_get}")
            assert val_get == val_update

    def test_station_set_val_analog_input_float(self, master_app, outstation_app):

        # outstation update with values
        analog_output_val = [1.2454, 33453.23, 45.21]
        for i, val_to_set in enumerate(analog_output_val):
            master_app.send_direct_point_command(group=40, variation=4, index=i,
                                                 val_to_set=val_to_set)
        # Note: group=40, variation=4 is AnalogOutFloat
        for i, val_to_set in enumerate(analog_output_val):
            val_get = master_app.get_val_by_group_variation_index(group=40, variation=4, index=i)
            # print(f"===val_update {val_update}, val_get {val_get}")
            assert val_get == val_to_set

        time.sleep(1)  # add delay buffer to pass the "stale_if_longer_than" checking statge

        # outstation update with random values
        analog_output_val_random = [random.random() for i in range(3)]
        for i, val_to_set in enumerate(analog_output_val_random):
            master_app.send_direct_point_command(group=40, variation=4, index=i,
                                                 val_to_set=val_to_set)
        # Note: group=40, variation=4 is AnalogOutFloat
        for i, val_to_set in enumerate(analog_output_val_random):
            val_get = master_app.get_val_by_group_variation_index(group=40, variation=4, index=i)
            # print(f"===val_update {val_update}, val_get {val_get}")
            assert val_get == val_to_set


@pytest.fixture
def dnp3_inherit_init_args(csv_config, driver_config_in_json_config):
    """
    args required for parent class init (i.e., class WrapperRegister)
    """
    args = {'driver_config': driver_config_in_json_config,
            'point_name': "",
            'data_type': "",
            'units': "",
            'read_only': ""}
    return args


@pytest.fixture
def driver_config_in_json_config():
    """
    associated with `driver_config` in driver-config.config (json-like file)
                    user inputs are put here, e.g., IP address, url, etc.
    """
    json_path = Path("./testing_data/udd-Dnp3.config")
    with open(json_path) as json_f:
        driver_config = json.load(json_f)
    k = "driver_config"
    return {k: driver_config.get(k)}


@pytest.fixture
def csv_config():
    """
    associated with the whole driver-config.csv file
    """
    csv_path = Path("./testing_data/udd-Dnp3.csv")
    with open(csv_path) as f:
        reader = csv.DictReader(f, delimiter=',')
        csv_config = [row for row in reader]

    return csv_config


@pytest.fixture
def reg_def_dummy():
    """
    register definition, row of csv config file
    """
    # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
    #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
    #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}
    reg_def = {'Point Name': 'pn', 'Volttron Point Name': 'pn',
               'Group': 'int', 'Variation': 'int', 'Index': 'int', 'Scaling': '1', 'Units': 'NA',
               'Writable': 'NA', 'Notes': ''}
    return reg_def


class TestDNPRegister:
    """
    Tests for UserDevelopRegisterDnp3 class

    init

    get_register_value
        analog input float
        analog input int
        binary input
    """

    def test_init(self, master_app, csv_config, dnp3_inherit_init_args):
        for reg_def in csv_config:
            UserDevelopRegisterDnp3(master_application=master_app,
                                    reg_def=reg_def,
                                    **dnp3_inherit_init_args
                                    )

    def test_get_register_value_analog_float(self, outstation_app, master_app, csv_config,
                                             dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        analog_input_val = [445.33, 1123.56, 98.456] + [random.random() for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 30, variation = 6 is AnalogInputFloat
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(analog_input_val)):
            reg_def["Group"] = "30"
            reg_def["Variation"] = "6"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # outstation update values
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # verify: driver read value
        for i, (val_update, csv_row) in enumerate(zip(analog_input_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_analog_int(self, outstation_app, master_app, csv_config,
                                           dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        analog_input_val = [345, 1123, 98] + [random.randint(1, 100) for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 30, variation = 1 is AnalogInputInt32
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(analog_input_val)):
            reg_def["Group"] = "30"
            reg_def["Variation"] = "1"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # outstation update values
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # verify: driver read value
        for i, (val_update, csv_row) in enumerate(zip(analog_input_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_binary(self, outstation_app, master_app, csv_config,
                                       dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        binary_input_val = [True, False, True] + [random.choice([True, False]) for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 1, variation = 2 is BinaryInput
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(binary_input_val)):
            reg_def["Group"] = "1"
            reg_def["Variation"] = "2"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # outstation update values
        for i, val_update in enumerate(binary_input_val):
            outstation_app.apply_update(opendnp3.Binary(value=val_update), index=i)

        # verify: driver read value
        for i, (val_update, csv_row) in enumerate(zip(binary_input_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print(f"=========== i {i}, val_get {val_get}, val_update {val_update}")
            assert val_get == val_update


class TestDNP3RegisterControlWorkflow:

    def test_set_register_value_analog_float(self, outstation_app, master_app, csv_config,
                                             dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        # Note: group=40, variation=4 is AnalogOutputDoubleFloat
        output_val = [343.23, 23.1109, 58.2] + [random.random() for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 1, variation = 2 is BinaryInput
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(output_val)):
            reg_def["Group"] = "40"
            reg_def["Variation"] = "4"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # master set values
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            dnp3_register.set_register_value(value=val_set)

        # verify: driver read value
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_set

    def test_set_register_value_analog_int(self, outstation_app, master_app, csv_config,
                                           dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        # Note: group=40, variation=4 is AnalogOutputDoubleFloat
        output_val = [45343, 344, 221] + [random.randint(1, 1000) for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 1, variation = 2 is BinaryInput
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(output_val)):
            reg_def["Group"] = "40"
            reg_def["Variation"] = "1"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # master set values
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            dnp3_register.set_register_value(value=val_set)

        # verify: driver read value
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_set

    def test_set_register_value_binary(self, outstation_app, master_app, csv_config,
                                       dnp3_inherit_init_args, reg_def_dummy):

        # dummy test variable
        # Note: group=40, variation=4 is AnalogOutputDoubleFloat
        output_val = [True, False, True] + [random.choice([True, False]) for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 1, variation = 2 is BinaryInput
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(output_val)):
            reg_def["Group"] = "10"
            reg_def["Variation"] = "2"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # master set values
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            dnp3_register.set_register_value(value=val_set)

        # verify: driver read value
        for i, (val_set, csv_row) in enumerate(zip(output_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_set


class TestDNP3Interface:

    def test_init(self):
        pass
        dnp3_interface = DNP3Interface()

    def test_get_reg_point(self, outstation_app, master_app, csv_config,
                           dnp3_inherit_init_args, reg_def_dummy):
        # dummy test variable
        analog_input_val = [445.33, 1123.56, 98.456] + [random.random() for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 30, variation = 6 is AnalogInputFloat
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(analog_input_val)):
            reg_def["Group"] = "30"
            reg_def["Variation"] = "6"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        # outstation update values
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # verify: driver read value
        dnp3_interface = DNP3Interface()
        for i, (val_update, csv_row) in enumerate(zip(analog_input_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )

            val_get = dnp3_interface.get_reg_point(register=dnp3_register)
            # print("======== dnp3_register.value", dnp3_register.value)
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_set_reg_point(self, outstation_app, master_app, csv_config,
                           dnp3_inherit_init_args, reg_def_dummy):
        # dummy test variable
        analog_output_val = [445.33, 1123.56, 98.456] + [random.random() for i in range(3)]

        # dummy reg_def (csv config row)
        # Note: group = 30, variation = 6 is AnalogInputFloat
        reg_def = reg_def_dummy
        reg_defs = []
        for i in range(len(analog_output_val)):
            reg_def["Group"] = "40"
            reg_def["Variation"] = "4"
            reg_def["Index"] = str(i)
            reg_defs.append(reg_def.copy())  # Note: Python gotcha, mutable don't evaluate til the end of the loop.

        dnp3_interface = DNP3Interface()

        # dnp3_interface update values
        for i, (val_update, csv_row) in enumerate(zip(analog_output_val, reg_defs)):
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )
            dnp3_interface.set_reg_point(register=dnp3_register, value_to_set=val_update)

        # verify: driver read value

        for i, (val_update, csv_row) in enumerate(zip(analog_output_val, reg_defs)):
            # print(f"====== reg_defs {reg_defs}, analog_input_val {analog_input_val}")
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=csv_row,
                                                    **dnp3_inherit_init_args
                                                    )

            val_get = dnp3_interface.get_reg_point(register=dnp3_register)
            # print("======== dnp3_register.value", dnp3_register.value)
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update
