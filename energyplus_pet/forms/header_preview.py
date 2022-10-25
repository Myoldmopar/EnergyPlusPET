from tkinter import Toplevel, Button, Frame, Label, HORIZONTAL, TOP, X
from tkinter.ttk import Separator

from pyperclip import copy

from energyplus_pet.equipment.base import BaseEquipment


class RequiredDataPreviewForm(Toplevel):
    """Allows users to view the required equipment data and copy it to the clipboard"""
    def __init__(self, parent_window, equipment: BaseEquipment):
        super().__init__(parent_window)
        self.title(f"{parent_window.title()}: Header Data Summary")
        headers_summary = equipment.headers().get_descriptive_summary().strip()
        headers_csv = equipment.headers().get_descriptive_csv()
        Label(self, text=equipment.name()).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Label(self, text="Data columns listed here\nData can be entered in any common units").pack(
            side=TOP, fill=X, expand=False, padx=3, pady=3
        )
        Label(self, text=headers_summary).pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        Label(
            self,
            text="If any data uses correction factors,\n constant values can be entered in tabular form \n and "
                 "correction factors are separate from tabulated data. "
        ).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Label(self, text="The equipment needs fixed parameters:").pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        constant_parameters = equipment.get_required_constant_parameters()
        param_summary = '\n'.join([f"{c.title} [{c.unit_type}]" for c in constant_parameters])
        param_csv = "ParameterName,UnitType\n"
        param_csv += '\n'.join([f"{c.title},{c.unit_type}" for c in constant_parameters])
        Label(self, text=param_summary).pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        self._summary = f"{equipment.name()}\n*Columnar data*\n{headers_summary}\n*Parameters*\n{param_summary}"
        self._csv = f"{equipment.short_name()}\n{headers_csv}\n\n{param_csv}"
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        button_frame = Frame(self)
        Button(button_frame, text="Copy Summary to Clipboard", command=self._copy).grid(row=0, column=0, padx=3, pady=3)
        Button(button_frame, text="Copy CSV to Clipboard", command=self._copy_csv).grid(row=0, column=1, padx=3, pady=3)
        Button(button_frame, text="Done", command=self._done).grid(row=0, column=2, padx=3, pady=3)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def _copy(self):
        copy(self._summary)

    def _copy_csv(self):
        copy(self._csv)

    def _done(self):
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wwhp_heating_curve import WaterToWaterHeatPumpHeatingCurveFit
    root = Tk()
    RequiredDataPreviewForm(root, WaterToWaterHeatPumpHeatingCurveFit())
    root.mainloop()
