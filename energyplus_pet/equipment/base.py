from abc import abstractmethod
from typing import Callable, List, Tuple

from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray
from energyplus_pet.units import BaseUnit


class BaseEquipment:

    def this_type(self) -> EquipType:
        return EquipType.InvalidType

    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    def short_name(self) -> str: pass

    @abstractmethod
    def headers(self) -> ColumnHeaderArray: pass

    @abstractmethod
    def required_constant_parameters(self) -> List[BaseUnit]: pass

    @abstractmethod
    def set_required_constant_parameter(self, parameter_name: str, new_value: float) -> None: pass

    @abstractmethod
    def to_eplus_idf_object(self) -> str: pass

    @abstractmethod
    def to_parameter_summary(self) -> str: pass

    @abstractmethod
    def to_eplus_epjson_object(self) -> str: pass

    @abstractmethod
    def get_number_of_progress_steps(self) -> int: pass

    @abstractmethod
    def minimum_data_points_for_generation(self) -> int: pass

    @abstractmethod
    def generate_parameters(self, data_manager, cb_progress_increment: Callable, cb_progress_done: Callable): pass

    @abstractmethod
    def get_absolute_plot_data(self) -> Tuple: pass

    @abstractmethod
    def get_error_plot_data(self) -> Tuple: pass

    # noinspection PyMethodMayBeStatic
    def get_extra_regression_metrics(self) -> Tuple:
        return ()

    @staticmethod
    def fill_eplus_object_format(fields: List[str], form: str) -> str:
        preferred_spaces = 16
        hanging_indent_string = " "*4
        pads = []
        string_fields = [str(x) for x in fields]
        for f in string_fields:
            this_padding = preferred_spaces - len(f)
            this_padding = max(2, this_padding)
            pads.append(" "*this_padding)
        all_tokens = []
        for f, p in zip(string_fields, pads):
            all_tokens.append(hanging_indent_string + f)
            all_tokens.append(p)
        return form.format(*all_tokens)
