from pathlib import Path
from queue import Queue
from threading import Thread
from tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y  # widget sides and directions to use in widget.pack commands
from tkinter import END  # key used when adding data to the scrolledText object
from tkinter import IntVar, StringVar  # GUI variables
from tkinter import NSEW, EW, S  # sticky cardinal directions to use in widget grid commands
from tkinter import SUNKEN, DISABLED, ACTIVE  # attributes used to modify widget appearance
from tkinter import Tk, Button, Frame, Label, PhotoImage, scrolledtext, Scrollbar, Menu  # widgets
from tkinter import messagebox, filedialog  # simple dialogs for user messages
from tkinter.ttk import LabelFrame, Progressbar, Treeview, Separator, Notebook  # ttk widgets
from webbrowser import open as browser_open

from energyplus_pet import NICE_NAME, VERSION
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.manager import EquipmentFactory
from energyplus_pet.equipment.equip_types import EquipType, EquipTypeUniqueStrings as ETString
from energyplus_pet.forms.correction_summary_form import CorrectionFactorSummaryForm
from energyplus_pet.forms.header_preview import RequiredDataPreviewForm
from energyplus_pet.forms.catalog_plot import CatalogDataPlotForm
from energyplus_pet.forms.comparison_plot import ComparisonPlot


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
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        # set up some important member variables
        self.full_data_set = None
        self.selected_equip_instance: BaseEquipment = BaseEquipment()  # nothing for now
        self.catalog_data_manager = CatalogDataManager()
        self.thread_running = False

        # window setup operations
        self.update_status_bar("Program Initialized")
        self._refresh_gui_state()

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
        self.var_progress = IntVar(value=0)
        self.var_status_equip = StringVar(value="Selected Equipment: NONE")
        self.var_status_data = StringVar(value="Catalog Data: NOT READY")
        self.var_status_status = StringVar(value="Program Initialized")

    def _build_gui(self):

        # now build the top menubar, it's not part of the geometry, but a config parameter on the root Tk object
        self._build_menu()

        # create an instance of the equipment id/tree mapping and then build the tree GUI contents
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
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self.var_status_equip).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self.var_status_data).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self.var_status_status).pack(
            side=LEFT, fill=BOTH, expand=True
        )

        # pack the parent objects on the GUI
        label_frame_equip_type.grid(row=0, column=0, sticky=NSEW)
        label_frame_control.grid(row=0, column=1, sticky=NSEW)
        label_frame_output.grid(row=0, column=2, sticky=NSEW)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=EW)

        # set up the weight of each row (even) and column (distributed) for a nice looking GUI
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=8)

    def _build_menu(self):
        menubar = Menu(self)
        menu_help = Menu(menubar, tearoff=0)
        menu_help.add_command(label="Open online documentation...", command=self._help_documentation)
        menu_help.add_command(label="About...", command=self._help_about)
        menubar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=menubar)

    def _build_treeview(self, container):
        tree_holder = Frame(container)
        equip_type_scrollbar = Scrollbar(tree_holder)
        # I don't believe the Treeview object can interact with a Tk.Variable, so the tree is stored on the class
        self.tree = Treeview(tree_holder, columns=('Type',), show='tree', yscrollcommand=equip_type_scrollbar.set)
        self.tree.column('#0', stretch=False)
        equip_type_scrollbar.config(command=self.tree.yview)
        # eventually use a defined dictionary somewhere for the tree items and keywords
        root_hp = self.tree.insert(parent='', index='end', text="Heat Pumps", open=True)
        branch_wah = self.tree.insert(parent=root_hp, index='end', text="Water to Air Heating", open=True)
        init = self.tree.insert(parent=branch_wah, index='end', text="Curve Fit", tags=ETString.WAHP_Heating_CurveFit)
        self.tree.insert(parent=branch_wah, index='end', text="Parameter Estimation", tags=ETString.WAHP_Heating_PE)
        branch_wac = self.tree.insert(parent=root_hp, index='end', text="Water to Air Cooling", open=True)
        self.tree.insert(parent=branch_wac, index='end', text="Curve Fit", tags=ETString.WAHP_Cooling_CurveFit)
        self.tree.insert(parent=branch_wac, index='end', text="Parameter Estimation", tags=ETString.WAHP_Cooling_PE)
        branch_wwh = self.tree.insert(parent=root_hp, index='end', text="Water to Water Heating", open=True)
        self.tree.insert(parent=branch_wwh, index='end', text="Curve Fit", tags=ETString.WWHP_Heating_CurveFit)
        branch_wwc = self.tree.insert(parent=root_hp, index='end', text="Water to Water Cooling", open=True)
        self.tree.insert(parent=branch_wwc, index='end', text="Curve Fit", tags=ETString.WWHP_Cooling_CurveFit)
        root_pumps = self.tree.insert(parent='', index='end', text='Pumps', open=True)
        branch_cons_pump = self.tree.insert(parent=root_pumps, index='end', text="Constant Speed Pump", open=True)
        self.tree.insert(parent=branch_cons_pump, index='end', text='Non-Dimensional', tags=ETString.Pump_ConstSpeed_ND)
        # COMPONENT_EXTENSION 08: Add more nodes to the treeview based on the type added
        self.tree.pack(side=LEFT, padx=3, pady=3, fill=BOTH, expand=True)
        equip_type_scrollbar.pack(side=RIGHT, padx=0, pady=3, fill=Y, expand=False)
        self.tree.focus(init)
        self.tree.selection_set(init)
        tree_holder.pack(side=TOP, fill=BOTH, expand=True)
        self.button_engage = Button(container, text='Engage Equipment Type', command=self._engage)
        self.button_engage.pack(side=TOP, padx=3, pady=3, fill=X)

    def _build_controls(self, container):
        self.button_preview = Button(container, text="Required Data Description", command=self._preview_data)
        self.button_preview.pack(side=TOP, padx=3, pady=3, fill=X)
        self.button_catalog = Button(container, text="Catalog Data Wizard", command=self._catalog_data_wizard)
        self.button_catalog.pack(side=TOP, padx=3, pady=3, fill=X)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        self.button_create = Button(container, text="Create Parameters", command=self.start_parameter_thread)
        self.button_create.pack(side=TOP, padx=3, pady=3)
        Label(container, text="Run Progress").pack(side=TOP, padx=3, pady=3)
        self.progress = Progressbar(container, variable=self.var_progress)
        self.progress.pack(side=TOP, padx=3, pady=3, fill=X)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        self.button_save_data = Button(
            container, text="Save Output to File", command=self._save_data_to_file, state="disabled",
        )
        self.button_save_data.pack(side=TOP, padx=3, pady=3)

    @staticmethod
    def _build_one_output_frame(notebook_container: Notebook, tab_title: str):
        output_frame_par = Frame(notebook_container)
        output_frame_par.pack(side=TOP, expand=True, fill=BOTH)
        horizontal_scroller_par = Scrollbar(output_frame_par, orient='horizontal')
        horizontal_scroller_par.pack(side=BOTTOM, fill=X)
        # ScrolledText objects can't operate with a Tk.Variable, so just store the widget on the class
        this_output_box = scrolledtext.ScrolledText(
            output_frame_par, wrap='none', width=40, height=20, xscrollcommand=horizontal_scroller_par.set
        )
        this_output_box.pack(side=TOP, padx=3, pady=3, fill=BOTH, expand=True)
        this_output_box.insert(END, '\n'.join(["BLAH" * 12] * 40))
        horizontal_scroller_par.config(command=this_output_box.xview)
        notebook_container.add(output_frame_par, text=tab_title)
        return this_output_box

    def _build_output(self, container):
        output_notebook = Notebook(container)
        self.output_box_par = self._build_one_output_frame(output_notebook, "Parameter Summary")
        self.output_box_idf = self._build_one_output_frame(output_notebook, "IDF Object")
        self.output_box_json = self._build_one_output_frame(output_notebook, "EpJSON Object")
        output_notebook.pack(expand=True, fill=BOTH)

    def _refresh_gui_state(self):
        if self.thread_running:
            self.button_engage['state'] = DISABLED
            self.button_catalog['state'] = DISABLED
            self.button_create['state'] = DISABLED
            self.button_preview['state'] = DISABLED
            self.button_save_data['state'] = ACTIVE
        elif self.selected_equip_instance is None or self.selected_equip_instance.this_type() == EquipType.InvalidType:
            self.button_engage['state'] = ACTIVE
            self.button_catalog['state'] = DISABLED
            self.button_create['state'] = DISABLED
            self.button_preview['state'] = DISABLED
            self.button_save_data['state'] = DISABLED
        else:
            self.button_engage['state'] = ACTIVE
            self.button_catalog['state'] = ACTIVE
            self.button_preview['state'] = ACTIVE
            if self.catalog_data_manager.data_processed:
                self.button_create['state'] = ACTIVE
                self.button_save_data['state'] = ACTIVE
            else:
                self.button_create['state'] = DISABLED
                self.button_save_data['state'] = DISABLED

    def _help_documentation(self):
        browser_open('https://energypluspet.readthedocs.io/en/latest/')
        self.update_status_bar('Launched online documentation')

    def _preview_data(self):
        preview = RequiredDataPreviewForm(self, self.selected_equip_instance)
        self.wait_window(preview)

    def _help_about(self):
        messagebox.showinfo(
            f"About {self.program_name}",
            "The original idea for this tool was developed in 2009ish by Edwin Lee and implemented in a VB.Net tool.\n"
            "This new version is developed in Python to allow for easy cross platform development and packaging."
        )

    def _save_data_to_file(self):
        file_path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", confirmoverwrite=True)
        if file_path is None or file_path == ():
            return
        try:
            with open(file_path, 'w') as f:
                f.write('hello,world')
        except Exception as e:  # noqa  any file issue could happen
            messagebox.showerror(self.program_name, "Could not save data to file")

    def _engage(self) -> None:
        """
        Checks the currently selected object in the equipment tree, and if valid, assigns the
        self.selected_equip_instance member variable to a proper equipment instance.

        :return: Nothing
        """
        cur_item = self.tree.focus()
        node_tags = self.tree.item(cur_item, 'tags')  # this always either returns '' or ('tag_contents',)
        if node_tags == '':
            messagebox.showwarning("Type Issue", "Make sure to select one of the child types, not a parent tree node")
            return
        node_tag = node_tags[0]
        potential_new_equip_type = ETString.get_equip_type_from_unique_string(node_tag)
        if not self.catalog_data_manager.data_processed:
            # then we are just selecting a new equip type, select it and move on
            self.selected_equip_instance = EquipmentFactory.factory(potential_new_equip_type)
            if self.selected_equip_instance is None:
                messagebox.showwarning("Not Implemented Yet", "This type has not been implemented yet, sorry!")
                return
            self.update_status_bar("New Equipment Type Selected")
            self._refresh_gui_state()
            return
        if potential_new_equip_type == self.selected_equip_instance.this_type():
            messagebox.showinfo("Type Issue", "This equipment type was already engaged, not making any changes")
            return
        else:
            response = messagebox.askyesno(
                "Type Issue",
                "New type selected, but catalog data is already present. Would you like to clear the old data?"
            )
            if response:
                self.catalog_data_manager.reset()
                self.full_data_set = None
                self.update_status_bar("New Equipment Type Selected")
            self._refresh_gui_state()

    def _catalog_data_wizard(self):
        """
        Manages the data entry processes.  Calls child functions to display forms, handles different exits, etc.
        This function assumes the self.selected_equip_instance has already been set to a proper instance in the engage
        function.
        :return:
        """
        # first open a correction factor definition form window, if this returns False, it means abort
        if not self.get_correction_factor_summaries():
            return
        # if that was successful, need to open individual correction entry forms for each factor
        for cf in self.catalog_data_manager.cf_summaries:
            print(cf.description())
            # TODO: Need to create a new form, modal, and check the response; if cancel then abort
            # Do we need to reset the catalog data at all?
            # TODO: The tables in the GUIs here shouldn't allow manual entry, right?
            # cf_detailed = CorrectionFactorDetailedForm(self) # modal, blah
            # catalog.add_correction_factor(cf)
            # self.catalog_data_manager.add_correction_factor(cf)
        # now that we have the full correction factor details, we need to collect the main catalog data
        # main_catalog_data_form = CatalogDataForm(self)  # modal, blah
        self.catalog_data_manager.add_base_data('Foo:Bar')
        # then process the base data and correction factors into a full data set
        self.catalog_data_manager.process()  # should return a meaningful response, not text
        # and actually, if the data doesn't have diversity, we should accept it, but not allow creating parameters
        # the user should be able to reopen the wizard and add more data to variables or whatever
        # then display the catalog data plot form for inspection
        cdf = CatalogDataPlotForm(self, self.catalog_data_manager)
        cdf.wait_window()
        self._refresh_gui_state()
        self.update_status_bar('Processed Catalog Data')

    def get_correction_factor_summaries(self) -> bool:
        cdf = CorrectionFactorSummaryForm(self, self.selected_equip_instance)
        self.wait_window(cdf)
        if cdf.exit_code == CorrectionFactorSummaryForm.ExitCode.Cancel:
            # in the original code, this would set CorrectionsExist to false, not sure that's right
            return False  # correction data form was cancelled, just move on
        elif cdf.exit_code == CorrectionFactorSummaryForm.ExitCode.Error:
            return False  # if an error occurred, it should have been reported, just abort the data process
        else:
            return True  # done/skip indicates the data manager has now gotten any/all updated correction summaries

    def start_parameter_thread(self):
        self.var_progress.set(0)
        # set buttons to disabled while it runs
        self.thread_running = True
        self._refresh_gui_state()
        self.update_status_bar('Starting parameter generation process')
        thd = Thread(target=self.generate_parameters, args=(self.selected_equip_instance, self.catalog_data_manager))
        thd.daemon = True
        thd.start()

    def update_status_bar(self, extra_message: str):
        if self.selected_equip_instance is None:
            self.var_status_equip.set("Selected Equipment: NONE")
        else:
            self.var_status_equip.set(f"Selected Equipment: {self.selected_equip_instance.name()}")
        if not self.catalog_data_manager.data_processed:
            self.var_status_data.set("Catalog data: NOT READY")
        else:
            self.var_status_data.set("Catalog Data: READY")
        self.var_status_status.set(extra_message)

    def handler_background_thread_increment(self):
        self.var_progress.set(self.var_progress.get() + 1)

    def callback_background_thread_increment(self):
        self.gui_queue.put(self.handler_background_thread_increment)

    def handler_background_thread_starting(self, initial_progress_value: int):
        self.progress['maximum'] = initial_progress_value

    def callback_background_thread_starting(self, initial_progress_value: int):
        self.gui_queue.put(lambda: self.handler_background_thread_starting(initial_progress_value))

    def handler_background_thread_done(self, success: bool, err_message: str = ''):
        self.thread_running = False
        self._refresh_gui_state()
        self.update_status_bar('Finished Parameter Generation')
        self.output_box_par.delete('1.0', END)
        self.output_box_idf.delete('1.0', END)
        self.output_box_json.delete('1.0', END)
        if not success:
            self.output_box_par.insert(END, err_message)
            self.output_box_idf.insert(END, err_message)
            self.output_box_json.insert(END, err_message)
            return
        self.output_box_par.insert(END, self.selected_equip_instance.to_parameter_summary())
        self.output_box_idf.insert(END, self.selected_equip_instance.to_eplus_idf_object())
        self.output_box_json.insert(END, self.selected_equip_instance.to_eplus_epjson_object())
        ComparisonPlot(
            self, self.catalog_data_manager, self.selected_equip_instance, ComparisonPlot.PlotType.RawComparison
        )
        ComparisonPlot(
            self, self.catalog_data_manager, self.selected_equip_instance, ComparisonPlot.PlotType.PercentError
        )

    def callback_background_thread_done(self, success: bool, err_message: str = ''):
        self.gui_queue.put(lambda: self.handler_background_thread_done(success, err_message))

    def generate_parameters(self, equip_instance: BaseEquipment, data: CatalogDataManager) -> None:
        # the self.selected_equip_instance should be mutated, right?  So that we don't have to pass it back upward?
        try:
            equip_instance.generate_parameters(
                data, self.callback_background_thread_starting,
                self.callback_background_thread_increment, self.callback_background_thread_done
            )
        except Exception as e:  # any type of exception
            self.callback_background_thread_done(False, "Error occurred! " + str(e))
            return

    def run(self) -> None:
        """
        Executes the Tk main loop to handle all GUI events and update
        """
        self.mainloop()
