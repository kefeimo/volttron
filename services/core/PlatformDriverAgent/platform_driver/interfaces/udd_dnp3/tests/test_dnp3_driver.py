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
from platform_driver.interfaces. \
    udd_dnp3 import UserDevelopRegisterDnp3
from platform_driver.interfaces.\
    udd_dnp3 import Interface as DNP3Interface

# from services.core.PlatformDriverAgent.platform_driver.interfaces import udd_dnp3
from dnp3_python.dnp3station.outstation_new import MyOutStationNew
from dnp3_python.dnp3station.master_new import MyMasterNew


from pydnp3 import opendnp3

class TestDummy:
    """
    Dummy test to check pytest setup
    """

    def test_dummy(self):
        print("I am a silly dummy test.")


# DNP3_DRIVER_CONFIG = {
#     "driver_config": {"master_ip": "0.0.0.0", "outstation_ip": "127.0.0.1",
#                       "master_id": 2, "outstation_id": 1,
#                       "port": 20000},
#     "registry_config": "config://udd-Dnp3-testing.csv",
#     "driver_type": "udd_dnp3",
#     "interval": 5,
#     "timezone": "UTC",
#     # "campus": "campus-testing",
#     # "building": "building-testing",
#     # "unit": "Dnp3-testing",
#     "heart_beat_point": "random_bool"
# }

json_path = "/home/kefei/project/volttron/services/core/PlatformDriverAgent/platform_driver/interfaces/udd_dnp3/tests/testing_data/udd-Dnp3-testing.config"

with open(json_path, "r") as f:
    json_config_str = f.read()
DNP3_DRIVER_CONFIG = json_config_str

csv_path = "/home/kefei/project/volttron/services/core/PlatformDriverAgent/platform_driver/interfaces/udd_dnp3/tests/testing_data/udd-Dnp3-testing.csv"

with open(csv_path, "r") as f:
    csv_config_str = f.read()

DNP3_REGISTER_MAP = csv_config_str


# DNP3_REGISTER_MAP = """Point Name,Volttron Point Name,Group,Variation,Index,Scaling,Units,Writable,Notes
# AnalogInput_index0,AnalogInput_index0,30,6,0,1,NA,FALSE,Double Analogue input without status
# AnalogInput_index1,AnalogInput_index1,30,6,1,1,NA,FALSE,Double Analogue input without status
# AnalogInput_index2,AnalogInput_index2,30,6,2,1,NA,FALSE,Double Analogue input without status
# AnalogInput_index3,AnalogInput_index3,30,6,3,1,NA,FALSE,Double Analogue input without status
# BinaryInput_index0,BinaryInput_index0,1,2,0,1,NA,FALSE,Single bit binary input with status
# BinaryInput_index1,BinaryInput_index1,1,2,1,1,NA,FALSE,Single bit binary input with status
# BinaryInput_index2,BinaryInput_index2,1,2,2,1,NA,FALSE,Single bit binary input with status
# BinaryInput_index3,BinaryInput_index3,1,2,3,1,NA,FALSE,Single bit binary input with status
# AnalogOutput_index0,AnalogOutput_index0,40,4,0,1,NA,TRUE,Double-precision floating point with flags
# AnalogOutput_index1,AnalogOutput_index1,40,4,1,1,NA,TRUE,Double-precision floating point with flags
# AnalogOutput_index2,AnalogOutput_index2,40,4,2,1,NA,TRUE,Double-precision floating point with flags
# AnalogOutput_index3,AnalogOutput_index3,40,4,3,1,NA,TRUE,Double-precision floating point with flags
# BinaryOutput_index0,BinaryOutput_index0,10,2,0,1,NA,TRUE,Binary Output with flags
# BinaryOutput_index1,BinaryOutput_index1,10,2,1,1,NA,TRUE,Binary Output with flags
# BinaryOutput_index2,BinaryOutput_index2,10,2,2,1,NA,TRUE,Binary Output with flags
# BinaryOutput_index3,BinaryOutput_index3,10,2,3,1,NA,TRUE,Binary Output with flags"""




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


class TestAgentFixture:
    """
    Dummy test to check agent fixture setup
    """
    pass


@pytest.fixture
def dnp3_driver_config_str():
    """
    DRIVER_CONFIG
    associated with `driver_config` in driver-config.config (json-like file)
                    user inputs are put here, e.g., IP address, url, etc.
    """
    json_path = Path("./testing_data/udd-Dnp3-testing.config")
    with open(json_path, 'r', encoding='utf-8') as f:
        driver_config = f.read()
    return driver_config


@pytest.fixture
def dnp3_csv_config_str():
    """
    REGISTER_MAP
    associated with the whole driver-config.csv file
    """
    csv_path = Path("./testing_data/udd-Dnp3-testing.csv")
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_config = f.read()
    return csv_config


