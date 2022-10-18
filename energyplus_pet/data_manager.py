from typing import List


class CatalogDataManager:
    def __init__(self):
        self.cf_summaries: List[str] = []  # TODO: This should be the very thin CorrectionFactor class from the widget
        self.base_data = ''
        self.data_processed = False

    def add_correction_factor(self, cf: str):
        self.cf_summaries.append(cf)

    def add_base_data(self, data: str):
        self.base_data = data

    def process(self) -> str:
        result = '*Pretend Catalog Data Manager*'
        result += '\n' + self.base_data
        for cf in self.cf_summaries:
            result += '\n' + cf  # .name
        self.data_processed = True
        return result

    def reset(self):
        self.cf_summaries.clear()
        self.data_processed = False
        self.base_data = ''
