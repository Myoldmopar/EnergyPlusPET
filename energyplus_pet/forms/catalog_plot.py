import matplotlib
matplotlib.use('TkAgg')
# unfortunately, with newer flake8, you cannot tag the code line above with noqa, you have to tag every trailing import
# I considered just ignoring E402 for this project, because it consists of small contained files, but for now, noqa here
import numpy as np  # noqa: E402
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from tkinter import Toplevel, Frame  # containers  # noqa: E402
from tkinter import Button, Label  # widgets  # noqa: E402
from tkinter import TOP, X, BOTH  # appearance stuff  # noqa: E402
from tkinter.ttk import Notebook, Style  # noqa: E402

from energyplus_pet.data_manager import CatalogDataManager  # noqa: E402


class CatalogDataPlotForm(Toplevel):
    def __init__(self, parent_window, _: CatalogDataManager):
        super().__init__(parent_window)
        Label(self, text="Here's some info about this catalog data\nClick through the plots to inspect").pack(
            side=TOP, expand=True, fill=X
        )
        style = Style(self)
        style.configure('my.TNotebook', tabposition='wn')
        plot_notebook = Notebook(self, style='my.TNotebook')
        plot_data = (
            ('Source Side Mass Flow Rate', [0, 1, 2, 3, 4], [5.2, 2.1, 3.1, 3.1, 4.5], 'kg/s'),
            ('Load Side Heat Transfer', [4, 1, 2, 3, 4], [6.2, 2.1, 3.1, 1.1, 4.5], 'Watts'),
            ('Compressor Impeller Size', [5, 1, 3, 3, 4], [7.2, 2.1, 5.1, 3.1, 2.5], 'Inches'),
            ('Other Really Cool Parameters', [5, 1, 3, 3, 4], [7.2, 2.1, 5.1, 3.1, 2.5], 'Inches'),
            ('Other Really Cool Parameters', [5, 1, 3, 3, 4], [7.2, 2.1, 5.1, 3.1, 2.5], 'Inches'),
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
        Button(self, text="OK, Done", command=self.done).pack(side=TOP, expand=False)
        self.wait_visibility()
        self.grab_set()
        self.transient(parent_window)

    def done(self):
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    from tkinter import Tk
    window = Tk()
    cdm = CatalogDataManager()
    start = CatalogDataPlotForm(window, cdm)
    window.mainloop()
