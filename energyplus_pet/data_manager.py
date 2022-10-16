from typing import List

from energyplus_pet.correction_factor import CorrectionFactor


class CatalogDataManager:
    def __init__(self):
        self.correction_factors: List[CorrectionFactor] = []
        self.base_data = ''
        self.data_processed = False

    def add_correction_factor(self, cf: CorrectionFactor):
        self.correction_factors.append(cf)

    def add_base_data(self, data: str):
        self.base_data = data

    def process(self) -> str:
        result = '*Pretend Catalog Data Manager*'
        result += '\n' + self.base_data
        for cf in self.correction_factors:
            result += '\n' + cf.name
        self.data_processed = True
        return result

    def reset(self):
        self.correction_factors.clear()
        self.data_processed = False
        self.base_data = ''
