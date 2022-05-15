# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright 2020, Battelle Memorial Institute.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This material was prepared as an account of work sponsored by an agency of
# the United States Government. Neither the United States Government nor the
# United States Department of Energy, nor Battelle, nor any of their
# employees, nor any jurisdiction or organization that has cooperated in the
# development of these materials, makes any warranty, express or
# implied, or assumes any legal liability or responsibility for the accuracy,
# completeness, or usefulness or any information, apparatus, product,
# software, or process disclosed, or represents that its use would not infringe
# privately owned rights. Reference herein to any specific commercial product,
# process, or service by trade name, trademark, manufacturer, or otherwise
# does not necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by
# BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}
import abc
import random
import datetime
import math
from math import pi

from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from ...platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from csv import DictReader
from io import StringIO
import logging

import requests

from typing import List, Type, Dict, Union, Optional

# TODO: parse to python_type based on literal. i.e., locate("int")("1") -> int(1)
# Design the data type validation logic (recommend but not enforce?)
type_mapping = {"string": str,
                "int": int,
                "integer": int,
                "float": float,
                "bool": bool,
                "boolean": bool}

# Type alias
RegisterValue = Union[int, str, float, bool]


class TemplateRegister(BaseRegister):
    """
    Template Register, host boilerplate code
    """
    # TODO: do we need to separate read-only and writable register? How a writable register looks like?
    # TODO: e.g., How the set-value pass to the register class?
    # TODO: (Mimic what happen to get_register_value method, we might need a controller method.
    def __init__(self, driver_config: dict, read_only: bool, point_name: str, units: str, reg_type: str,
                 default_value=None, description=''):
        """
        Parameters  # TODO: clean this up,
        ----------
        config_dict: associated with `driver_config` in driver-config.config (json-like file)
                    user inputs are put here, e.g., IP address, url, etc.

        read_only: associated with `Writable` in driver-config.csv
        point_name: associated with `Volttron Point Name` in driver-config.csv
        units: associated with `Units` in driver-config.csv
        reg_type: ?? # TODO: clean this up,
        default_value: ?? # TODO: clean this up,
        description: ?? # TODO: clean this up,

        Associated with Point Name,Volttron Point Name,Units,Units Details,Writable,Starting Value,Type,Notes
            read_only = regDef['Writable'].lower() != 'true'
            point_name = regDef['Volttron Point Name']
            description = regDef.get('Notes', '')
            units = regDef['Units']
            default_value = regDef.get("Starting Value", 'sin').strip()
        """
        super().__init__("byte", read_only, point_name, units, description='')
        self._value: str = ""
        self.config_dict: dict = driver_config
        self.reg_type: str = reg_type
        self.point_name: str = point_name
        self.read_only: bool = read_only

    @property
    def value(self):
        return self.get_register_value()

    @value.setter
    def value(self, x):
        self._value = x

    @abc.abstractmethod
    def get_register_value(self, **kwargs) -> any:
        """
        Override this to get register value
        Examples:
            def get_register_value():
                some_url: str = self.config_dict.get("url")
                return self.get_restAPI_value(url=some_url)
            def get_restAPI_value(url=some_url)
                ...
        Returns
        -------

        """

    # @abc.abstractmethod
    # def set_register_value(self, **kwargs) -> None:  # TODO: need an example/redesign for this
    #     """
    #     Override this to set register value. (Only for writable==True/read_only==False)
    #     Examples:
    #         def set_register_value():
    #             some_temperature: int = get_comfortable_temperature(...)
    #             self.value = some_temperature
    #         def get_comfortable_temperature(**kwargs) -> int:
    #             ...
    #     Returns
    #     -------
    #
    #     """


# alias
ImplementedRegister = Union[TemplateRegister, Type[TemplateRegister]]


class FakeRegister(TemplateRegister):
    def get_register_value(self) -> bool:
        return random.choice([True, False])


class RestAPIRegister(TemplateRegister):

    def get_register_value(self) -> str:
        return self.get_json_str(self.config_dict.get("url"))

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



