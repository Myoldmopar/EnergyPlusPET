from enum import auto, Enum
from typing import List


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
        # self.correction_is_wb_db: bool
        # self.correction_db_value: float
        self.correction_type: CorrectionFactorType = CorrectionFactorType.Multiplier
        self.base_column_index: int = 0
        self.columns_to_modify: List[int] = []

    def describe(self) -> str:
        return f"CorrectionFactor: {self.name}, {self.num_corrections} {self.correction_type.name} rows, base column " \
               f"{self.base_column_index}, modifies columns {self.columns_to_modify}"
