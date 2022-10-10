from tkinter import Tk

from energyplus_pet.forms.main import EnergyPlusPetWindow


class PetApplication(Tk):
    def __init__(self):
        super().__init__()
        self.main_gui = EnergyPlusPetWindow(self)

    def run(self):
        self.main_gui.run()


def main_gui():
    PetApplication().run()


if __name__ == "__main__":
    main_gui()
