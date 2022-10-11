from energyplus_pet.data_manager import CatalogDataManager


class ParameterCalculator:
    """
    Handles the optimization routines for calculating performance parameters.
    Basically converts the full catalog data set into best-fit parameters.
    Generalized to work on any equipment type if the equipment instance implements the necessary functions.
    """
    def __init__(self, data: CatalogDataManager):
        self.data = data

    def output(self) -> str:
        return f"{self.data.process()} - Hey\n"
