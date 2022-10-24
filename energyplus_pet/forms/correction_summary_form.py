from enum import Enum, auto
from functools import partial
from platform import system
from tkinter import Toplevel, Frame, Canvas, simpledialog
from tkinter import Button, Label, Listbox, Scrollbar
from tkinter import HORIZONTAL, TOP, X, BOTH, VERTICAL, NW, LEFT, Y, EW, RIGHT
from tkinter import StringVar
from tkinter.ttk import Separator
from typing import List

from energyplus_pet.correction_factor import CorrectionFactor
from energyplus_pet.forms.correction_summary_widget import CorrectionSummaryWidget
from energyplus_pet.forms.basic_message_form import PetMessageForm
from energyplus_pet.equipment.base import BaseEquipment


class Event:
    LinuxWheelUp = '<Button-4>'
    LinuxWheelDown = '<Button-5>'
    WindowsWheelEvent = '<MouseWheel>'
    Configure = '<Configure>'
    WidgetEnter = '<Enter>'
    WidgetLeave = '<Leave>'


class CorrectionFactorSummaryForm(Toplevel):
    """
    This form is where the user will enter basic correction factor summary data.
    """
    class ExitCode(Enum):
        Cancel = auto()
        Done = auto()
        Error = auto()

    def __init__(self, parent_window, equipment: BaseEquipment):
        super().__init__(parent_window, height=200, width=200)
        self.title(f"{parent_window.title()}: Correction Factor Summary Input")
        # store arguments for manipulation here, these are passed by assignment, in this case "by reference"
        self._summary_widgets: List[CorrectionSummaryWidget] = []
        self.factor_summaries: List[CorrectionFactor] = []
        self._equipment = equipment
        self.exit_code = CorrectionFactorSummaryForm.ExitCode.Cancel  # initialize with this value
        self._text_done = 'Done, ready for factor details'
        self._text_skip = 'Skip entering factors'
        # create the gui
        self._build_gui()
        # draw factors, in case there already are any
        self._redraw_factors()
        # finalize UI operations
        self.grab_set()
        self.transient(parent_window)

    def _build_gui(self):
        lbl = Label(self, text="""All data columns should have at least two values.
Without this variation, a curve fit cannot be generated.
Manufacturers often provide tabular data at fixed temperatures/flow.
However, there is often correction factor data that can add variation.
These factors modify the "constant" temp/flow values by replacement or multiplying.
If you have any correction factors, add them here, otherwise, press done to continue.""")
        s_0 = Separator(self, orient=HORIZONTAL)
        #
        correction_factor_outer_frame = Frame(self)
        # need to store the canvas as a member since it is "scrolled" to view the inner frame
        self._factor_canvas = Canvas(correction_factor_outer_frame)
        # need to store the scrollbar because we check what widget we "scrolled" later
        self._scrollbar = Scrollbar(correction_factor_outer_frame, orient=VERTICAL, command=self._factor_canvas.yview)
        # need to store this because it is the actual frame where we place correction factor summaries
        self._correction_factor_inner_frame = Frame(self._factor_canvas, height=20)
        # bind the inner frame's configure event to a lambda that will update the containing canvas
        self._correction_factor_inner_frame.bind(
            Event.Configure, lambda e: self._factor_canvas.configure(scrollregion=self._factor_canvas.bbox("all"))
        )
        self._correction_factor_inner_frame.grid_columnconfigure(0, weight=1)
        # create a window into the inner frame to display on the canvas
        self._factor_canvas.create_window((0, 0), window=self._correction_factor_inner_frame, anchor=NW)
        # configure the canvas to update the scrollbar when the view is changed in any other way
        self._factor_canvas.configure(yscrollcommand=self._scrollbar.set)
        # pack the canvas and the scrollbar inside the outer frame
        self._factor_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=3, pady=3)
        self._scrollbar.pack(side=RIGHT, fill=Y, padx=3, pady=3)
        # bind the mouse entry/exit events to register or deregister mouse wheel listeners
        self._factor_canvas.bind(Event.WidgetEnter, self._bind_mouse_wheel_events)
        self._factor_canvas.bind(Event.WidgetLeave, self._unbind_mouse_wheel_events)
        #
        s_1 = Separator(self, orient=HORIZONTAL)
        button_frame = Frame(self)
        btn_add = Button(button_frame, text="Add Correction Factor (Ctrl-a)", command=self._add_factor_widget)
        self._txt_done_skip = StringVar(value=self._text_skip)
        btn_ok_skip = Button(button_frame, textvariable=self._txt_done_skip, command=self._done_skip)
        btn_cancel = Button(button_frame, text="Cancel Wizard", command=self._cancel)
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
        self.bind('<Key>', self._handle_button_pressed)

    def _handle_button_pressed(self, event):
        # relevant_modifiers
        # mod_shift = 0x1
        mod_control = 0x4
        # mod_alt = 0x20000
        if event.keysym == 'a' and mod_control & event.state:
            self._add_factor_widget()

    def _handle_mouse_wheel_event_linux(self, event, scroll):
        amount_to_scroll_canvas = int(scroll)
        if event.widget == self._scrollbar:
            amount_to_scroll_canvas = int(amount_to_scroll_canvas / 2.0)
        elif isinstance(event.widget, Listbox):
            amount_to_scroll_canvas = 0
        self._factor_canvas.yview_scroll(amount_to_scroll_canvas, "units")

    def _handle_mouse_wheel_event_windows(self, event):
        amount_to_scroll_canvas = int(-1 * (event.delta / 120))
        if event.widget == self._scrollbar:
            amount_to_scroll_canvas = int(amount_to_scroll_canvas / 2.0)
        elif isinstance(event.widget, Listbox):
            amount_to_scroll_canvas = 0
        self._factor_canvas.yview_scroll(amount_to_scroll_canvas, "units")

    def _bind_mouse_wheel_events(self, _):
        if system() == 'Linux':
            self._factor_canvas.bind_all(Event.LinuxWheelUp, partial(self._handle_mouse_wheel_event_linux, scroll=-1))
            self._factor_canvas.bind_all(Event.LinuxWheelDown, partial(self._handle_mouse_wheel_event_linux, scroll=1))
        elif system() == 'Windows':
            self._factor_canvas.bind_all(Event.WindowsWheelEvent, self._handle_mouse_wheel_event_windows)

    def _unbind_mouse_wheel_events(self, _):
        if system() == 'Linux':
            self._factor_canvas.unbind_all(Event.LinuxWheelUp)
            self._factor_canvas.unbind_all(Event.LinuxWheelDown)
        elif system() == 'Windows':
            self._factor_canvas.unbind_all(Event.WindowsWheelEvent)

    def _redraw_factors(self):
        for i, f in enumerate(self._summary_widgets):
            f.grid(row=i, column=0, sticky=EW, padx=3, pady=3)

    def _add_factor_widget(self):
        name = simpledialog.askstring(
            "Correction Factor Name", "Give this correction factor a name", initialvalue="CorrFactorName", parent=self
        )
        if name is None:
            return
        name = name.lower()
        new_widget = CorrectionSummaryWidget(
            self._correction_factor_inner_frame, name, self._equipment, self._remove_a_factor
        )
        self._summary_widgets.append(new_widget)
        self._redraw_factors()
        self._txt_done_skip.set(self._text_done)

    def _remove_a_factor(self):
        indexes_to_remove = []
        for i, f in enumerate(self._summary_widgets):
            if f.remove_me:
                indexes_to_remove.append(i)
        for i in reversed(indexes_to_remove):
            self._summary_widgets[i].destroy()
            del self._summary_widgets[i]
        self._redraw_factors()
        if len(self._summary_widgets) == 0:
            self._txt_done_skip.set(self._text_skip)

    def _done_skip(self):
        self.exit_code = CorrectionFactorSummaryForm.ExitCode.Done
        output_message = ""
        for x in self._summary_widgets:
            if not x.check_ok():
                output_message += f"Errors for {x.cf.name}:\n"
                for e in x.cf.check_ok_messages:
                    output_message += f" - {e}\n"
        if output_message:
            message_window = PetMessageForm(
                self, "Problem with Correction Factor(s)", output_message, justify_message_left=True
            )
            self.wait_window(message_window)
            return
        self.factor_summaries = [x.cf for x in self._summary_widgets]
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.exit_code = CorrectionFactorSummaryForm.ExitCode.Cancel
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit

    root = Tk()
    eq = WaterToAirHeatPumpHeatingCurveFit()
    CorrectionFactorSummaryForm(root, eq)
    root.mainloop()
