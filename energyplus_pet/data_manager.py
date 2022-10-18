from enum import auto, Enum
from typing import List, Tuple

from energyplus_pet.correction_factor import CorrectionFactor


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
        self.base_data: List[List[float]] = [[]]
        self.data_processed = False

    def add_correction_factor(self, cf: CorrectionFactor):
        """

        :param cf:
        :return:
        """
        self.correction_factors.append(cf)

    def add_base_data(self, data: List[List[float]]):
        """

        :param data:
        :return:
        """
        self.base_data = data

    class ProcessResult(Enum):
        """

        """
        OK = auto()
        Error = auto()
        # add more as they are needed

    def process(self) -> Tuple[ProcessResult, str]:
        """
        Process the base data and correction factors to create one large full dataset
        Validates the data against a series of tests for data diversity and infinite/out-of-range

        :return: Tuple[bool, str], Bool indicates if the data processing was successful; if not, str is a status message
        """
        result = '*Pretend Catalog Data Manager*\n'
        for data_point in self.base_data:
            result += str(data_point) + '\n'
        for cf in self.correction_factors:
            result += cf.describe() + '\n'
        self.data_processed = True
        return CatalogDataManager.ProcessResult.OK, result

    def reset(self):
        """

        :return:
        """
        self.correction_factors.clear()
        self.data_processed = False
        self.base_data = [[]]
