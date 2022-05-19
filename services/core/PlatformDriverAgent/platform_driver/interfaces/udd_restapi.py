from platform_driver.interfaces.driver_wrapper import WrapperInterface, WrapperRegister
from platform_driver.interfaces.driver_wrapper import ImplementedRegister, RegisterValue
from typing import List, Optional
import numpy as np
import random
import requests

# TODO-developer: Your code here
# Add dependency as needed, and update in requirements
import json


# TODO-developer: Your code here
# Change the classname "UserDevelopRegister" as needed
class UDDBitcoinRestAPI(WrapperRegister):
    # boilerplate code. Don't touch me.  # TODO: find a better way to display this
    # def __init__(self,
    #              driver_config: dict,
    #              point_name: str,
    #              data_type: RegisterValue,
    #              units: str, read_only: bool,
    #              default_value: Optional[RegisterValue] = None,
    #              description: str = ""):  # re-define for redability
    #     super().__init__(driver_config, point_name, data_type, units, default_value, description)  # base class1
    #     super().__init__("byte", read_only, point_name, units, description='')  # base class2

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
        return self._get_json_fromrestapi(url=self.driver_config.get("url"))

    def _get_json_fromrestapi(self, url: str) -> RegisterValue:
        response: json = requests.get(url)
        response_str: dict = response.json()

        time_updated: str = response_str.get("time").get("updated")
        bitcoin_usd = response_str.get("bpi").get("USD").get("rate")
        bitcoin_usd = self._save_parse_to_float(bitcoin_usd)
        bitcoin_gbp = response_str.get("bpi").get("GBP").get("rate")
        bitcoin_gbp = self._save_parse_to_float(bitcoin_gbp)
        bitcoin_eur = response_str.get("bpi").get("EUR").get("rate")
        bitcoin_eur = self._save_parse_to_float(bitcoin_eur)

        return_point_value: RegisterValue

        if self.point_name == "time_updated":
            return_point_value = time_updated
        elif self.point_name == "bitcoin_usd":
            return_point_value = bitcoin_usd
        elif self.point_name == "bitcoin_gbp":
            return_point_value = bitcoin_gbp
        elif self.point_name == "bitcoin_eur":
            return_point_value = bitcoin_eur
        elif self.point_name == "random_bool":
            return_point_value: bool = random.choice([True, False])
        else:
            raise ValueError("Wrong register for Point Name " + self.point_name)

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
register_types = [UserDevelopRegisterBitcoinRestAPI] * 4


# boilerplate code. Don't touch me.
class Interface(WrapperInterface):
    def pass_register_types(self):
        return register_types


