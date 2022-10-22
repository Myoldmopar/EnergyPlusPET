from enum import Enum, auto
import numpy as np
from tkinter import Toplevel, Frame  # containers
from tkinter import Button, Label  # widgets
from tkinter import TOP, X, BOTH, ALL  # appearance stuff
from tkinter.ttk import Notebook, Style  # ttk specific stuff

from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.units import unit_instance_factory

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


class CatalogDataPlotForm(Toplevel):
    """
    This form is where we display the processed catalog data to the user to allow them to see variation in each
    parameter.
    """
    class ExitCode(Enum):
        OK = auto()
        CANCEL = auto()

    def __init__(self, parent_window, cdm: CatalogDataManager, eq: BaseEquipment):
        super().__init__(parent_window)
        self.exit_code = CatalogDataPlotForm.ExitCode.OK
        Label(self, text="Here's some info about this catalog data\nClick through the plots to inspect").pack(
            side=TOP, expand=True, fill=X
        )
        style = Style(self)
        style.configure('my.TNotebook', tabposition='wn')
        plot_notebook = Notebook(self, style='my.TNotebook')
        plot_data = []
        for col_num in range(len(eq.headers().name_array())):  # TODO: Just loop over headers here
            line_title = eq.headers().name_array()[col_num]
            line_unit_type = eq.headers().unit_array()[col_num]  # TODO: Each header should store a dummy unit instance
            dummy_unit_instance = unit_instance_factory(0.0, line_unit_type)
            line_unit_string = dummy_unit_instance.get_unit_string_map()[dummy_unit_instance.calculation_unit_id()]
            data_vector = [row[col_num] for row in cdm.final_data_matrix]
            x_values = list(range(len(data_vector)))
            plot_data.append(
                (line_title, x_values, data_vector, line_unit_string)
            )
        for pd in plot_data:
            plot_frame = Frame(plot_notebook)
            plot_frame.pack(side=TOP, expand=True, fill=BOTH)
            plot_notebook.add(plot_frame, text=pd[0])
            fig = Figure(figsize=(7, 5))
            a = fig.add_subplot(111)
            a.plot(np.array(pd[1]), np.array(pd[2]))
            a.set_title("Catalog Data Display", fontsize=16)
            a.set_ylabel(f"[{pd[3]}]", fontsize=14)
            a.set_xlabel("Catalog Data Points (no order)", fontsize=14)
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.get_tk_widget().pack()
            canvas.draw()
        plot_notebook.pack(side=TOP, expand=True, fill=BOTH)
        button_frame = Frame(self)
        Button(button_frame, text="Looks good, generate parameters", command=self.ok).grid(
            row=0, column=0, padx=3, pady=3
        )
        Button(button_frame, text="Something is wrong -- cancel", command=self.cancel).grid(
            row=0, column=1, padx=3, pady=3
        )
        button_frame.grid_columnconfigure(ALL, weight=1)
        button_frame.pack(side=TOP, expand=False, fill=X)
        self.grab_set()
        self.transient(parent_window)

    def ok(self):
        self.exit_code = CatalogDataPlotForm.ExitCode.OK
        self.finish()

    def cancel(self):
        self.exit_code = CatalogDataPlotForm.ExitCode.CANCEL
        self.finish()

    def finish(self):
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_cooling_curve import WaterToWaterHeatPumpHeatingCurveFit

    window = Tk()
    _cdm = CatalogDataManager()
    _cdm.add_base_data(
        [
            [1, 2, 3, 4, 5, 6, 7],
            [2, 3, 4, 5, 6, 7, 8],
            [3, 4, 5, 6, 7, 8, 9]
        ]
    )
    _cdm.apply_correction_factors(3)
    start = CatalogDataPlotForm(window, _cdm, WaterToWaterHeatPumpHeatingCurveFit())
    window.mainloop()
