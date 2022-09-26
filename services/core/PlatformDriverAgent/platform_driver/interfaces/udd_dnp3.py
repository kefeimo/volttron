from platform_driver.interfaces.driver_wrapper import WrapperInterface, WrapperRegister
from platform_driver.interfaces.driver_wrapper import ImplementedRegister, RegisterValue
from typing import List, Optional, Dict
import numpy as np
import random
import requests

# TODO-developer: Your code here
# Add dependency as needed, and update in requirements
import json

import logging
import random
import sys

from datetime import datetime

from pydnp3 import opendnp3
from .dnp3_python.master_new import MyMasterNew
from .dnp3_python.outstation_new import MyOutStationNew
from .dnp3_python.master_utils import parsing_gvid_to_gvcls


import datetime
from time import sleep

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
# _log = logging.getLogger("data_retrieval_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)
_log.setLevel(logging.WARNING)
_log.setLevel(logging.ERROR)


# TODO-developer: Your code here
# Change the classname "UserDevelopRegister" as needed
class UserDevelopRegisterDnp3(WrapperRegister):
    # boilerplate code. Don't touch me.
    # def __init__(self,
    #              driver_config: dict,
    #              point_name: str,
    #              data_type: RegisterValue,
    #              units: str, read_only: bool,
    #              default_value: Optional[RegisterValue] = None,
    #              description: str = "",
    #              csv_config=csv_config):  # re-define for redability
    #     super().__init__(driver_config, point_name, data_type, units, default_value, description)
    def __init__(self, *args, **kwargs):
        # self.master_application = MyMasterNew()  # TODO: verify if long-live master_application will block connection
        # self.reg_def = kwargs['reg_def']
        super().__init__(*args, **kwargs)
        self.master_application = kwargs['master_application']
        self.reg_def = kwargs['reg_def']

    def get_register_value(self) -> RegisterValue:
        # TODO-developer: Your code here
        # Implemet get-register-value logic here
        # Note: Keep the method name as it is including the signatures.
        # Use a helper method if needed.

        # EXAMPLE:
        # def get_register_value(self) -> RegisterValue:
        #    return _get_register_value_helper(url=self.driver_config.get("url"))
        # def _get_register_value_helper(self, url: str):
        #    ...

        #         print("silly implementation")
        # the url will be in the config file

        try:
            reg_def = self.reg_def
            group = int(reg_def.get("Group"))
            variation = int(reg_def.get("Variation"))
            index = int(reg_def.get("Index"))
            val = self._get_outstation_pt(self.master_application, group, variation, index)
            val = str(val)

            return val
        except Exception as e:
            # print(f"!!!!!!!!!!!!!!!!!!!!{e}")
            _log.error(e)
            _log.warning("DNP3 driver (master) couldn't collect data from the outstation.")


    @staticmethod
    def _get_outstation_pt(master_application, group, variation, index) -> RegisterValue:
        """
        Core logic to retrieve register value by polling a dnp3 outstation
        Note: using def get_db_by_group_variation_index
        Returns
        -------

        """
        return_point_value = master_application.get_val_by_group_variation_index(group=group,
                                                                                 variation=variation,
                                                                                 index=index)
        # print(f"===important log: case7 get_db_by_group_variation_index ====", datetime.datetime.now(),
        #       return_point_value)
        # return_point_value = result.get()

        return return_point_value

    def set_register_value(self, value, **kwargs) -> Optional[RegisterValue]:
        """
        TODO: docstring
        """
        try:
            reg_def = self.reg_def
            group = int(reg_def.get("Group"))
            variation = int(reg_def.get("Variation"))
            index = int(reg_def.get("Index"))
            val = self._set_outstation_pt(self.master_application, group, variation, index)
            val = str(val)
            # print(f"!!!!!!!!!!!!!!!!!!!!{val}")

            print(f"=========I am a silly for set_point,")
            return val
        except Exception as e:
            # print(f"!!!!!!!!!!!!!!!!!!!!{e}")
            _log.error(e)
            _log.warning("DNP3 driver (master) couldn't collect data from the outstation.")

    @staticmethod
    def _set_outstation_pt(master_application, group, variation, index):
        """
        # TODO: docstring
        -------

        """
        # master_application.send_direct_operate_command(opendnp3.AnalogOutputDouble64(float(p_val)),
        #                                                i,
        #                                                )
        gv_cls = opendnp3.GroupVariationID(group, variation)
        gv_cls_name = gv_cls.getattr()
        # TODO: improve the following type selector logic (only distinguish analog-float and binary for now)
        print(f"=================gv_cls_name {gv_cls_name}")

        return "sdfdsdi"




# TODO-developer: Your code here
# fill in register_types with register types accordingly
# EXAMPLE:
# register_types = [UserDevelopRegister, UserDevelopRegister]
register_types: List[ImplementedRegister]
register_types = [UserDevelopRegisterDnp3] * (4 + 4 + 3 + 3)


# register_types = [UserDevelopRegisterDnp3] * (2)

# boilerplate code. Don't touch me.

class Interface(WrapperInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master_application = MyMasterNew(master_log_level=7)
        self.master_application.start()
        self.register_types = [UserDevelopRegisterDnp3] * (4 + 4 + 3 + 3)

    def pass_register_types(self):
        return self.register_types

    def create_register(self, driver_config,
                        point_name,
                        data_type,
                        units,
                        read_only,
                        default_value,
                        description,
                        csv_config,
                        reg_def,
                        register_type, *args, **kwargs):
        # register: WrapperRegister = register_type(
        register = UserDevelopRegisterDnp3(
                    driver_config=driver_config,
                    point_name=point_name,
                    data_type=data_type,  # TODO: make it more clear in documentation
                    units=units,
                    read_only=read_only,
                    default_value=default_value,
                    description=description,
                    csv_config=csv_config,
                    reg_def=reg_def,
                    master_application=self.master_application
        )
        return register

    def _set_point(self, point_name: str,
                   value: RegisterValue):
        # print(f"=========I am a silly set_point test, point_name {point_name},"
        #       f"value {value}")
