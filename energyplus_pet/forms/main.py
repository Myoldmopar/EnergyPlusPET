from datetime import datetime
from enum import Enum, auto
from inspect import stack
from pathlib import Path
from queue import Queue
from threading import Thread
from time import sleep
from tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y  # widget sides and directions to use in widget.pack commands
from tkinter import END  # key used when adding data to the scrolledText object
from tkinter import IntVar, StringVar  # GUI variables
from tkinter import NSEW, W, EW, SW  # sticky cardinal directions to use in widget grid commands
from tkinter import SUNKEN, DISABLED, ACTIVE  # attributes used to modify widget appearance
from tkinter import Tk, Button, Frame, Label, PhotoImage, scrolledtext, Scrollbar, Menu  # widgets
from tkinter import messagebox  # simple dialogs for user messages
from tkinter.ttk import LabelFrame, Progressbar, Treeview, Radiobutton, Checkbutton, Separator  # special ttk widgets

from energyplus_pet import NICE_NAME, VERSION
from energyplus_pet.calculator import ParameterCalculator
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.types import EquipType
from energyplus_pet.forms.corrections import CorrectionFactorForm


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


class EnergyPlusPetWindow(Tk):
    """A really great parameter estimation tool main window"""

    def __init__(self) -> None:
        """
        The main window of the parameter estimation tool GUI workflow.
        This window is an instance of a tk.Tk object
        """
        super().__init__()

        # set some basic program information like title and an icon
        self.program_name = NICE_NAME
        program_name_with_version = f"{self.program_name} {VERSION}"
        self.title(program_name_with_version)
        icon_path = Path(__file__).parent / 'favicon.png'
        image = PhotoImage(file=str(icon_path))
        self.iconphoto(True, image)

        # setup event listeners
        self.gui_queue = Queue()
        self.check_queue()

        # define the Tk.Variable instances that will be used to communicate with the GUI widgets
        self._define_tk_variables()

        # build out the form and specify a minimum size, which may not be uniform across platforms
        self._build_gui()
        self.minsize(1000, 410)

        # set up some important member variables
        self.full_data_set = None
        self.selected_equip_type = EquipType.InvalidType
        self.catalog_data_in_place = False
        self.catalog_data_manager = CatalogDataManager()
        self.calculator = None

        # window setup operations
        self.update_status("Program Initialized")
        self.set_button_status()

    def check_queue(self):
        while True:
            # noinspection PyBroadException
            try:
                task = self.gui_queue.get(block=False)
                self.after_idle(task)
            except Exception:
                break
        self.after(100, self.check_queue)

    def _define_tk_variables(self):
        """
        Creates and initializes all the Tk.Variable instances used in the GUI for two-way communication
        :return:
        """
        self.var_output_type = StringVar(value=OutputType.IDFObject.name)
        self.var_data_plot = IntVar(value=1)
        self.var_error_plot = IntVar(value=1)
        self.var_progress = IntVar(value=0)
        self.var_status = StringVar(value="Form Initialized, Catalog Data: Empty")

    def _build_gui(self):

        # now build the top menubar, it's not part of the geometry, but a config parameter on the root Tk object
        self._build_menu()

        # create an instance of the equipment id/tree mapping and then build the tree GUI contents
        self.equip_ids = TreeViewEquipIDMaps()
        label_frame_equip_type = LabelFrame(self, text="Equipment Type")
        self._build_treeview(label_frame_equip_type)

        # build the options/controls GUI contents
        label_frame_control = LabelFrame(self, text="Options and Controls")
        self._build_controls(label_frame_control)

        # build the output GUI contents
        label_frame_output = LabelFrame(self, text="Parameter Output")
        self._build_output(label_frame_output)

        # build the status bar
        status_frame = Frame(self)
        Label(status_frame, relief=SUNKEN, anchor=SW, textvariable=self.var_status).pack(fill=BOTH, expand=True)

        # pack the parent objects on the GUI
        label_frame_equip_type.grid(row=0, column=0, sticky=NSEW)
        label_frame_control.grid(row=0, column=1, sticky=NSEW)
        label_frame_output.grid(row=0, column=2, sticky=NSEW)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=EW)

        # set up the weight of each row (even) and column (distributed) for a nice looking GUI
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=4)

    def _build_menu(self):
        menubar = Menu(self)
        menu_file = Menu(menubar, tearoff=0)
        menu_file.add_command(label="Start Catalog Data Wizard", command=self.catalog_data_wizard)
        menu_file.add_command(label="Create Parameters", command=self.create_parameters)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="Operations", menu=menu_file)
        menu_help = Menu(menubar, tearoff=0)
        menu_help.add_command(label="Open documentation", command=self.help_documentation)
        menu_help.add_command(label="What data will I need for selected equipment?", command=self.help_preview_data)
        menu_help.add_command(label="About...", command=self.help_about)
        menubar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=menubar)

    def _build_treeview(self, container):
        equip_type_scrollbar = Scrollbar(container)
        # I don't believe the Treeview object can interact with a Tk.Variable, so the tree is stored on the class
        self.tree_equip = Treeview(container, columns=('Type',), show='tree', yscrollcommand=equip_type_scrollbar.set)
        equip_type_scrollbar.config(command=self.tree_equip.yview)
        # eventually use a defined dictionary somewhere for the tree items and keywords
        tree_root_hp = self.tree_equip.insert(parent='', index='end', text="Heat Pumps", open=True)
        tree_branch_wah = self.tree_equip.insert(
            parent=tree_root_hp, index='end', text="Water to Air Heating", open=True  # leave it open as the default
        )
        leaf = self.tree_equip.insert(parent=tree_branch_wah, index='end', text="Curve Fit")
        self.equip_ids.add_to_map(EquipType.WAHP_Heating_CurveFit, leaf)
        initial_focus = leaf
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
        # COMPONENT_EXTENSION 08: Add more nodes to the treeview based on the type added
        self.tree_equip.pack(side=LEFT, padx=3, pady=3, fill=BOTH, expand=True)
        equip_type_scrollbar.pack(side=RIGHT, padx=0, pady=3, fill=Y, expand=False)

        self.tree_equip.focus(initial_focus)
        self.tree_equip.selection_set(initial_focus)

    def _build_controls(self, container):
        Radiobutton(
            container, text="IDF Object", value=OutputType.IDFObject.name, variable=self.var_output_type
        ).pack(
            side=TOP, anchor=W, padx=3, pady=3
        )
        Radiobutton(
            container, text="EpJSON Object", value=OutputType.EpJSONObject.name, variable=self.var_output_type
        ).pack(
            side=TOP, anchor=W, padx=3, pady=3
        )
        Radiobutton(
            container, text="Parameter List", value=OutputType.ParameterList.name, variable=self.var_output_type
        ).pack(
            side=TOP, anchor=W, padx=3, pady=3
        )
        Separator(container, orient='horizontal').pack(fill='x', padx=3, pady=3)
        Checkbutton(
            container, text="Make Data Comparison Plot", variable=self.var_data_plot, onvalue=1, offvalue=0
        ).pack(
            side=TOP, anchor=W, padx=3, pady=3
        )
        Checkbutton(
            container, text="Make Error % Plot", variable=self.var_error_plot, onvalue=1, offvalue=0
        ).pack(
            side=TOP, anchor=W, padx=3, pady=3
        )
        Separator(container, orient='horizontal').pack(fill='x', padx=3, pady=3)
        Button(container, text='Engage Equipment Type', command=self.engage).pack(side=TOP, padx=3, pady=3)
        self.button_catalog = Button(container, text="Catalog Data Wizard", command=self.catalog_data_wizard)
        self.button_catalog.pack(side=TOP, padx=3, pady=3)
        Separator(container, orient='horizontal').pack(fill='x', padx=3, pady=3)
        self.button_create = Button(container, text="Create Parameters", command=self.create_parameters)
        self.button_create.pack(side=TOP, padx=3, pady=3)
        Label(container, text="Run Progress").pack(side=TOP, padx=3, pady=3)
        Progressbar(container, variable=self.var_progress).pack(side=TOP, padx=3, pady=3, fill=X)
        Button(
            container, text="Save Output to File", command=self.save_data_to_file, state="disabled",
        ).pack(
            side=TOP, padx=3, pady=3
        )

    def _build_output(self, container):
        horizontal_scroller = Scrollbar(container, orient='horizontal')
        horizontal_scroller.pack(side=BOTTOM, fill=X)
        # ScrolledText objects can't operate with a Tk.Variable, so just store the widget on the class
        self.output_box = scrolledtext.ScrolledText(
            container, wrap='none', width=40, height=20, xscrollcommand=horizontal_scroller.set
        )
        self.output_box.pack(side=TOP, padx=3, pady=3, fill=BOTH, expand=True)
        self.output_box.insert(END, '\n'.join(["BLAH" * 12] * 40))
        horizontal_scroller.config(command=self.output_box.xview)

    def set_button_status(self):
        if self.selected_equip_type == EquipType.InvalidType:
            self.button_catalog['state'] = DISABLED
            self.button_create['state'] = DISABLED
        else:
            self.button_catalog['state'] = ACTIVE
            if self.catalog_data_in_place:
                self.button_create['state'] = ACTIVE
            else:
                self.button_create['state'] = DISABLED

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
        equip_type = self.equip_ids.check_iid(cur_item)
        if equip_type == EquipType.InvalidType:
            messagebox.showwarning("Type Issue", "Make sure to select one of the child types, not a parent tree node")
            return
        if not self.catalog_data_in_place:
            # then we are just selecting a new equip type, select it and move on
            self.selected_equip_type = equip_type
            self.set_button_status()
            return
        if equip_type == self.selected_equip_type:
            messagebox.showinfo("Type Issue", "This equipment type was already engaged, not making any changes")
            return
        else:
            response = messagebox.askyesno(
                "Type Issue",
                "New type selected, but catalog data ia already present. Would you like to clear the old data?"
            )
            if response:
                self.catalog_data_in_place = False
                self.full_data_set = None
                self.update_status(f"New Equipment Type Selected ({equip_type})")
            self.set_button_status()

    def catalog_data_wizard(self):
        # first open a correction factor definition form window
        cdf = CorrectionFactorForm(self)
        self.wait_window(cdf)
        if cdf.return_data is None:
            return  # correction data form was cancelled, just move on
        correction_factor_summaries = cdf.return_data
        # if that was successful, need to open individual correction entry forms for each factor
        for cf in correction_factor_summaries:
            # TODO: The tables in the GUIs here shouldn't allow manual entry, right?
            # cf_detailed = CorrectionFactorDetailedForm(self) # modal, blah
            # catalog.add_correction_factor(cf)
            self.catalog_data_manager.add_correction_factor(cf)
        # now that we have the full correction factor details, we need to collect the main catalog data
        # main_catalog_data_form = CatalogDataForm(self)  # modal, blah
        self.catalog_data_manager.add_base_data('Foo:Bar')
        self.catalog_data_in_place = True
        self.full_data_set = self.catalog_data_manager.process()
        self.set_button_status()

    def create_parameters(self):
        self.var_progress.set(0)
        thd = Thread(target=self.long_runner, args=(self.catalog_data_manager,))  # timer thread
        thd.daemon = True
        thd.start()

    def update_status(self, extra_message: str = ''):
        status_clause = ''
        if extra_message:
            status_clause = f"  Status Update: {extra_message}"
        if self.catalog_data_in_place:
            self.var_status.set(f"Catalog Data in place, ready to run.{status_clause}")
        else:
            self.var_status.set(f"Catalog Data is NOT READY.{status_clause}")

    def handler_background_thread_update(self, value):
        self.var_progress.set(value)

    def callback_background_thread_update(self, x: int):
        self.gui_queue.put(lambda: self.handler_background_thread_update(x))

    def handler_background_thread_done(self, response: str):
        self.output_box.delete('1.0', END)
        self.output_box.insert(END, response)

    def callback_background_thread_done(self, response: str):
        self.gui_queue.put(lambda: self.handler_background_thread_done(response))

    def long_runner(self, full_catalog_data_manager: CatalogDataManager) -> None:
        total_seconds = 1
        num_iterations = 100
        for x in range(num_iterations):
            self.callback_background_thread_update(x)
            print(x)
            sleep(total_seconds / num_iterations)
        # access stuff on self.calculator
        self.calculator = ParameterCalculator(full_catalog_data_manager)
        self.callback_background_thread_done(self.calculator.output())

    def run(self) -> None:
        """
        Executes the Tk main loop to handle all GUI events and update
        """
        self.mainloop()
