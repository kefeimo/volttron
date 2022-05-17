import abc
import random
import datetime
import math
from math import pi

# from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
# # from ...platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
# from csv import DictReader
# from io import StringIO
# import logging

import requests

from typing import List, Type, Dict, Union, Optional

from platform_driver.interfaces.driver_template import TemplateInterface, TemplateRegister

# alias
ImplementedRegister = Union[TemplateRegister, Type[TemplateRegister]]


class FakeRegister(TemplateRegister):
    def get_register_value(self) -> bool:
        return random.choice([True, False])


class RestAPIRegister(TemplateRegister):

    def get_register_value(self) -> str:
        return self.get_json_str(self.driver_config.get("url"))

    @staticmethod
    def get_json_str(url: str) -> str:
        """
        REST API request
        Return a string (cat fact)

        EXAMPLE:

        Typical response:
        {'fact': "A cat's nose is as unique as a human's fingerprint.", 'length': 51}
        Return:
        "A cat's nose is as unique as a human's fingerprint."

        """
        activity_info_str: str  # return value
        response = requests.get(url)
        response_json: dict = response.json()
        activity_info = response_json
        activity_info_str = str(response_json)
        return activity_info_str

register_types_2 = [
        FakeRegister,
        RestAPIRegister]

class Interface(TemplateInterface):
    register_types: List[ImplementedRegister]  # subclass of Type[TemplateRegister]
    # TODO-developer
    register_types = [
        FakeRegister,
        RestAPIRegister]

    def pass_register_types(self):
        # return self.register_types
        return register_types_2


int_type_for_testing: int
int_type_for_testing = "dfddfssdfdd"

