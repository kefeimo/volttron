import pytest
import gevent
import logging
import time

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
def outstation_app():
    """
    outstation using default configuration (including default database)
    """

    outstation_appl = MyOutStationNew()
    outstation_appl.start()
    # time.sleep(3)
    yield outstation_appl
    # clean-up
    # note: will cause "Fatal Python error: Aborted" Cannot capture
    outstation_appl.shutdown()


@pytest.fixture
def master_app(outstation_app):
    """
    master station using default configuration
    Note: outstation needs to exist first to make connection.
    """

    master_appl = MyMasterNew()
    master_appl.start()
    # time.sleep(3)
    yield master_appl
    # clean-up
    master_appl.shutdown()





class TestRegister:
    # def __init__(self):
    #     self.master_app = master_app
    #     self.outstation_app = outstation_app

    def test_station_init(self, master_app, outstation_app):
        # master_app = MyMasterNew()
        # master_app.start()
        driver_wrapper_init_arg = {'driver_config': {}, 'point_name': "", 'data_type': "", 'units': "", 'read_only': ""}
        UserDevelopRegisterDnp3(master_application=master_app, reg_def={},
                                **driver_wrapper_init_arg)

    def test_get_val_AnalogInputFloat(self, master_app, outstation_app):
        # master_app = MyMasterNew()
        # master_app.start()
        analog_input_val = [1.2454, 33453.23, 45.21]
        outstation_app.apply_update(opendnp3.Analog(value=analog_input_val[0],
                                                    flags=opendnp3.Flags(24),
                                                    time=opendnp3.DNPTime(3094)), 0)
        outstation_app.apply_update(opendnp3.Analog(value=analog_input_val[1],
                                                    flags=opendnp3.Flags(24),
                                                    time=opendnp3.DNPTime(3094)), 1)
        outstation_app.apply_update(opendnp3.Analog(value=analog_input_val[2],
                                                    flags=opendnp3.Flags(24),
                                                    time=opendnp3.DNPTime(3094)), 2)
        driver_wrapper_init_arg = {'driver_config': {}, 'point_name': "", 'data_type': "", 'units': "", 'read_only': ""}
        UserDevelopRegisterDnp3(master_application=master_app, reg_def={},
                                **driver_wrapper_init_arg)
        # get_vals =
        # [val for val in master_app.get_db_by_group_variation_index()]
        val = master_app.get_val_by_group_variation_index(group=30, variation=6, index=0)
        print(f"========val {val}")


class TestPlaceholder:

    def test_placeholder(self):
        master_app = MyMasterNew()
        master_app.start()
        driver_wrapper_init_arg = {'driver_config': {}, 'point_name': "", 'data_type': "", 'units': "", 'read_only': ""}
        UserDevelopRegisterDnp3(master_application=master_app, reg_def={},
                                **driver_wrapper_init_arg)
