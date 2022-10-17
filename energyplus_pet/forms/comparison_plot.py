from enum import auto, Enum
import matplotlib
matplotlib.use('TkAgg')
# unfortunately, with newer flake8, you cannot tag the code line above with noqa, you have to tag every trailing import
# I considered just ignoring E402 for this project, because it consists of small contained files, but for now, noqa here
import numpy as np  # noqa: E402
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from tkinter import Toplevel  # containers  # noqa: E402

from energyplus_pet.data_manager import CatalogDataManager  # noqa: E402
from energyplus_pet.equipment.base import BaseEquipment  # noqa: E402


class ComparisonPlot(Toplevel):

    class PlotType(Enum):
        RawComparison = auto()
        PercentError = auto()

    def __init__(self, parent_window, _: CatalogDataManager, equip_instance: BaseEquipment, plot_type: PlotType):
        super().__init__(parent_window)
        self.title("Results Comparison")
        fig = Figure(figsize=(7, 5))
        a = fig.add_subplot(111)
        if plot_type == ComparisonPlot.PlotType.RawComparison:
            plot_data = equip_instance.get_absolute_plot_data()
            plot_title = "Model vs. Catalog Data Points"
        else:
            plot_data = equip_instance.get_error_plot_data()
            plot_title = "Percent Error"
        for pd in plot_data:
            if pd[1] == 'line':
                line_arg = '-'
            elif pd[1] == 'point':
                line_arg = '--'
            else:
                raise Exception('bad line type')
            a.plot(np.array(pd[3]), label=pd[0], linestyle=line_arg, color=pd[2])
        a.legend()
        a.set_title(plot_title, fontsize=16)
        # a.set_ylabel(f"[{pd[3]}]", fontsize=14)  # what about different units?
        a.set_xlabel("Catalog Data Points (no order)", fontsize=14)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.get_tk_widget().pack()
        canvas.draw()


if __name__ == "__main__":
    from tkinter import Tk
    from energyplus_pet.equipment.wahp_heating_curve import WaterToAirHeatPumpHeatingCurveFit
    window = Tk()
    cdm = CatalogDataManager()
    eq = WaterToAirHeatPumpHeatingCurveFit()
    ComparisonPlot(window, cdm, eq, ComparisonPlot.PlotType.RawComparison)
    ComparisonPlot(window, cdm, eq, ComparisonPlot.PlotType.PercentError)
    window.mainloop()
