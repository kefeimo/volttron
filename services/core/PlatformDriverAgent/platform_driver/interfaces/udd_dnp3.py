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

        val = 1123
        try:
            val = self._get_json_fromrestapi()
            val = str(val)
            print(f"!!!!!!!!!!!!!!!!!!!!{val}")
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!{e}")

        return val

    def _get_json_fromrestapi(self) -> RegisterValue:

        print("=====Look at here. I am evoked======.")
        # print("self.csv_config", self.csv_config)
        print("self.reg_def", self.reg_def)

        # master_application = MyMasterNew()
        # _log.debug('Initialization complete. Master Station in command loop.')

        # scan_result = self.master_application.retrieve_val_by_gv(gv_id=opendnp3.GroupVariationID(30, 6))
        # print(f"===important log: case7 retrieve_val_by_gv default ==== ", datetime.datetime.now(),
        #       scan_result)

        # scan_result: Dict[opendnp3.GroupVariation, Optional[Dict[int, RegisterValue]]] = \
        #     self.master_application.retrieve_all_obj_by_gvids(gv_ids=[opendnp3.GroupVariationID(30, 6),
        #                                                               opendnp3.GroupVariationID(1, 2)])
        # e.g., {GroupVariation.Group30Var6: {0: 7.8, 1: 14.1, 2: 22.2, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0}}
        # e.g., {GroupVariation.Group1Var2: {0: False, 1: False, 2: False, 3: False, 4: False,}}
        # e.g., {GroupVariation.Group30Var6: None}

        # response: json = requests.get(url)
        # response_str: dict = response.json()

        reg_def = self.reg_def
        group = int(reg_def.get("Group"))
        variation = int(reg_def.get("Variation"))
        index = int(reg_def.get("Index"))

        # gv_id = opendnp3.GroupVariationID(30, 6)
        gv_id = opendnp3.GroupVariationID(group=group,
                                          variation=variation)
        scan_result = self.master_application.retrieve_val_by_gv_i(gv_id=gv_id, index=index)
        print(f"///////////group {group}, variation {variation}, index {index}")
        print(f"===important log: case7 retrieve_val_by_gv default ==== ", datetime.datetime.now(),
              scan_result)
        return_point_value = None
        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        if scan_result.get(gv_cls):
            return_point_value = scan_result.get(gv_cls).get(index)

        # try:
        #     scan_result = self.master_application.retrieve_val_by_gv(gv_id=opendnp3.GroupVariationID(group=group,
        #                                                                                              variation=variation))
        #     gv_id = opendnp3.GroupVariationID(group=group, variation=variation)
        #     gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        #     val_storage = self.master_application.soe_handler.gv_ts_ind_val_dict.get(gv_cls)
        #     print(f"//////////val_storage {val_storage}, gv_cls, {gv_cls} {datetime.datetime.now()}")
        #
        # except Exception as e:
        #     print(f"//////////e {e}, group {group}, variation {variation}")
        # print(f"===important log: case7 retrieve_val_by_gv default ==== ", datetime.datetime.now(),
        #       scan_result)
        # # try:
        # #     group = int(reg_def.get("Group"))
        # # except Exception:
        # #     print(Exception)
        # #     # raise "Wrong Group value configuration"
        # # try:
        # #     variation = int(reg_def.get("Variation"))
        # # except Exception:
        # #     print(Exception)
        # #     raise "Wrong Variation value configuration"
        # # try:
        # #     index = int(reg_def.get("Index"))
        # # except Exception:
        # #     print(Exception)
        # #     raise "Wrong Index value configuration"
        # #
        # # # TODO: complete the group+variation family or do it in a smarter way
        # #
        # # try:
        # #     scan_result = self.master_application.retrieve_val_by_gv(gv_id=opendnp3.GroupVariationID(group, variation))
        # #     print(f"===important log: case7 retrieve_val_by_gv default ==== ", datetime.datetime.now(),
        # #           scan_result)
        # # except Exception:
        # #     print(Exception)
        # #     return None
        #
        # return_point_value = None
        # if group == group and variation == variation:
        #     gv = getattr(opendnp3.GroupVariation, f"Group{group}Var{variation}")
        #     print("type(gv)", type(gv))
        #     if scan_result.get(gv):
        #         return_point_value = scan_result.get(gv).get(index)
        #     print("====return_point_value", return_point_value, "type(return_point_value)", type(return_point_value),
        #           "scan result", scan_result)
        # #
        # # # elif group == 30 and variation == 6:
        # # #     return_point_value = scan_result.get(opendnp3.GroupVariation.Group30Var6).get(index)
        # # # elif group == 1 and variation == 2:
        # # #     return_point_value = scan_result.get(opendnp3.GroupVariation.Group1Var2).get(index)
        # # # elif group == 40 and variation == 4:
        # # #     return_point_value = scan_result.get(opendnp3.GroupVariation.Group40Var4).get(index)
        # # # elif group == 10 and variation == 2:
        # # #     return_point_value = scan_result.get(opendnp3.GroupVariation.Group10Var2).get(index)
        # # else:
        # #     _log.warning(f"Group{group}Variation{variation} is not found")
        #
        # # gv = getattr(opendnp3.GroupVariation, f"Group{group}Var{variation}")
        # # print(f"=======test getattr, gv {gv}, group, {group}, var, {variation}")
        # # print("====return_point_value", return_point_value, "scan result", scan_result)

        return return_point_value

    @staticmethod
    def _save_parse_to_float(str_with_comma: str) -> float:
        # Note: the input is in the form like "30,464.1101"
        num: float
        try:
            num = float(str_with_comma.replace(',', ''))
        except ValueError as e:
            print(e)
            num = np.nan
        return num


# TODO-developer: Your code here
# fill in register_types with register types accordingly
# EXAMPLE:
# register_types = [UserDevelopRegister, UserDevelopRegister]
register_types: List[ImplementedRegister]
register_types = [UserDevelopRegisterDnp3] * (4 + 4 + 3 + 3)
# register_types = [UserDevelopRegisterDnp3] * (2)

# boilerplate code. Don't touch me.
try:
    class Interface(WrapperInterface):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.master_application = MyMasterNew()
            print("==============self.master_application = MyMasterNew()")

        def pass_register_types(self):
            return register_types

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
            register: WrapperRegister = register_type(driver_config=driver_config,
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

except Exception as e:
    print(e)
