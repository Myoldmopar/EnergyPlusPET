from abc import abstractmethod
from typing import Callable, List

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray


class BaseEquipment:

    def this_type(self) -> EquipType:
        return EquipType.InvalidType

    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    def headers(self) -> ColumnHeaderArray: pass

    @abstractmethod
    def to_eplus_idf_object(self) -> str: pass

    @abstractmethod
    def to_parameter_summary(self) -> str: pass

    @abstractmethod
    def to_eplus_epjson_object(self) -> str: pass

    @abstractmethod
    def generate_parameters(
            self, data_manager: CatalogDataManager, cb_progress_initialize: Callable,
            cb_progress_increment: Callable, cb_progress_done: Callable
    ): pass

    @abstractmethod
    def generate_absolute_plot(self): pass

    @abstractmethod
    def generate_error_plot(self): pass

    @staticmethod
    def fill_eplus_object_format(fields: List[str], form: str):
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
