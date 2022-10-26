from copy import deepcopy
from enum import auto, Enum
from typing import List

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType


class CatalogDataManager:
    """
    This class represents a data manager for the entire catalog data set.  This includes
    the primary tabular data, plus any correction factors applied to the data.
    While the equipment definitions define the types of data, the data manager actually stores the data.
    The equipment instances read data from the catalog data manager when processing parameters.
    """

    def __init__(self):
        """
        Create a new CatalogDataManager instance, initializing arrays and flags.
        """
        self._correction_factors: List[CorrectionFactor] = []
        self._base_data: List[List[float]] = []  # inner arrays are column allocated: self.base_data[data_point][column]
        self.data_processed = False
        self.final_data_matrix: List[List[float]] = []
        self.last_error_message = ""

    def add_correction_factor(self, cf: CorrectionFactor) -> None:
        """
        Add a completed correction factor, with summary data and detailed data.

        :param cf: A correction factor instance, expecting to be fully fleshed out with summary and detailed data.
        :return: None
        """
        self._correction_factors.append(cf)

    # TODO: I think a nicer interface here would be add_base_data_column(column_id), and each equip defines column ids
    def add_base_data(self, data: List[List[float]]) -> None:
        """
        Add base data as a list of data point rows, so the array lookup should be data[row][column].
        The data should already be in the calculation_unit for each column.

        Right now this function does not do any checks on the data because the tabular forms are supposed to handle
        all of that, and the apply_correction_factors function does a bunch of checking as well.

        :param data: Catalog base data set in proper units
        :return: None
        """
        self._base_data = data

    def summary(self) -> dict:
        """Returns a string representation of the catalog data manager as it currently exists"""
        return {
            'base_data_in_rows': self._base_data,
            'correction_factors': [cf.describe() for cf in self._correction_factors],
            'final_data_rows': self.final_data_matrix
        }

    class ProcessResult(Enum):
        OK = auto()
        ERROR = auto()

    def apply_correction_factors(self, minimum_data_points: int, db_column: int, wb_column: int) -> ProcessResult:
        """
        Process the base data and correction factors to create one large full dataset.
        Validates the data against a series of tests for data diversity and infinite/out-of-range.

        :return: A ProcessResult enum instance for the success of the process.  If ERROR, then there is a
                 ``last_error_message`` member variable with an explanation of what went wrong.
        """
        self.data_processed = True
        self.final_data_matrix = self._base_data
        for cf in self._correction_factors:
            updated_data_matrix = deepcopy(self.final_data_matrix)  # deep is required for complex lists of lists
            for cf_row in range(cf.num_corrections):  # each row of the cf data implies a new copy of the data set
                for row in updated_data_matrix:
                    new_row = list(row)  # list provides a deep copy of a simple list
                    if cf.correction_type == CorrectionFactorType.Multiplier:
                        new_row[cf.base_column_index] *= cf.base_correction[cf_row]
                    elif cf.correction_type == CorrectionFactorType.Replacement:
                        new_row[cf.base_column_index] = cf.base_correction[cf_row]
                    elif cf.correction_type == CorrectionFactorType.CombinedDbWb:
                        new_row[db_column] = cf.base_correction_db[cf_row]
                        new_row[wb_column] = cf.base_correction_wb[cf_row]
                    for column_to_modify in cf.columns_to_modify:
                        new_row[column_to_modify] *= cf.mod_correction_data_column_map[column_to_modify][cf_row]
                    self.final_data_matrix.append(new_row)
        if len(self.final_data_matrix) < minimum_data_points:
            self.last_error_message = f"Full catalog data set too small. \nData includes {len(self.final_data_matrix)} "
            self.last_error_message += f"rows, but this equipment requires at least {minimum_data_points}."
            return CatalogDataManager.ProcessResult.ERROR
        else:
            if len(self.final_data_matrix) == 0:
                self.last_error_message = "Catalog data appears empty!  Abort!"
                return CatalogDataManager.ProcessResult.ERROR
            for column_index in range(len(self.final_data_matrix[0])):
                this_column_data = [row[column_index] for row in self.final_data_matrix]
                if len(set(this_column_data)) == 1:
                    self.last_error_message = f"Problem with data, column #{column_index} (zero-based) is constant "
                    self.last_error_message += "after factors have been applied.  Each column should contain variation!"
                    return CatalogDataManager.ProcessResult.ERROR
        return CatalogDataManager.ProcessResult.OK

    def reset(self) -> None:
        """
        Resets the catalog data manager to an original state.

        :return: None
        """
        self._correction_factors.clear()
        self.data_processed = False
        self._base_data = []
        self.final_data_matrix: List[List[float]] = []
        self.last_error_message = ""