def test_dnp3_csv_config_str(dnp3_csv_config_str, dnp3_driver_config_str):
    print("I am a agent dummy test.")
    print(f"======dnp3_csv_config_str {dnp3_csv_config_str}")
    print(f"======dnp3_driver_config_str {dnp3_driver_config_str}")


def test_agent(agent):
    print("I am a agent dummy test.")
    # print(f"======agent {agent}")



@pytest.fixture(scope="module")
def agent(request, volttron_instance,
          ):
    """
    Build PlatformDriverAgent, add dnp3 driver & csv configurations
    """

    # Build platform driver agent
    tester_agent = volttron_instance.build_agent(identity="test_dnp3_agent")

    # Note: add_capabilities may cause test fail for agent fixture
    # (i.e., (messagebus='rmq', ssl_auth=True), (messagebus='zmq', auth_enabled=False))
    capabilities = {'edit_config_store': {'identity': PLATFORM_DRIVER}}
    volttron_instance.add_capabilities(tester_agent.core.publickey, capabilities)

    # Clean out platform driver configurations
    # wait for it to return before adding new config
    # .call('config.store',
    #                       'manage_delete_store',
    #                       PLATFORM_DRIVER).get()


    # List platformdriver configurations
    config_lists_pre = tester_agent.vip.rpc.call('config.store',
                                             method='manage_list_configs',
                                             identity=PLATFORM_DRIVER,).get()
    print(f"==========config_lists{config_lists_pre}")

    # Add driver configurations
    tester_agent.vip.rpc.call('config.store',
                              'manage_store',
                              PLATFORM_DRIVER,
                              'devices/campus-vm/building-vm/Dnp3',
                              DNP3_DRIVER_CONFIG,
                              config_type='json')

    # md_agent.vip.rpc.call('config.store',
    #                       'manage_store',
    #                       PLATFORM_DRIVER,
    #                       'devices/modbus',
    #                       jsonapi.dumps(OLD_VOLTTRON_DRIVER_CONFIG),
    #                       config_type='json')

    # Add csv configurations
    tester_agent.vip.rpc.call('config.store',
                              'manage_store',
                              PLATFORM_DRIVER,
                              'udd-Dnp3.csv',
                              DNP3_REGISTER_MAP,
                              config_type='csv')



    config_lists_post = tester_agent.vip.rpc.call('config.store',
                                                 method='manage_list_configs',
                                                 identity=PLATFORM_DRIVER, ).get()
    print(f"==========config_lists{config_lists_post}")

    # config_csv = tester_agent.vip.rpc.call('config.store',
    #                                               method='manage_get',
    #                                               identity=PLATFORM_DRIVER,
    #                                               config_name="udd-Dnp3-testing.csv").get()
    # print(f"==========config_csv{config_csv}")
    #
    # config_json = tester_agent.vip.rpc.call('config.store',
    #                                        method='manage_get',
    #                                        identity=PLATFORM_DRIVER,
    #                                        config_name="devices/udd_dnp3",
    #                                         # config_name="devices/campus-testing/building-testing/Dnp3-testing"
    #                                         ).get()
    # print(f"==========config_json{config_json}")


    # md_agent.vip.rpc.call('config.store',
    #                       'manage_store',
    #                       PLATFORM_DRIVER,
    #                       'modbus.csv',
    #                       OLD_VOLTTRON_REGISTRY_CONFIG,
    #                       config_type='csv')

    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={},
        start=True)

    gevent.sleep(10)  # wait for the agent to start and start the devices

    def stop():
        """
        Stop platform driver agent
        """
        volttron_instance.stop_agent(platform_uuid)
        tester_agent.core.stop()

    request.addfinalizer(stop)
    return tester_agent


def test_agent_get(agent, outstation_app):
    print("I am a agent dummy test.")

    analog_input_val = 445.33
    outstation_app.apply_update(opendnp3.Analog(value=analog_input_val), index=0)

    config_lists_post = agent.vip.rpc.call('config.store',
                                                  method='manage_list_configs',
                                                  identity=PLATFORM_DRIVER, ).get()
    print(f"=+++++++++config_lists{config_lists_post}")

    # Note: need to explicitly create master station by calling configuration
    # TODO: create master should be in init. (refactor this.)


    try:
        res_get = agent.vip.rpc.call("platform.driver", "get_point",
                       "campus-vm/building-vm/Dnp3",
                       "AnalogInput_index0").get(timeout=60)

        print(f"+++++++++++++res_get{res_get}")
    except Exception as e:
        print(f"+++++++++++++e{e}")


class TestStation:
    """
    Testing the underlying pydnp3 package station-related functions.
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
    json_path = Path("./testing_data/udd-Dnp3-testing.config")
    with open(json_path) as json_f:
        driver_config = json.load(json_f)
    k = "driver_config"
    return {k: driver_config.get(k)}


@pytest.fixture
def csv_config():
    """
    associated with the whole driver-config.csv file
    """
    csv_path = Path("./testing_data/udd-Dnp3-testing.csv")
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
