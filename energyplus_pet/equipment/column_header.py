from typing import List

from energyplus_pet.units import UnitType


class ColumnHeader:
    """Defines a single column of data for an equipment type"""
    def __init__(self, column_name: str, unit_type: UnitType, db: bool = False, wb: bool = False):
        """
        Constructs a single column header

        :param column_name: The string name of this column
        :param unit_type: The UnitType for this column
        :param db: An optional bool flag for whether this column is an air dry-bulb column
        :param wb: An optional bool flag for whether this column is an air wet-bulb column
        """
        self.name = column_name
        self.units_type = unit_type
        self.dry_bulb_column_flag = db
        self.wet_bulb_column_flag = wb


class ColumnHeaderArray:
    """Defines a full set of headers for an equipment type"""
    def __init__(self, columns: List[ColumnHeader]):
        """Constructs an array of columns from a list of column headers"""
        self.columns = columns

    def __len__(self) -> int:
        """Returns the length of the header array, so it can be used in len() expressions"""
        return len(self.columns)

    def unit_array(self) -> List[UnitType]:
        """Returns the list of units for these columns"""
        return [c.units_type for c in self.columns]

    def name_array(self) -> List[str]:
        """Returns the list of strings for these columns"""
        return [c.name for c in self.columns]

    def get_descriptive_summary(self) -> str:
        """Returns a descriptive summary of this set of column headers"""
        response = ""
        for c in self.columns:
            response += f"{c.name} [{c.units_type}]\n"
        return response

    def get_descriptive_csv(self) -> str:
        """Returns a CSV summary of this set of column headers"""
        name_row = ','.join(self.name_array())
        unit_row = ','.join([str(u) for u in self.unit_array()])
        return f"{name_row}\n{unit_row}"

    def get_db_column(self) -> int:
        """Returns a zero-based index of the air dry-bulb column in a set of headers"""
        for i, c in enumerate(self.columns):
            if c.dry_bulb_column_flag:
                return i
        return -1

    def get_wb_column(self) -> int:
        """Returns a zero-based index of the air wet-bulb column in a set of headers"""
        for i, c in enumerate(self.columns):
            if c.wet_bulb_column_flag:
                return i
        return -1
