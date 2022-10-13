from enum import Enum, auto
from functools import partial
from platform import system
from tkinter import Toplevel, Button, Frame, Label, simpledialog, HORIZONTAL, TOP, X, StringVar, BOTH, Canvas, \
    Scrollbar, VERTICAL, NW, LEFT, Y, Listbox, EW
from tkinter.ttk import Separator

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment


class CorrectionFactorFormResponse(Enum):
    Cancel = auto()
    Done = auto()
    Skip = auto()
    Error = auto()


class CorrectionFactorForm(Toplevel):
    def __init__(self, parent_window, data_manager: CatalogDataManager, equipment: BaseEquipment):
        super().__init__(parent_window, height=200, width=200)
        # store some
        self.data_manager = data_manager
        self.equipment = equipment
        self.exit_code = CorrectionFactorFormResponse.Error
        # create all the objects
        lbl = Label(self, text="""In order to estimate parameters, all data categories should have at least two values.
If all values are constant, a curve fit cannot be generated.
It is common for manufacturers to only give a constant value for certain data.
This is typically entering temperatures or flow rates.
They will then give correction factor data in order to modify this value.
These correction factors can be new flow rate/temperature values, or multipliers from the base values.
If you have any correction factors, add them here, otherwise, press done to continue.""")
        s_0 = Separator(self, orient=HORIZONTAL)
        #
        quick_frame = Frame(self)
        self.factor_canvas = Canvas(quick_frame)
        self.scrollbar = Scrollbar(quick_frame, orient=VERTICAL, command=self.factor_canvas.yview)
        self.scrollable_factor_frame = Frame(self.factor_canvas, height=20)
        self.scrollable_factor_frame.bind(
            "<Configure>", lambda e: self.factor_canvas.configure(scrollregion=self.factor_canvas.bbox("all"))
        )
        self.factor_canvas.create_window((0, 0), window=self.scrollable_factor_frame, anchor=NW)
        self.factor_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.factor_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=3, pady=3)
        self.scrollbar.pack(side='right', fill=Y, padx=3, pady=3)
        self.factor_canvas.bind('<Enter>', self.bind_wheel)
        self.factor_canvas.bind('<Leave>', self.unbind_wheel)
        #
        s_1 = Separator(self, orient=HORIZONTAL)
        button_frame = Frame(self)
        btn_add = Button(button_frame, text="Add Factor", command=self.add_factor)
        self.txt_ok_skip = StringVar(value="Skip")
        btn_ok_skip = Button(button_frame, textvariable=self.txt_ok_skip, command=self.ok_skip)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
        # pack everything
        lbl.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        s_0.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        quick_frame.pack(side=TOP, fill=BOTH, expand=True, padx=3, pady=3)
        s_1.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        btn_add.grid(row=0, column=0, padx=3, pady=3)
        btn_ok_skip.grid(row=0, column=1, padx=3, pady=3)
        btn_cancel.grid(row=0, column=2, padx=3, pady=3)
        # configure the grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        # draw factors, in case there already are any
        self.redraw_factors()
        # set up connections/config calls as needed
        pass
        # finalize UI operations
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def mouse_wheel(self, event, scroll):
        amount_to_scroll_canvas = int(scroll)
        if event.widget == self.scrollbar:
            amount_to_scroll_canvas = int(amount_to_scroll_canvas / 2.0)
        elif isinstance(event.widget, Listbox):
            amount_to_scroll_canvas = 0
        self.factor_canvas.yview_scroll(amount_to_scroll_canvas, "units")

    def mouse_wheel_windows(self, event):
        amount_to_scroll_canvas = int(-1 * (event.delta / 120))
        if event.widget == self.scrollbar:
            amount_to_scroll_canvas = int(amount_to_scroll_canvas / 2.0)
        elif isinstance(event.widget, Listbox):
            amount_to_scroll_canvas = 0
        self.factor_canvas.yview_scroll(amount_to_scroll_canvas, "units")

    def bind_wheel(self, _):
        if system() == 'Linux':
            self.factor_canvas.bind_all("<Button-4>", partial(self.mouse_wheel, scroll=-1))
            self.factor_canvas.bind_all("<Button-5>", partial(self.mouse_wheel, scroll=1))
        elif system() == 'Windows':
            self.factor_canvas.bind_all("<MouseWheel>", self.mouse_wheel_windows)

    def unbind_wheel(self, _):
        if system() == 'Linux':
            self.factor_canvas.unbind_all("<Button-4>")
            self.factor_canvas.unbind_all("<Button-5>")
        elif system() == 'Windows':
            self.factor_canvas.unbind_all("<MouseWheel>")

    def redraw_factors(self):
        # destroy all widgets from frame
        for widget in self.scrollable_factor_frame.winfo_children():
            widget.destroy()
        for i, f in enumerate(self.data_manager.correction_factors):
            f.render_as_tk_frame(self.scrollable_factor_frame).grid(row=i, column=0, sticky=EW, padx=3, pady=3)
        self.scrollable_factor_frame.grid_columnconfigure(0, weight=1)
        if len(self.data_manager.correction_factors) > 0:
            self.txt_ok_skip.set("OK")

    def add_factor(self):
        name = simpledialog.askstring("Correction Factor Name", "Give this correction factor a name", parent=self)
        if name is None:
            return
        self.data_manager.add_correction_factor(CorrectionFactor(name, self.remove_a_factor))
        self.redraw_factors()

    def remove_a_factor(self):
        # delete the widget
        indexes_to_remove = []
        for i, f in enumerate(self.data_manager.correction_factors):
            if f.remove_me:
                indexes_to_remove.append(i)
        for i in reversed(indexes_to_remove):
            del self.data_manager.correction_factors[i]
        self.redraw_factors()

    def ok_skip(self):
        if self.txt_ok_skip == "OK":
            self.exit_code = CorrectionFactorFormResponse.Done
        else:
            self.exit_code = CorrectionFactorFormResponse.Skip
        self.grab_release()
        self.destroy()

    def cancel(self):
        self.grab_release()
        self.destroy()
