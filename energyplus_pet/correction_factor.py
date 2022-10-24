from enum import auto, Enum
from json import dumps
from typing import Dict, List


class CorrectionFactorType(Enum):
    Multiplier = auto()
    Replacement = auto()
    CombinedDbWb = auto()


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
        self.name: str = name
        self.check_ok_messages: List[str] = []

        # The following are the variables that define this correction factor summary, initialize them as needed and the
        # widget should reflect the initialized values by setting Tk Variables appropriately.
        self.num_corrections: int = 5
        self.correction_type: CorrectionFactorType = CorrectionFactorType.Multiplier
        self.base_column_index: int = -1
        self._columns_to_modify: List[int] = []

        # for normal corrections, just keep one array of base column data
        self.base_correction: List[float] = []  # could be multipliers or replacement values
        # for db/wb corrections, just keep two separate arrays
        self.base_correction_db: List[float] = []  # could be multipliers or replacement values
        self.base_correction_wb: List[float] = []  # could be multipliers or replacement values
        # keep a dict of dependent variable modifiers keyed off of the equipment column number
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
        response = f"CorrectionFactor: {self.name}\n"
        response += f"* {self.num_corrections} {self.correction_type.name} rows\n"
        if self.correction_type != CorrectionFactorType.CombinedDbWb:
            response += f"* base column: {self.base_column_index}\n"
            response += f"* Base Correction Array: {self.base_correction}\n"
        else:
            response += "* base columns are equipment db/wb columns\n"
            response += f"* Base dry-bulb correction array: {self.base_correction_db}"
            response += f"* Base wet-bulb correction array: {self.base_correction_wb}"
        response += f"* modifies columns {self._columns_to_modify}\n"
        response += "* Mod Correction Matrix:\n"
        response += dumps(self.mod_correction_data_column_map, indent=2)
        return response

    def check_ok(self, db_column: int, wb_column: int, summary_only: bool = False) -> bool:
        """
        Checks values of this correction factor and returns True or False to indicate success.
        If False, the client can check the .check_ok_last_message for a string message about what is wrong

        :param db_column: The dry-bulb column from the current equipment headers().get_db_column()
        :param wb_column: The wet-bulb column from the current equipment headers().get_wb_column()
        :param summary_only: If this is True, it will only check summary data, not the full data set
        :return: True if everything looks good, False if not
        """
        self.check_ok_messages.clear()
        if self.num_corrections < 1:
            self.check_ok_messages.append(
                f"# of corrections ({self.num_corrections}) is less than 1, this is invalid."
            )
        if self.correction_type not in list(CorrectionFactorType):
            self.check_ok_messages.append(
                f"Correction factor type appears invalid: ({self.correction_type})."
            )
        if not self.correction_type == CorrectionFactorType.CombinedDbWb:
            if self.base_column_index < 0:
                self.check_ok_messages.append(
                    f"Base column index ({self.base_column_index}) is less than 0, invalid."
                )
            if self.base_column_index in self._columns_to_modify:
                self.check_ok_messages.append(
                    "Base column index appears in modification column list, invalid."
                )
        else:  # is a wet-bulb/dry-bulb type
            if db_column in self._columns_to_modify:
                self.check_ok_messages.append(
                    "Dry-bulb column index appears in modification column list, invalid."
                )
            if wb_column in self._columns_to_modify:
                self.check_ok_messages.append(
                    "Wet-bulb column index appears in modification column list, invalid."
                )
        if not summary_only:
            if not self.correction_type == CorrectionFactorType.CombinedDbWb:
                if len(self.base_correction) != self.num_corrections:
                    self.check_ok_messages.append(
                        'Size of base corrections does not match num_corrections, invalid.'
                    )
            else:
                if len(self.base_correction_db) != self.num_corrections:
                    self.check_ok_messages.append(
                        'Size of base dry-bulb corrections does not match num_corrections, invalid.'
                    )
                if len(self.base_correction_wb) != self.num_corrections:
                    self.check_ok_messages.append(
                        'Size of base wet-bulb corrections does not match num_corrections, invalid.'
                    )
            if len(self.mod_correction_data_column_map) != len(self._columns_to_modify):
                self.check_ok_messages.append(
                    'Size of mod correction data does not match columns_to_modify, invalid.'
                )
            for c in self._columns_to_modify:
                if c not in self.mod_correction_data_column_map:
                    self.check_ok_messages.append(
                        f"Did not find mod column {c} in mod data map keys."
                    )
                elif len(self.mod_correction_data_column_map[c]) != self.num_corrections:
                    self.check_ok_messages.append(
                        f"Size of column {c} data array in mode data map does not match num_corrections = "
                        f"{self.num_corrections}, invalid. "
                    )
        if self.check_ok_messages:  # the message has content, must be a problem
            return False
        return True