class TemplateInterface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.point_map: Dict[str, ImplementedRegister] = {}  # {register.point_name: register}

        # TODO: clean up this public interface
        # from *.csv configure file "driver_config": {...}
        # self.config_dict: dict = {}

    def configure(self, config_dict: dict, registry_config_str: List[dict]):
        """
        Used by driver.py
            def get_interface(self, driver_type, config_dict, config_string):
                interface.configure(config_dict, config_string)

        Parameters  # TODO: follow BaseInterface.configure signatures. But the names are wrong.
        ----------
        config_dict: associated with `driver_config` in driver-config.config (json-like file)
                    user inputs are put here, e.g., IP address, url, etc.
        registry_config_str: associated with the whole driver-config.csv file
            Examples:
            [{'Point Name': 'Heartbeat', 'Volttron Point Name': 'Heartbeat', 'Units': 'On/Off',
            'Units Details': 'On/Off', 'Writable': 'TRUE', 'Starting Value': '0', 'Type': 'boolean',
            'Notes': 'Point for heartbeat toggle'},
            {'Point Name': 'Catfact', 'Volttron Point Name': 'Catfact', 'Units': 'No cat fact',
            'Units Details': 'No cat fact', 'Writable': 'TRUE', 'Starting Value': 'No cat fact', 'Type': 'str',
            'Notes': 'Cat fact extract from REST API'}]

        """
        self.parse_config(registry_config_str, config_dict)

    def parse_config(self, csv_config: List[dict], driver_config_in_json_config: dict):  # TODO: this configDict is from *.csv not .config
        print("========================================== csv_config, ", csv_config)
        print("========================================== driver_config_in_json_config, ", driver_config_in_json_config)
        if csv_config is None:
            return

        # TODO-developer: define register lists. Need to match *.csv point orders.
        register_types: List[ImplementedRegister]  # subclass of Type[TemplateRegister]
        register_types = [
            FakeRegister,
            RestAPIRegister, int]

        for regDef, register_type_iter in zip(csv_config, register_types):  # TODO: clean global variable
            # Skip lines that have no address yet.
            if not regDef['Point Name']:
                continue

            read_only = regDef['Writable'].lower() != 'true'
            point_name = regDef['Volttron Point Name']
            description = regDef.get('Notes', '')
            units = regDef['Units']
            default_value = regDef.get("Starting Value", 'sin').strip()
            if not default_value:
                default_value = None
            type_name = regDef.get("Type", 'string')
            reg_type = type_mapping.get(type_name, str)

            # register_type = FakeRegister if not point_name.startswith('Cat') else CatfactRegister  # TODO: change this
            register_type = register_type_iter  # TODO: OMG, who wrote this!!! Instantiate directly.

            register = register_type(driver_config_in_json_config,
                                     read_only,
                                     point_name,
                                     units,
                                     reg_type,
                                     default_value=default_value,
                                     description=description)

            if default_value is not None:
                self.set_default(point_name, register.value)

            self.insert_register(register)

    def insert_register(self, register: TemplateRegister):
        """
        Inserts a register into the :py:class:`Interface`.

        :param register: Register to add to the interface.
        :type register: :py:class:`BaseRegister`
        """
        register_point: str = register.point_name
        self.point_map[register_point] = register

        register_type = register.get_register_type()
        self.registers[register_type].append(register)

    def get_point(self, point_name, **kwargs):
        register: TemplateRegister = self.get_register_by_name(point_name)

        return register.value

    def _set_point(self, point_name, value):  # TODO: this method has some problem. Understand the logic: overall + example
        register: ImplementedRegister = self.get_register_by_name(point_name)
        if register.read_only:
            raise RuntimeError(  # TODO: Is RuntimeError necessary
                "Trying to write to a point configured read only: " + point_name)

        register.value = register.reg_type(value)
        return register.value

    def _scrape_all(self) -> Dict[str, any]:
        result: Dict[str, RegisterValue] = {}  # Dict[register.point_name, register.value]
        read_registers = self.get_registers_by_type(reg_type="byte", read_only=True)  # TODO: Parameterize the "byte" hard-code here
        write_registers = self.get_registers_by_type(reg_type="byte", read_only=False)
        all_registers: List[ImplementedRegister] = read_registers + write_registers
        for register in all_registers:
            result[register.point_name] = register.value
        return result

    def get_register_by_name(self, name: str) -> TemplateRegister:
        """
        Get a register by it's point name.

        :param name: Point name of register.
        :type name: str
        :return: An instance of BaseRegister
        :rtype: :py:class:`BaseRegister`
        """
        try:
            return self.point_map[name]
        except KeyError:
            raise DriverInterfaceError("Point not configured on device: "+name)


class DriverInterfaceError(Exception):
    pass


# class Interface(BasicRevert, BaseInterface):
#     def __init__(self, **kwargs):
#         super(Interface, self).__init__(**kwargs)
#
#         # TODO: clean up this public interface
#         # from *.csv configure file "driver_config": {...}
#         # self.config_dict: dict = {}
#
#     def configure(self, config_dict, registry_config_str):
#         self.parse_config(registry_config_str, config_dict)
#
#     def get_point(self, point_name):
#         register = self.get_register_by_name(point_name)
#
#         return register.value
#
#     def _set_point(self, point_name, value):
#         register = self.get_register_by_name(point_name)
#         if register.read_only:
#             raise RuntimeError(
#                 "Trying to write to a point configured read only: " + point_name)
#
#         register.value = register.reg_type(value)
#         return register.value
#
#     def _scrape_all(self):
#         result = {}
#         read_registers = self.get_registers_by_type("byte", True)
#         write_registers = self.get_registers_by_type("byte", False)
#         for register in read_registers + write_registers:
#             result[register.point_name] = register.value
#
#         return result
#
#     def parse_config(self, configDict, config_dict):  # TODO: this configDict is from *.csv not .config
#         print("========================================== configDict, ", configDict)
#         print("========================================== configDict, ", config_dict)
#         if configDict is None:
#             return
#
#         for regDef, register_type_iter in zip(configDict, register_types):  # TODO: clean global variable
#             # Skip lines that have no address yet.
#             if not regDef['Point Name']:
#                 continue
#
#             read_only = regDef['Writable'].lower() != 'true'
#             point_name = regDef['Volttron Point Name']
#             description = regDef.get('Notes', '')
#             units = regDef['Units']
#             default_value = regDef.get("Starting Value", 'sin').strip()
#             if not default_value:
#                 default_value = None
#             type_name = regDef.get("Type", 'string')
#             reg_type = type_mapping.get(type_name, str)
#
#             # register_type = FakeRegister if not point_name.startswith('Cat') else CatfactRegister  # TODO: change this
#             register_type = register_type_iter  # TODO: OMG, who wrote this!!! Instantiate directly.
#
#             register = register_type(config_dict,
#                                      read_only,
#                                      point_name,
#                                      units,
#                                      reg_type,
#                                      default_value=default_value,
#                                      description=description)
#
#             if default_value is not None:
#                 self.set_default(point_name, register.value)
#
#             self.insert_register(register)
