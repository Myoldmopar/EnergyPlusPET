from enum import auto, Enum
from json import dumps
from typing import Dict, List


class CorrectionFactorType(Enum):
    Multiplier = auto()
    Replacement = auto()


class CorrectionFactor:
    """
    This class represents a small data set that is used to modify the base data and create a larger final data set.
    Often times manufacturers will provide equipment data with some independent variables held constant.
    From this data alone, it is not possible to generate a curve fit that is a function of that variable.
    It is common for the manufacturers to provide small separate tables of correction factor data that describe how
    the dependent variables behave as those originally constant values change, using multipliers for the dependent data.
    """
    def __init__(self, name: str):
        """
        Create a new CorrectionFactor instance.  From a user perspective, the correction factor is generated in two
        parts: inputting basic summary data, then inputting detailed tabular data.  Behind the scenes, the construction
        of a correction factor starts with just a name passed in here.  After that, there is a set of summary data
        members initialized to meaningful values for the widget to show.  Finally, once details have been read from
        the user, the data is set here.
        :param name:
        """
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

        # The following are the variables that complete the correction factor details.
        self.correction_db_value: float
        self.base_correction: List[float] = []  # could be multipliers or replacement values
        self.mod_correction_data_column_map: Dict[int, List[float]] = {}

    @property
    def columns_to_modify(self) -> List[int]:
        """Returns the list of columns that this correction factor is designed to modify"""
        return self._columns_to_modify

    @columns_to_modify.setter
    def columns_to_modify(self, mod_column_indices: List[int]):
        """Sets the list of columns that this correction factor modifies, initializes data column map internally"""
        self._columns_to_modify = mod_column_indices
        for i in mod_column_indices:
            self.mod_correction_data_column_map[i] = []

    def describe(self) -> str:
        """Returns a multiline descriptive string for this correction factor"""
        return f"""CorrectionFactor: {self.name}
* {self.num_corrections} {self.correction_type.name} rows
* base column {self.base_column_index}
* modifies columns {self._columns_to_modify}
* Base Correction Array {self.base_correction}
* Mod Correction Matrix:
{dumps(self.mod_correction_data_column_map, indent=2)}"""
