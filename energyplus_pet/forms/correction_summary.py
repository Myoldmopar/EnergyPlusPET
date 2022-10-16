from enum import Enum, auto
from functools import partial
from platform import system
from tkinter import Toplevel, Frame, Canvas, simpledialog
from tkinter import Button, Label, Listbox, Scrollbar
from tkinter import HORIZONTAL, TOP, X, BOTH, VERTICAL, NW, LEFT, Y, EW, RIGHT
from tkinter import StringVar
from tkinter.ttk import Separator

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment


class Event:
    LinuxWheelUp = '<Button-4>'
    LinuxWheelDown = '<Button-4>'
    WindowsWheelEvent = '<MouseWheel>'
    Configure = '<Configure>'
    WidgetEnter = '<Enter>'
    WidgetLeave = '<Leave>'


class CorrectionFactorSummaryForm(Toplevel):
    class ExitCode(Enum):
        Cancel = auto()
        Done = auto()
        Skip = auto()
        Error = auto()

    def __init__(self, parent_window, data_manager: CatalogDataManager, equipment: BaseEquipment):
        super().__init__(parent_window, height=200, width=200)
        # store arguments for manipulation here, these are passed by assignment, in this case "by reference"
        self.data_manager = data_manager
        self.equipment = equipment
        # initialize an exit code so that the main form knows how this window closed
        self.exit_code = CorrectionFactorSummaryForm.ExitCode.Error
        self.text_done = 'Done'
        self.text_skip = 'Skip'
        # create the gui
        self._build_gui()
        # draw factors, in case there already are any
        self.redraw_factors()
        # finalize UI operations
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def _build_gui(self):
        lbl = Label(self, text="""In order to estimate parameters, all data categories should have at least two values.
        If all values are constant, a curve fit cannot be generated.
        It is common for manufacturers to only give a constant value for certain data.
        This is typically entering temperatures or flow rates.
        They will then give correction factor data in order to modify this value.
        These correction factors can be new flow rate/temperature values, or multipliers from the base values.
        If you have any correction factors, add them here, otherwise, press done to continue.""")
        s_0 = Separator(self, orient=HORIZONTAL)
        #
        correction_factor_outer_frame = Frame(self)
        # need to store the canvas as a member since it is "scrolled" to view the inner frame
        self.factor_canvas = Canvas(correction_factor_outer_frame)
        # need to store the scrollbar because we check what widget we "scrolled" later
        self.scrollbar = Scrollbar(correction_factor_outer_frame, orient=VERTICAL, command=self.factor_canvas.yview)
        # need to store this because it is the actual frame where we place correction factor summaries
        self.correction_factor_inner_frame = Frame(self.factor_canvas, height=20)
        # bind the inner frame's configure event to a lambda that will update the containing canvas
        self.correction_factor_inner_frame.bind(
            Event.Configure, lambda e: self.factor_canvas.configure(scrollregion=self.factor_canvas.bbox("all"))
        )
        # create a window into the inner frame to display on the canvas
        self.factor_canvas.create_window((0, 0), window=self.correction_factor_inner_frame, anchor=NW)
        # configure the canvas to update the scrollbar when the view is changed in any other way
        self.factor_canvas.configure(yscrollcommand=self.scrollbar.set)
        # pack the canvas and the scrollbar inside the outer frame
        self.factor_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=3, pady=3)
        self.scrollbar.pack(side=RIGHT, fill=Y, padx=3, pady=3)
        # bind the mouse entry/exit events to register or deregister mouse wheel listeners
        self.factor_canvas.bind(Event.WidgetEnter, self.bind_wheel)
        self.factor_canvas.bind(Event.WidgetLeave, self.unbind_wheel)
        #
        s_1 = Separator(self, orient=HORIZONTAL)
        button_frame = Frame(self)
        btn_add = Button(button_frame, text="Add Factor", command=self.add_factor)
        self.txt_done_skip = StringVar(value=self.text_skip)
        btn_ok_skip = Button(button_frame, textvariable=self.txt_done_skip, command=self.done_skip)
        btn_cancel = Button(button_frame, text="Cancel", command=self.cancel)
        # pack everything
        lbl.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        s_0.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        correction_factor_outer_frame.pack(side=TOP, fill=BOTH, expand=True, padx=3, pady=3)
        s_1.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        button_frame.pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        btn_add.grid(row=0, column=0, padx=3, pady=3)
        btn_ok_skip.grid(row=0, column=1, padx=3, pady=3)
        btn_cancel.grid(row=0, column=2, padx=3, pady=3)
        # configure the grid
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

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
            self.factor_canvas.bind_all(Event.LinuxWheelUp, partial(self.mouse_wheel, scroll=-1))
            self.factor_canvas.bind_all(Event.LinuxWheelDown, partial(self.mouse_wheel, scroll=1))
        elif system() == 'Windows':
            self.factor_canvas.bind_all(Event.WindowsWheelEvent, self.mouse_wheel_windows)

    def unbind_wheel(self, _):
        if system() == 'Linux':
            self.factor_canvas.unbind_all(Event.LinuxWheelUp)
            self.factor_canvas.unbind_all(Event.LinuxWheelDown)
        elif system() == 'Windows':
            self.factor_canvas.unbind_all(Event.WindowsWheelEvent)

    def redraw_factors(self):
        # destroy all widgets from frame
        for widget in self.correction_factor_inner_frame.winfo_children():
            widget.destroy()
        for i, f in enumerate(self.data_manager.correction_factors):
            f.render_as_tk_frame(self.correction_factor_inner_frame).grid(row=i, column=0, sticky=EW, padx=3, pady=3)
        self.correction_factor_inner_frame.grid_columnconfigure(0, weight=1)

    def add_factor(self):
        name = simpledialog.askstring("Correction Factor Name", "Give this correction factor a name", parent=self)
        if name is None:
            return
        self.data_manager.add_correction_factor(CorrectionFactor(name, self.remove_a_factor))
        self.redraw_factors()
        self.txt_done_skip.set(self.text_done)

    def remove_a_factor(self):
        # delete the widget
        indexes_to_remove = []
        for i, f in enumerate(self.data_manager.correction_factors):
            if f.remove_me:
                indexes_to_remove.append(i)
        for i in reversed(indexes_to_remove):
            del self.data_manager.correction_factors[i]
        self.redraw_factors()
        if len(self.data_manager.correction_factors) == 0:
            self.txt_done_skip.set(self.text_skip)

    def done_skip(self):
        if self.txt_done_skip == self.text_done:
            self.exit_code = CorrectionFactorSummaryForm.ExitCode.Done
        else:
            self.exit_code = CorrectionFactorSummaryForm.ExitCode.Skip
        self.grab_release()
        self.destroy()

    def cancel(self):
        self.grab_release()
        self.destroy()
