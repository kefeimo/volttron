import pytest
import gevent
import logging
import time
import csv
import json
from pathlib import Path
import random

from volttrontesting.utils.utils import get_rand_ip_and_port
from volttron.platform import get_services_core, jsonapi
from platform_driver.interfaces.modbus_tk.server import Server
from platform_driver.interfaces.modbus_tk.maps import Map, Catalog
from volttron.platform.agent.known_identities import PLATFORM_DRIVER

# from services.core.PlatformDriverAgent.platform_driver.interfaces import udd_dnp3
from services.core.PlatformDriverAgent.platform_driver.interfaces. \
    udd_dnp3.pydnp3.src.dnp3_python.outstation_new import MyOutStationNew
from services.core.PlatformDriverAgent.platform_driver.interfaces. \
    udd_dnp3.pydnp3.src.dnp3_python.master_new import MyMasterNew
from services.core.PlatformDriverAgent.platform_driver.interfaces. \
    udd_dnp3.udd_dnp3 import UserDevelopRegisterDnp3
from pydnp3 import  opendnp3


class TestDummy:
    """
    Dummy test to check pytest setup
    """

    def test_dummy(self):
        print("I am a silly dummy test.")


# DRIVER_CONFIG = {
#     "driver_config": {"master_ip": "0.0.0.0", "outstation_ip": "127.0.0.1",
#                       "master_id": 2, "outstation_id": 1,
#                       "port": 20000},
#     "registry_config": "config://udd-Dnp3.csv",
#     "driver_type": "udd_dnp3",
#     "interval": 5,
#     "timezone": "UTC",
#     "campus": "campus-vm",
#     "building": "building-vm",
#     "unit": "Dnp3",
#     "publish_depth_first_all": True,
#     "heart_beat_point": "random_bool"
# }

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
    # time.sleep(3)
    yield master_appl
    # clean-up
    master_appl.shutdown()


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

    def test_get_register_value_analog_float(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        analog_input_val = [1.2454, 33453.23, 45.21]
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=30, variation=6 is AnalogInputFloat
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(analog_input_val):
            reg_def = csv_config[i]
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_analog_float_random(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        analog_input_val = [random.random() for i in range(3)]
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=30, variation=6 is AnalogInputFloat
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(analog_input_val):
            reg_def = csv_config[i]
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_analog_int(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        analog_input_val = [345, 1123, 98]
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=30, variation=1 is AnalogInputInt32
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(analog_input_val):
            # reg_def = csv_config[i]
            reg_def = {'Point Name': f'AnalogInput_index{i}', 'Volttron Point Name': f'AnalogInput_index{i}',
                       'Group': '30', 'Variation': '1', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_analog_int_random(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        analog_input_val = [random.randint(1, 100) for i in range(3)]
        for i, val_update in enumerate(analog_input_val):
            outstation_app.apply_update(opendnp3.Analog(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=30, variation=1 is AnalogInputInt32
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(analog_input_val):
            # reg_def = csv_config[i]
            reg_def = {'Point Name': f'AnalogInput_index{i}', 'Volttron Point Name': f'AnalogInput_index{i}',
                       'Group': '30', 'Variation': '1', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_binary_int(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        binary_input_val = [True, False, True]
        for i, val_update in enumerate(binary_input_val):
            outstation_app.apply_update(opendnp3.Binary(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=1, variation=2 is BinaryInput (with flag)
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(binary_input_val):
            # reg_def = csv_config[i]
            reg_def = {'Point Name': f'BinaryInput_index{i}', 'Volttron Point Name': f'BinaryInput_index{i}',
                       'Group': '1', 'Variation': '2', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update

    def test_get_register_value_binary_int_random(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        binary_input_val = [random.choice([True, False]) for i in range(3)]
        for i, val_update in enumerate(binary_input_val):
            outstation_app.apply_update(opendnp3.Binary(value=val_update), index=i)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=1, variation=2 is BinaryInput (with flag)
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(binary_input_val):
            # reg_def = csv_config[i]
            reg_def = {'Point Name': f'BinaryInput_index{i}', 'Volttron Point Name': f'BinaryInput_index{i}',
                       'Group': '1', 'Variation': '2', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update


class TestDNP3RegisterControlWorkflow:

    def test_set_register_value_analog_float(self, outstation_app, master_app, csv_config, dnp3_inherit_init_args):

        # dummy test variable
        # Note: group=40, variation=4 is AnalogOutputDoubleFloat
        analog_output_val = [343.23, 23.1109, 58.2]
        for i, val_set in enumerate(analog_output_val):
            reg_def = {'Point Name': f'AnalogOutput_index{i}', 'Volttron Point Name': f'AnalogOutput_index{i}',
                       'Group': '40', 'Variation': '4', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            dnp3_register.set_register_value(value=val_set)

        # Note: make sure Group, Variation, Index in config are consistent with desired testing dummy
        # Note: group=30, variation=1 is AnalogInputInt32
        # Note: reg_def = csv_config[i], structure example
        # reg_def = {'Point Name': 'AnalogInput_index0', 'Volttron Point Name': 'AnalogInput_index0',
        #            'Group': '30', 'Variation': '6', 'Index': '0', 'Scaling': '1', 'Units': 'NA',
        #            'Writable': 'FALSE', 'Notes': 'Double Analogue input without status'}

        # verify
        for i, val_update in enumerate(analog_output_val):
            # reg_def = csv_config[i]
            reg_def = {'Point Name': f'AnalogOutput_index{i}', 'Volttron Point Name': f'AnalogOutput_index{i}',
                       'Group': '40', 'Variation': '4', 'Index': f"{i}", 'Scaling': '1', 'Units': 'NA',
                       'Writable': 'FALSE', 'Notes': ''}
            dnp3_register = UserDevelopRegisterDnp3(master_application=master_app,
                                                    reg_def=reg_def,
                                                    **dnp3_inherit_init_args
                                                    )
            val_get = dnp3_register.get_register_value()
            # print("===========val_get, val_update", val_get, val_update)
            assert val_get == val_update
class TestPlaceholder:

    def test_placeholder(self, csv_config):
        print("=============", csv_config)
        # k = "driver_config"
        # print("=============", {k:driver_config_in_json_config.get(k)})
