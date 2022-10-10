from datetime import datetime
from enum import Enum, auto
from inspect import stack
from queue import Queue
from threading import Thread
from time import sleep
from tkinter import Tk, Button, Frame, Label, BOTH, LEFT, TOP, BOTTOM, \
    NSEW, W, EW, S, X, Y, SW, SUNKEN, END, Menu, IntVar, StringVar, scrolledtext, Scrollbar
from tkinter.ttk import LabelFrame, Progressbar, Treeview, Radiobutton, Checkbutton, Separator, Style

from energyplus_pet import NICE_NAME, VERSION
from energyplus_pet.equipment.types import EquipType


class TreeViewEquipIDMaps:
    def __init__(self):
        self.map = {EquipType.InvalidType: "[INVALID]"}

    def add_to_map(self, equipment_type: EquipType, iid: str) -> None:
        self.map[equipment_type] = iid

    def check_iid(self, iid: str) -> EquipType:
        for k, v in self.map.items():
            if v == iid:
                return k
        return EquipType.InvalidType


class OutputType(Enum):
    IDFObject = auto()
    EpJSONObject = auto()
    ParameterList = auto()


class EnergyPlusPetWindow:
    """A really great parameter estimation tool main window"""

    def __init__(self, root: Tk) -> None:
        """
        The main window of the parameter estimation tool GUI workflow.
        This window stores an instance of tk.Tk since everything GUI-related
        starts with this form.
        """
        self.root = root
        self.program_name = NICE_NAME

        # setup event listeners
        self.gui_queue = Queue()
        self.check_queue()

        # build out the form
        self._build()

    def check_queue(self):
        while True:
            # noinspection PyBroadException
            try:
                task = self.gui_queue.get(block=False)
                self.root.after_idle(task)
            except Exception:
                break
        self.root.after(100, self.check_queue)

    def _build(self):

        # set the GUI title
        self.root.title(f"{NICE_NAME} {VERSION}")

        # now build the top menubar, it's not part of the geometry, but a config parameter on the root Tk object
        menubar = Menu(self.root)
        menu_file = Menu(menubar, tearoff=0)
        menu_file.add_command(label="Reinitialize Form", command=self.reinitialize_form)
        menu_file.add_command(label="Start Catalog Data Wizard", command=self.catalog_data_wizard)
        menu_file.add_command(label="Create Parameters", command=self.create_parameters)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="Operations", menu=menu_file)
        menu_help = Menu(menubar, tearoff=0)
        menu_help.add_command(label="Open documentation", command=self.help_documentation)
        menu_help.add_command(label="What data will I need for selected equipment?", command=self.help_preview_data)
        menu_help.add_command(label="About...", command=self.help_about)
        menubar.add_cascade(label="Help", menu=menu_help)
        self.root.config(menu=menubar)

        label_frame_equip_type = LabelFrame(self.root, text="Equipment Type")
        label_frame_equip_type.grid(row=0, column=0, sticky=NSEW)
        self.tree_equip = Treeview(label_frame_equip_type, columns=('Type',), show='tree')
        # eventually use a defined dictionary somewhere for the tree items and keywords
        self.equip_ids = TreeViewEquipIDMaps()
        tree_root_hp = self.tree_equip.insert(parent='', index='end', text="Heat Pumps", open=True)
        tree_branch_wah = self.tree_equip.insert(parent=tree_root_hp, index='end', text="Water to Air Heating")
        leaf = self.tree_equip.insert(parent=tree_branch_wah, index='end', text="Curve Fit")
        self.equip_ids.add_to_map(EquipType.WAHP_Heating_CurveFit, leaf)
        leaf = self.tree_equip.insert(parent=tree_branch_wah, index='end', text="Parameter Estimation")
        self.equip_ids.add_to_map(EquipType.WAHP_Heating_PE, leaf)
        tree_branch_wac = self.tree_equip.insert(parent=tree_root_hp, index='end', text="Water to Air Cooling")
        leaf = self.tree_equip.insert(parent=tree_branch_wac, index='end', text="Curve Fit")
        self.equip_ids.add_to_map(EquipType.WAHP_Cooling_CurveFit, leaf)
        leaf = self.tree_equip.insert(parent=tree_branch_wac, index='end', text="Parameter Estimation")
        self.equip_ids.add_to_map(EquipType.WAHP_Cooling_PE, leaf)
        tree_branch_wwh = self.tree_equip.insert(parent=tree_root_hp, index='end', text="Water to Water Heating")
        leaf = self.tree_equip.insert(parent=tree_branch_wwh, index='end', text="Curve Fit")
        self.equip_ids.add_to_map(EquipType.WWHP_Heating_CurveFit, leaf)
        tree_branch_wwc = self.tree_equip.insert(parent=tree_root_hp, index='end', text="Water to Water Cooling")
        leaf = self.tree_equip.insert(parent=tree_branch_wwc, index='end', text="Curve Fit")
        self.equip_ids.add_to_map(EquipType.WWHP_Cooling_CurveFit, leaf)
        tree_root_pumps = self.tree_equip.insert(parent='', index='end', text='Pumps', open=True)
        tree_branch_const_pump = self.tree_equip.insert(parent=tree_root_pumps, index='end', text="Constant Speed Pump")
        leaf = self.tree_equip.insert(parent=tree_branch_const_pump, index='end', text='Non-Dimensional')
        self.equip_ids.add_to_map(EquipType.Pump_ConstSpeed_ND, leaf)
        self.tree_equip.pack(side=TOP, padx=3, pady=3, expand=True)
        button_engage = Button(label_frame_equip_type, text='Engage Equipment Type Selection', command=self.engage)
        button_engage.pack(side=TOP, padx=3, pady=3)

        label_frame_control = LabelFrame(self.root, text="Options and Controls")
        label_frame_control.grid(row=0, column=1, sticky=NSEW)
        self.output_type = StringVar(value=OutputType.IDFObject.name)
        Radiobutton(
            label_frame_control, text="IDF Object", value=OutputType.IDFObject.name, variable=self.output_type
        ).pack(side=TOP, anchor=W, padx=3, pady=3)
        Radiobutton(
            label_frame_control, text="EpJSON Object", value=OutputType.EpJSONObject.name, variable=self.output_type
        ).pack(side=TOP, anchor=W, padx=3, pady=3)
        Radiobutton(
            label_frame_control, text="Parameter List", value=OutputType.ParameterList.name, variable=self.output_type
        ).pack(side=TOP, anchor=W, padx=3, pady=3)
        Separator(label_frame_control, orient='horizontal').pack(fill='x', padx=3, pady=3)
        self.create_data_plot = IntVar(value=1)
        Checkbutton(
            label_frame_control, text="Make Data Comparison Plot", variable=self.create_data_plot, onvalue=1, offvalue=0
        ).pack(side=TOP, anchor=W, padx=3, pady=3)
        self.create_error_plot = IntVar(value=1)
        Checkbutton(
            label_frame_control, text="Make Error % Plot", variable=self.create_error_plot, onvalue=1, offvalue=0
        ).pack(side=TOP, anchor=W, padx=3, pady=3)
        Separator(label_frame_control, orient='horizontal').pack(fill='x', padx=3, pady=3)
        button_wizard = Button(label_frame_control, text="Catalog Data Wizard", command=self.catalog_data_wizard)
        button_wizard.pack(side=TOP, padx=3, pady=3)
        Separator(label_frame_control, orient='horizontal').pack(fill='x', padx=3, pady=3)
        button_create = Button(
            label_frame_control, text="Create Parameters", command=self.create_parameters
        )
        button_create.pack(side=TOP, padx=3, pady=3)
        label_progress = Label(label_frame_control, text="Run Progress")
        label_progress.pack(side=TOP, padx=3, pady=3)
        self.progress_value = IntVar()
        self.progress_value.set(0)
        progress_bar = Progressbar(label_frame_control, variable=self.progress_value)
        progress_bar.pack(side=TOP, padx=3, pady=3)
        self.button_save_data = Button(
            label_frame_control, text="Save Output to File", command=self.save_data_to_file, state="disabled",
        )
        self.button_save_data.pack(side=TOP, padx=3, pady=3)

        label_frame_output = LabelFrame(self.root, text="Parameter Output")
        label_frame_output.grid(row=0, column=2, sticky=NSEW)
        horizontal_scroller = Scrollbar(label_frame_output, orient='horizontal')
        horizontal_scroller.pack(side=BOTTOM, fill=X)
        self.text_area = scrolledtext.ScrolledText(
            label_frame_output, wrap='none', width=40, height=20, xscrollcommand=horizontal_scroller.set
        )
        self.text_area.pack(side=TOP, padx=3, pady=3, fill=BOTH, expand=True)
        self.text_area.insert(END, '\n'.join(["BLAH"*12]*40))
        horizontal_scroller.config(command=self.text_area.xview)

        self.status = StringVar(value="Form Initialized, Catalog Data: Empty")
        status_bar = Label(self.root, relief=SUNKEN, anchor=SW, textvariable=self.status)
        status_bar.grid(row=1, column=0, columnspan=3, sticky=S)

        # self.root.grid_rowconfigure(1, weight=1)
        # self.root.grid_columnconfigure(1, weight=1)

    def reinitialize_form(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def catalog_data_wizard(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def create_parameters(self):
        self.progress_value.set(0)
        thd = Thread(target=self.long_runner)  # timer thread
        thd.daemon = True
        thd.start()

    def help_documentation(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def help_preview_data(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def help_about(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def save_data_to_file(self):
        print(f"{self.program_name} : {datetime.now()} : {stack()[0][3]}")

    def engage(self):
        cur_item = self.tree_equip.focus()
        print(f"Selected IID=\"{cur_item}\"; Type={self.equip_ids.check_iid(cur_item)}")

    def handler_background_thread_update(self, value):
        self.progress_value.set(value)

    def callback_background_thread_update(self, x: int):
        self.gui_queue.put(lambda: self.handler_background_thread_update(x))

    def handler_background_thread_done(self):
        pass  # self.lbl.config(text="All done")

    def callback_background_thread_done(self):
        self.gui_queue.put(self.handler_background_thread_done)

    def long_runner(self) -> None:
        total_seconds = 3
        num_iterations = 100
        for x in range(num_iterations):
            self.callback_background_thread_update(x)
            print(x)
            sleep(total_seconds / num_iterations)
        self.callback_background_thread_done()

    def run(self) -> None:
        """
        Executes the Tk main loop to handle all GUI events and update
        """
        self.root.mainloop()
