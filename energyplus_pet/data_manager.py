from copy import deepcopy
from enum import auto, Enum
from typing import List

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType


class CatalogDataManager:
    """

    """

    def __init__(self):
        """

        """
        self.correction_factors: List[CorrectionFactor] = []
        # allocate the inner array to the number of columns
        # this implies it will be the second index in the lookup
        # self.base_data[data_point][column]
        self.base_data: List[List[float]] = []
        self.data_processed = False
        self.final_data_matrix: List[List[float]] = []
        self.last_error_message = ""

    def add_correction_factor(self, cf: CorrectionFactor):
        """
        Add a completed correction factor, with summary data and detailed data.

        :param cf:
        :return:
        """
        self.correction_factors.append(cf)

    def add_base_data(self, data: List[List[float]]):
        """
        Add base data in rows.  The array lookup should be data[row][column]

        :param data:
        :return:
        """
        self.base_data = data

    class ProcessResult(Enum):
        OK = auto()
        ERROR = auto()

    def process(self, minimum_data_points: int) -> ProcessResult:
        """
        Process the base data and correction factors to create one large full dataset
        Validates the data against a series of tests for data diversity and infinite/out-of-range

        :return: Tuple[bool, str], Bool indicates if the data processing was successful; if not, str is a status message
        """
        # TODO: Add a check() method on the correction factor to validate all the array and index lengths
        # TODO: Assert the sizes of base data and cf match here
        self.data_processed = True
        self.final_data_matrix = self.base_data
        for cf in self.correction_factors:
            updated_data_matrix = deepcopy(self.final_data_matrix)  # deep is required for complex lists of lists
            for cf_row in range(len(cf.base_correction)):  # each row of the cf data implies a new copy of the data set
                for row in updated_data_matrix:
                    new_row = list(row)  # list provides a deep copy of a simple list
                    if cf.correction_type == CorrectionFactorType.Multiplier:
                        new_row[cf.base_column_index] *= cf.base_correction[cf_row]
                    else:  # Replacement
                        new_row[cf.base_column_index] = cf.base_correction[cf_row]
                    for column_to_modify in cf.get_columns_to_modify():
                        new_row[column_to_modify] *= cf.mod_correction_data_column_map[column_to_modify][cf_row]
                    self.final_data_matrix.append(new_row)
        if len(self.final_data_matrix) < minimum_data_points:
            self.last_error_message = f"Full catalog data set too small. \nData includes {len(self.final_data_matrix)} "
            self.last_error_message += f"rows, but this equipment requires at least {minimum_data_points}."
            return CatalogDataManager.ProcessResult.ERROR
        return CatalogDataManager.ProcessResult.OK

    def reset(self):
        """

        :return:
        """
        self.correction_factors.clear()
        self.data_processed = False
        self.base_data = [[]]
