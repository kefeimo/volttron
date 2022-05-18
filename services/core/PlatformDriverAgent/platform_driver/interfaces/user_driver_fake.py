from platform_driver.interfaces.driver_template import TemplateInterface, TemplateRegister
from platform_driver.interfaces.driver_template import ImplementedRegister, RegisterValue
from typing import List, Optional


# TODO-developer: Your code here
# Add dependency as needed, and update in requirements

import random
import datetime
import math


# TODO-developer: Your code here
# Change the classname "UserDevelopRegister" as needed
class UserDevDriverFake(TemplateRegister):

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

        return_value: RegisterValue
        point_name: str = self.point_name
        if point_name == "Heartbeat":
            return_value: bool = self._get_random_bool()
        elif point_name == "EKG":
            return_value: float = self._get_sine_value()
        elif point_name == "OutsideAirTemperature1":
            return_value: float = self._get_random_float()
        elif point_name == "SampleLong1":
            return_value: int = self._get_random_int()
        else:
            raise ValueError("Wrong register for Point Name " + self.point_name)

        return return_value

    @staticmethod
    def _get_sine_value() -> float:
        sin_value: float
        now = datetime.datetime.now()
        seconds_in_radians = math.pi * float(now.second) / 30.0
        sin_value = math.sin(seconds_in_radians)
        return sin_value

    @staticmethod
    def _get_random_float() -> float:
        # TODO: hardcode range here. Parameterize it if needed
        float_range_low: float = -100.
        float_range_high: float = 300.
        return random.uniform(float_range_low, float_range_high)

    @staticmethod
    def _get_random_bool() -> bool:
        return random.choice([True, False])

    @staticmethod
    def _get_random_int() -> int:
        # TODO: hardcode range here. Parameterize it if needed
        int_range_low: int = 1
        int_range_high: int = 13
        return random.randrange(int_range_low, int_range_high)


# TODO-developer: Your code here
# fill in register_types with register types accordingly
# EXAMPLE:
# register_types = [UserDevelopRegister, UserDevelopRegister]
register_types: List[ImplementedRegister]
register_types = [UserDevDriverFake] * 4


# boilerplate code. Don't touch me.
class Interface(TemplateInterface):
    def pass_register_types(self):
        return register_types


