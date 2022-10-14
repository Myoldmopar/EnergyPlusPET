from tkinter import Toplevel, Button, Frame, Label, HORIZONTAL, TOP, X, StringVar
from tkinter.ttk import Separator

from pyperclip import copy

from energyplus_pet.equipment.base import BaseEquipment


class RequiredDataPreviewForm(Toplevel):
    def __init__(self, parent_window, equipment: BaseEquipment):
        super().__init__(parent_window)
        self.summary = equipment.headers().get_descriptive_summary()
        self.csv = equipment.headers().get_descriptive_csv()
        header_string = ""
        column_names = equipment.headers().name_array()
        for h in column_names:
            if h == column_names[-1]:
                header_string += h
            else:
                header_string += f"{h}\n"
        Label(self, text=equipment.name()).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Label(self, text="Data columns listed here\nData can be entered in any common units").pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Label(self, text=self.summary).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        Label(self, text="If any data uses correction factors,\n the constant values are entered in tabular form \n and correction factors are separate from tabulated data.").pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        button_frame = Frame(self)
        Button(button_frame, text="Copy Summary to Clipboard", command=self.copy).grid(row=0, column=0, padx=3, pady=3)
        Button(button_frame, text="Copy CSV to Clipboard", command=self.copy_csv).grid(row=0, column=1, padx=3, pady=3)
        Button(button_frame, text="Done", command=self.done).grid(row=0, column=2, padx=3, pady=3)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        # finalize UI operations
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def copy(self):
        copy(self.summary)

    def copy_csv(self):
        copy(self.csv)

    def done(self):
        self.grab_release()
        self.destroy()
