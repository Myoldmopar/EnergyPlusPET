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
        self.check_ok_last_message = ""

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

    def check_ok(self) -> bool:
        """
        Checks values of this correction factor and returns True or False to indicate success.
        If False, the client can check the .check_ok_last_message for a string message about what is wrong

        :return: True if everything looks good, False if not
        """
        self.check_ok_last_message = ''
        if self.num_corrections < 1:
            self.check_ok_last_message += f"# of corrections ({self.num_corrections}) is less than 1, this is invalid. "
        if self.correction_type not in [CorrectionFactorType.Multiplier, CorrectionFactorType.Replacement]:
            self.check_ok_last_message += f"Correction factor type appears invalid: ({self.correction_type}). "
        if self.base_column_index < 0:
            self.check_ok_last_message += f"Base column index ({self.base_correction}) is less than 0, invalid. "
        if self.base_column_index in self._columns_to_modify:
            self.check_ok_last_message += "Base column index appears in modification column list, invalid. "
        if len(self.base_correction) != self.num_corrections:
            self.check_ok_last_message += 'Size of base corrections does not match num_corrections, invalid. '
        if len(self.mod_correction_data_column_map) != len(self._columns_to_modify):
            self.check_ok_last_message += 'Size of mod correction data does not match columns_to_modify, invalid. '
        for c in self._columns_to_modify:
            if c not in self.mod_correction_data_column_map:
                self.check_ok_last_message += f"Did not find mod column {c} in mod data map keys. "
            elif len(self.mod_correction_data_column_map[c]) != self.num_corrections:
                self.check_ok_last_message += f"Size of column {c} data array in mode data map does not match " \
                                              f"num_corrections = {self.num_corrections}, invalid. "
        if self.check_ok_last_message:  # the message has content, must be a problem
            return False
        return True
