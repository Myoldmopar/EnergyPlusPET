from enum import auto, Enum
from json import dumps
from typing import Dict, List


class CorrectionFactorType(Enum):
    Multiplier = auto()
    Replacement = auto()


class CorrectionFactor:
    def __init__(self, name: str):
        self.name = name
        # Once we start supporting the wb/db replacement, we'll need to check from the equipment instance
        # to see if it should be offered for this catalog data.  Then we'll need to track whether the user
        # wants it for this particular correction factor.  Then if so I think we need to track the db/wb value separate.
        # The following are the variables that define this correction factor summary, initialize them as needed and the
        # widget should reflect the initialized values by setting Tk Variables appropriately.
        self.num_corrections: int = 5
        self.correction_is_wb_db: bool = False
        self.correction_type: CorrectionFactorType = CorrectionFactorType.Multiplier
        self.base_column_index: int = 0
        self._columns_to_modify: List[int] = []
        # the rest of this data comes from the detail form
        self.correction_db_value: float
        self.base_correction: List[float] = []  # could be multipliers or replacement values
        self.mod_correction_data_column_map: Dict[int, List[float]] = {}

    def set_columns_to_modify(self, mod_column_indices: List[int]) -> None:
        self._columns_to_modify = mod_column_indices
        for i in mod_column_indices:
            self.mod_correction_data_column_map[i] = []

    def get_columns_to_modify(self) -> List[int]:
        return self._columns_to_modify

    def describe(self) -> str:
        return f"""CorrectionFactor: {self.name}
* {self.num_corrections} {self.correction_type.name} rows
* base column {self.base_column_index}
* modifies columns {self._columns_to_modify}
* Base Correction Array {self.base_correction}
* Mod Correction Matrix:
{dumps(self.mod_correction_data_column_map, indent=2)}"""
