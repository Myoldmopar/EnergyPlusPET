from tkinter import Toplevel, Button, Frame, Label, simpledialog, HORIZONTAL, TOP, X
from tkinter.ttk import Separator
from typing import List, Union

from energyplus_pet.corrections import CorrectionFactor


class CorrectionFactorForm(Toplevel):
    def __init__(self, parent_window):
        super().__init__(parent_window, height=200, width=200)
        self._factors: List[CorrectionFactor] = []
        self.return_data: Union[None, List[CorrectionFactor]] = None
        # create all the objects
        lbl = Label(self, text="""In order to estimate parameters, all data categories should have at least two values.
If all values are constant, a curve fit cannot be generated.
It is common for manufacturers to only give a constant value for certain data.
This is typically entering temperatures or flow rates.
They will then give correction factor data in order to modify this value.
These correction factors can be new flow rate/temperature values, or multipliers from the base values.
If you have any correction factors, add them here, otherwise, press done to continue.""")
        s_0 = Separator(self, orient=HORIZONTAL)
        self.factor_frame = Frame(self, height=20)
        s_1 = Separator(self, orient=HORIZONTAL)
        button_frame = Frame(self)
        btn_add = Button(button_frame, text="Add Factor", command=self.add_factor)
        btn_ok = Button(button_frame, text="OK", command=self.ok)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
        # pack everything
        lbl.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        s_0.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        self.factor_frame.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        s_1.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        button_frame.pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        btn_add.grid(row=0, column=0, padx=3, pady=3)
        btn_ok.grid(row=0, column=1, padx=3, pady=3)
        btn_cancel.grid(row=0, column=2, padx=3, pady=3)
        # configure the grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        # set up connections/config calls as needed
        pass
        # finalize UI operations
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def draw_factors(self):
        # destroy all widgets from frame
        for widget in self.factor_frame.winfo_children():
            widget.destroy()
        for i, f in enumerate(self._factors):
            f.draw(self.factor_frame).grid(row=i, column=0, padx=3, pady=3)
        self.factor_frame.grid_columnconfigure(0, weight=1)

    def add_factor(self):
        name = simpledialog.askstring("Correction Factor Name", "Give this correction factor a name", parent=self)
        if name is None:
            return
        self._factors.append(CorrectionFactor(name))
        self.draw_factors()

    def ok(self):
        self.return_data = self._factors
        self.grab_release()
        self.destroy()

    def cancel(self):
        self.return_data = None
        self.grab_release()
        self.destroy()
