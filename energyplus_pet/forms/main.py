from platform import system
from json import dumps
from pathlib import Path
from queue import Queue
from subprocess import check_call
from sys import executable
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

from pyshortcuts import make_shortcut

from energyplus_pet import NICE_NAME, VERSION
from energyplus_pet.forms.correction_detail_form import DetailedCorrectionFactorForm
from energyplus_pet.data_manager import CatalogDataManager
from energyplus_pet.equipment.base import BaseEquipment
from energyplus_pet.equipment.manager import EquipmentFactory
from energyplus_pet.equipment.equip_types import EquipType, EquipTypeUniqueStrings as ETString
from energyplus_pet.forms.constant_parameters import ConstantParameterEntryForm
from energyplus_pet.forms.correction_summary_form import CorrectionFactorSummaryForm
from energyplus_pet.forms.header_preview import RequiredDataPreviewForm
from energyplus_pet.forms.catalog_plot import CatalogDataPlotForm
from energyplus_pet.forms.comparison_plot import ComparisonPlot
from energyplus_pet.forms.base_data_form import MainDataForm


class EnergyPlusPetWindow(Tk):
    """This form is the primary GUI entry point for the program; all control runs through here"""

    def __init__(self):
        """
        The main window of the parameter estimation tool GUI workflow.
        This window is an instance of a tk.Tk object
        """
        super().__init__()

        # set some basic program information like title and an icon
        self._program_name = NICE_NAME
        program_name_with_version = f"{self._program_name} {VERSION}"
        self.title(program_name_with_version)
        icon_path = Path(__file__).parent / 'favicon.png'
        image = PhotoImage(file=str(icon_path))
        self.iconphoto(True, image)

        # setup event listeners
        self._gui_queue = Queue()
        self._check_queue()

        # define the Tk.Variable instances that will be used to communicate with the GUI widgets
        self._define_tk_variables()

        # build out the form and specify a minimum size, which may not be uniform across platforms
        self._build_gui()
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        # set up some important member variables
        self._equip_instance: BaseEquipment = BaseEquipment()  # sits as a dummy value initially, may not be necessary
        self._catalog_data_manager = CatalogDataManager()
        self._thread_running = False

        # window setup operations
        self._update_status_bar("Program Initialized")
        self._refresh_gui_state()
        self.bind('<Key>', self._handle_button_pressed)

    def _handle_button_pressed(self, event):
        # relevant_modifiers
        # mod_shift = 0x1
        mod_control = 0x4
        # mod_alt = 0x20000
        if event.keysym == 'e' and mod_control & event.state:
            if self._button_engage['state'] != DISABLED:
                self._engage()
        elif event.keysym == 'r' and mod_control & event.state:
            if self._button_preview['state'] != DISABLED:
                self._preview_data()
        elif event.keysym == 't' and mod_control & event.state:
            if self._button_catalog['state'] != DISABLED:
                self._catalog_data_wizard()
        elif event.keysym == 's' and mod_control & event.state:
            if self._button_save_data['state'] != DISABLED:
                self._save_data_to_file()

    def _check_queue(self):
        """Checks the GUI queue for actions and sets a timer to check again each time"""
        while True:
            # noinspection PyBroadException
            try:
                task = self._gui_queue.get(block=False)
                self.after_idle(task)
            except Exception:
                break
        self.after(100, self._check_queue)

    def _define_tk_variables(self):
        """Creates and initializes all the Tk.Variable instances used in the GUI for two-way communication"""
        self._tk_var_progress = IntVar(value=0)
        self._tk_var_status_equip = StringVar(value="Selected Equipment: NONE")
        self._tk_var_status_data = StringVar(value="Catalog Data: NOT READY")
        self._tk_var_status_status = StringVar(value="Program Initialized")

    def _build_gui(self):
        """Builds out the entire window GUI, calling workers as necessary"""
        # now build the top menubar, it's not part of the geometry, but a config parameter on the root Tk object
        self._build_menu()

        # create an instance of the equipment id/tree mapping and then build the tree GUI contents
        label_frame_equip_type = LabelFrame(self, text="Equipment Type")
        self._build_treeview(label_frame_equip_type)
        label_frame_equip_type.grid(row=0, column=0, sticky=NSEW)

        # build the options/controls GUI contents
        label_frame_control = LabelFrame(self, text="Options and Controls")
        self._build_controls(label_frame_control)
        label_frame_control.grid(row=0, column=1, sticky=NSEW)

        # build the output GUI contents
        label_frame_output = LabelFrame(self, text="Parameter Output")
        self._build_output(label_frame_output)
        label_frame_output.grid(row=0, column=2, sticky=NSEW)

        # build the status bar
        status_frame = Frame(self)
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self._tk_var_status_equip).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self._tk_var_status_data).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self._tk_var_status_status).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        status_frame.grid(row=1, column=0, columnspan=3, sticky=EW)

        # set up the weight of each row (even) and column (distributed) for a nice looking GUI
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=8)

    def _build_menu(self):
        """Builds out the menubar at the top of thw window"""
        menubar = Menu(self)
        menu_help = Menu(menubar, tearoff=0)
        menu_help.add_command(label="Open online documentation...", command=self._help_documentation)
        menu_help.add_command(label="Open examples folder...", command=self._open_examples)
        menu_help.add_command(label="Create desktop icon", command=self._create_shortcut)
        menu_help.add_command(label="About...", command=self._help_about)
        menubar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=menubar)

    def _build_treeview(self, container):
        """Builds out the equipment treeview on the left side of the window"""
        tree_holder = Frame(container)
        equip_type_scrollbar = Scrollbar(tree_holder)
        # I don't believe the Treeview object can interact with a Tk.Variable, so the tree is stored on the class
        self._tree = Treeview(tree_holder, columns=('Type',), show='tree', yscrollcommand=equip_type_scrollbar.set)
        self._tree.column('#0', stretch=False)
        equip_type_scrollbar.config(command=self._tree.yview)
        # eventually use a defined dictionary somewhere for the tree items and keywords
        root_hp = self._tree.insert(parent='', index='end', text="Heat Pump Coils", open=True)
        branch_wah = self._tree.insert(parent=root_hp, index='end', text="Water to Air Heating Coil", open=True)
        self.init = self._tree.insert(
            parent=branch_wah, index='end', text="Curve Fit", tags=ETString.WAHP_Heating_CurveFit
        )
        # self._tree.insert(parent=branch_wah, index='end', text="Parameter Estimation", tags=ETString.WAHP_Heating_PE)
        branch_wac = self._tree.insert(parent=root_hp, index='end', text="Water to Air Cooling Coil", open=True)
        self._tree.insert(parent=branch_wac, index='end', text="Curve Fit", tags=ETString.WAHP_Cooling_CurveFit)
        # self._tree.insert(parent=branch_wac, index='end', text="Parameter Estimation", tags=ETString.WAHP_Cooling_PE)
        branch_wwh = self._tree.insert(parent=root_hp, index='end', text="Water to Water Heating", open=True)
        self._tree.insert(parent=branch_wwh, index='end', text="Curve Fit", tags=ETString.WWHP_Heating_CurveFit)
        branch_wwc = self._tree.insert(parent=root_hp, index='end', text="Water to Water Cooling", open=True)
        self._tree.insert(parent=branch_wwc, index='end', text="Curve Fit", tags=ETString.WWHP_Cooling_CurveFit)
        # root_pumps = self._tree.insert(parent='', index='end', text='Pumps', open=True)
        # branch_con_pump = self._tree.insert(parent=root_pumps, index='end', text="Constant Speed Pump", open=True)
        # self._tree.insert(
        #     parent=branch_con_pump, index='end', text='Non-Dimensional', tags=ETString.Pump_ConstSpeed_ND
        # )
        self._tree.pack(side=LEFT, padx=3, pady=3, fill=BOTH, expand=True)
        equip_type_scrollbar.pack(side=RIGHT, padx=0, pady=3, fill=Y, expand=False)
        self._tree.focus(self.init)
        self._tree.selection_set(self.init)
        tree_holder.pack(side=TOP, fill=BOTH, expand=True)

    def _build_controls(self, container):
        """Builds out the control section in the middle of the window"""
        Label(
            container, text="Select an equipment type in the tree\nand press Ctrl-e or click here:"
        ).pack(side=TOP, padx=3, pady=3)
        self._button_engage = Button(container, text='Engage Equipment Type', command=self._engage)
        self._button_engage.pack(side=TOP, padx=3, pady=3, fill=X)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        Label(
            container, text="To view the required data for the selected\nequipment, press Ctrl-r or click here:"
        ).pack(side=TOP, padx=3, pady=3)
        self._button_preview = Button(container, text="Required Data Description", command=self._preview_data)
        self._button_preview.pack(side=TOP, padx=3, pady=3, fill=X)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        Label(
            container, text="Finally, to enter data and process parameters\n press Ctrl-t or click here..."
        ).pack(side=TOP, padx=3, pady=3)
        self._button_catalog = Button(container, text="Catalog Data Wizard", command=self._catalog_data_wizard)
        self._button_catalog.pack(side=TOP, padx=3, pady=3, fill=X)
        Label(container, text="...and watch the progress here:").pack(side=TOP, padx=3, pady=3)
        self._progress = Progressbar(container, variable=self._tk_var_progress)
        self._progress.pack(side=TOP, padx=3, pady=3, fill=X)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        Label(container, text="Once complete, use Ctrl-s to save data:").pack(side=TOP, padx=3, pady=3)
        self._button_save_data = Button(
            container, text="Save Output to File", command=self._save_data_to_file, state=DISABLED,
        )
        self._button_save_data.pack(side=TOP, fill=X, padx=3, pady=3)
        Separator(container, orient='horizontal').pack(fill=X, padx=3, pady=3)
        Label(container, text="Then if you want to run another, just reinitialize here:").pack(
            side=TOP, padx=3, pady=3)
        Button(container, text="Reinitialize Form", command=self._reinitialize).pack(side=TOP, fill=X, padx=3, pady=3)

    @staticmethod
    def _build_one_output_frame(notebook_container: Notebook, tab_title: str):
        """Builds out a single output frame to be in the output notebook"""
        output_frame_par = Frame(notebook_container)
        output_frame_par.pack(side=TOP, expand=True, fill=BOTH)
        horizontal_scroller_par = Scrollbar(output_frame_par, orient='horizontal')
        horizontal_scroller_par.pack(side=BOTTOM, fill=X)
        this_output_box = scrolledtext.ScrolledText(
            output_frame_par, wrap='none', width=40, height=20, xscrollcommand=horizontal_scroller_par.set
        )
        this_output_box.pack(side=TOP, padx=3, pady=3, fill=BOTH, expand=True)
        this_output_box.insert(END, 'Messages and results will appear here')
        horizontal_scroller_par.config(command=this_output_box.xview)
        notebook_container.add(output_frame_par, text=tab_title)
        return this_output_box

    def _build_output(self, container):
        """Builds out the full output notebook on the right side of the window, calling workers as needed"""
        output_notebook = Notebook(container)
        self._output_box_par = self._build_one_output_frame(output_notebook, "Parameter Summary")
        self._output_box_idf = self._build_one_output_frame(output_notebook, "IDF Object")
        self._output_box_json = self._build_one_output_frame(output_notebook, "EpJSON Object")
        output_notebook.pack(expand=True, fill=BOTH)

    def _refresh_gui_state(self):
        """Checks current instance flags and sets button states appropriately"""
        if self._thread_running:
            self._button_engage['state'] = DISABLED
            self._button_catalog['state'] = DISABLED
            self._button_preview['state'] = DISABLED
            self._button_save_data['state'] = ACTIVE
        elif self._equip_instance is None or self._equip_instance.this_type() == EquipType.InvalidType:
            self._button_engage['state'] = ACTIVE
            self._button_catalog['state'] = DISABLED
            self._button_preview['state'] = DISABLED
            self._button_save_data['state'] = DISABLED
        else:
            self._button_engage['state'] = ACTIVE
            self._button_catalog['state'] = ACTIVE
            self._button_preview['state'] = ACTIVE
            if self._catalog_data_manager.data_processed:
                self._button_save_data['state'] = ACTIVE
            else:
                self._button_save_data['state'] = DISABLED

    def _help_documentation(self):
        """Launches a browser to open the stable documentation"""
        # could try to use the current version docs but that may be a bit finicky
        browser_open('https://energypluspet.readthedocs.io/en/stable/')
        self._update_status_bar('Launched online documentation')

    def _create_shortcut(self):
        runner_script = str(Path(__file__).resolve().parent.parent / 'runner.py')
        icon_extension = 'ico' if system() == 'Windows' else 'png'
        icon_path = str(Path(__file__).resolve().parent / f"favicon.{icon_extension}")
        make_shortcut(
            runner_script, name=self._program_name, terminal=False, icon=icon_path,
            executable=executable, startmenu=False
        )

    @staticmethod
    def _open_examples():
        examples_dir = str(Path(__file__).resolve().parent.parent / 'examples')
        if system() == 'Darwin':
            check_call(["open", examples_dir])
        elif system() == 'Linux':
            check_call(["xdg-open", examples_dir])
        elif system() == 'Windows':
            from os import startfile
            startfile(examples_dir)

    def _preview_data(self):
        """Allows the user to preview the data for the selected equipment, button is disabled until an equip is set."""
        preview = RequiredDataPreviewForm(self, self._equip_instance)
        self.wait_window(preview)

    def _help_about(self):
        """Simple about window showing program information"""
        messagebox.showinfo(
            f"About {self._program_name}",
            "The original idea for this tool was developed in 2009ish by Edwin Lee and implemented in a VB.Net tool.\n"
            "This new version is developed in Python to allow for easy cross platform development and packaging."
        )

    def _save_data_to_file(self):
        """Saves catalog data to a file"""
        file_path = filedialog.asksaveasfilename(
            parent=self, filetypes=(('JSON File', '.json'),), confirmoverwrite=True
        )
        if file_path is None or file_path == ():
            return
        try:
            with open(file_path, 'w') as f:
                response_object = {
                    'catalog_inputs': self._catalog_data_manager.summary(),
                    'parameter_summary': self._output_box_par.get('1.0', END),
                    'idf_object': self._output_box_idf.get('1.0', END),
                    'epjson_object': self._output_box_json.get('1.0', END),
                }
                f.write(dumps(response_object, indent=2))
        except Exception as e:  # noqa  any file issue could happen
            messagebox.showerror(self._program_name, "Could not save data to file")

    def _reinitialize(self):
        self._update_all_output_boxes('Messages and results will appear here')
        self._equip_instance = None
        self._catalog_data_manager.reset()
        self._tk_var_progress.set(0)
        self._tree.focus(self.init)
        self._tree.selection_set(self.init)
        self._refresh_gui_state()

    def _engage(self) -> None:
        """
        Checks the currently selected object in the equipment tree, and if valid, assigns the
        self.selected_equip_instance member variable to a proper equipment instance.
        GUI state is refreshed if anything changed

        :return: Nothing
        """
        cur_item = self._tree.focus()
        node_tags = self._tree.item(cur_item, 'tags')  # this always either returns '' or ('tag_contents',)
        if node_tags == '':
            messagebox.showwarning("Type Issue", "Make sure to select one of the child types, not a parent tree node")
            return
        node_tag = node_tags[0]
        potential_new_equip_type = ETString.get_equip_type_from_unique_string(node_tag)
        if not self._catalog_data_manager.data_processed:
            # then we are just selecting a new equip type, select it and move on
            potential_equip = EquipmentFactory.instance_factory(potential_new_equip_type)
            if potential_equip is None:
                messagebox.showwarning("Not Implemented Yet", "This type has not been implemented yet, sorry!")
                return
            self._equip_instance = potential_equip
            self._catalog_data_manager.reset()
            self._tk_var_progress.set(0)
            self._update_status_bar("New Equipment Type Selected")
            self._refresh_gui_state()
            return
        if potential_new_equip_type == self._equip_instance.this_type():
            messagebox.showinfo("Type Issue", "This equipment type was already engaged, not making any changes")
            return
        else:
            response = messagebox.askyesno(
                "Type Issue",
                "New type selected, but catalog data is already present. Would you like to clear the old data?"
            )
            if response:
                self._catalog_data_manager.reset()
                self._update_status_bar("New Equipment Type Selected")
            self._refresh_gui_state()

    def _catalog_data_wizard(self):
        """
        Manages the data entry processes.  Calls child functions to display forms, handles different exits, etc.
        This function assumes the self.selected_equip_instance has already been set to a proper instance in the engage
        function.

        :return: Nothing
        """
        self._update_status_bar('Started catalog wizard')
        self._update_all_output_boxes('Catalog wizard starting')

        self._tk_var_progress.set(0)
        self._progress['maximum'] = self._equip_instance.get_number_of_progress_steps() + 9  # 9 steps in here
        self._handler_thread_increment()

        # first open a correction factor definition form window, if this returns False, it means abort
        cdf = CorrectionFactorSummaryForm(self, self._equip_instance)
        self.wait_window(cdf)
        if cdf.exit_code == CorrectionFactorSummaryForm.ExitCode.Cancel:
            # in the original code, this would set CorrectionsExist to false, not sure that's right
            self._update_status_bar('Correction factor form cancelled')
            self._update_all_output_boxes('Correction factor form cancelled; reopen wizard to try again')
            self._tk_var_progress.set(0)
            return  # correction data form was cancelled, just abort
        elif cdf.exit_code == CorrectionFactorSummaryForm.ExitCode.Error:
            self._update_status_bar('Correction factor form error!')
            self._update_all_output_boxes('Correction factor form encountered an error; reopen wizard to try again')
            self._tk_var_progress.set(0)
            return  # may need to report the error
        else:
            self._update_status_bar('Correction factor summary complete')
        self._handler_thread_increment()

        # if that was successful, loop over each local summary and open individual correction entry forms for each
        for cf_num, cf in enumerate(cdf.factor_summaries):
            cfd_form = DetailedCorrectionFactorForm(
                self, cf, self._equip_instance, cf_num + 1, len(cdf.factor_summaries)
            )
            self.wait_window(cfd_form)
            if cfd_form.exit_code == DetailedCorrectionFactorForm.DetailedCorrectionExitCode.Cancel:
                self._update_status_bar('Correction factor form cancelled')
                self._update_all_output_boxes('Correction factor form cancelled; reopen wizard to try again')
                self._tk_var_progress.set(0)
                return
            self._catalog_data_manager.add_correction_factor(cfd_form.completed_factor)
        self._update_status_bar('Correction factor details complete')
        self._handler_thread_increment()

        # now that we have the full correction factor details, we need to collect the main catalog data
        main_catalog_data_form = MainDataForm(self, self._equip_instance)
        self.wait_window(main_catalog_data_form)
        if main_catalog_data_form.exit_code == MainDataForm.MainDataExitCode.Cancel:
            self._update_status_bar('Main catalog data form cancelled')
            self._update_all_output_boxes('Main catalog data form cancelled; reopen wizard to try again')
            self._tk_var_progress.set(0)
            return
        self._catalog_data_manager.add_base_data(main_catalog_data_form.final_base_data_rows)
        self._handler_thread_increment()

        # then process the base data and correction factors into a full data set
        response_status = self._catalog_data_manager.apply_correction_factors(
            self._equip_instance.minimum_data_points_for_generation(),
            self._equip_instance.headers().get_db_column(),
            self._equip_instance.headers().get_wb_column()
        )
        if response_status == CatalogDataManager.ProcessResult.ERROR:
            self._update_status_bar('Error processing catalog data')
            self._update_all_output_boxes(
                f"Error processing data! Message: \n\n{self._catalog_data_manager.last_error_message}"
            )
            self._tk_var_progress.set(0)
            return
        self._handler_thread_increment()

        # if this equipment requires constant/rated parameters, get them now
        if len(self._equip_instance.get_required_constant_parameters()) > 0:
            cde = ConstantParameterEntryForm(self, self._equip_instance)
            self.wait_window(cde)
            if cde.form_cancelled:
                self._update_status_bar('Constant parameter data form cancelled')
                self._update_all_output_boxes('Constant parameter data form cancelled; reopen wizard to try again')
                self._tk_var_progress.set(0)
                return
            for k, v in cde.parameter_value_map.items():
                self._equip_instance.set_required_constant_parameter(k, v)
        self._handler_thread_increment()

        # and actually, if the data doesn't have diversity, we should accept it, but not allow creating parameters
        # the user should be able to reopen the wizard and add more data to variables or whatever
        # then display the catalog data plot form for inspection
        cdf = CatalogDataPlotForm(self, self._catalog_data_manager, self._equip_instance)
        cdf.wait_window()
        if cdf.exit_code == CatalogDataPlotForm.ExitCode.CANCEL:
            self._update_status_bar('Catalog data plot form cancelled')
            self._update_all_output_boxes('Catalog data plot form cancelled; reopen wizard to try again')
            self._tk_var_progress.set(0)
            return
        self._handler_thread_increment()

        # catalog data is now ready
        self._update_status_bar('Processed Catalog Data')
        self._update_all_output_boxes('Catalog data plot form cancelled; reopen wizard to try again')
        self._handler_thread_increment()

        # the parameter generation process could be lengthy, so we put it in a background thread
        self._update_status_bar('Starting parameter generation process')
        self._thread_running = True
        self._refresh_gui_state()
        thd = Thread(target=self._worker_generate_params, args=(self._equip_instance, self._catalog_data_manager))
        thd.daemon = True
        thd.start()
        self._handler_thread_increment()

    def _worker_generate_params(self, equip_instance: BaseEquipment, data: CatalogDataManager) -> None:
        """
        Function that will be in a background thread, calls the equipment to generate parameters.
        Equipment instance passed in will be mutated so that when the main thread accesses it, it will be updated.

        :param equip_instance: An equipment instance constructed by the main form
        :param data: A fully populated catalog data manager, with final data ready for the equipment to process
        :return: Nothing
        """
        try:
            equip_instance.generate_parameters(data, self._callback_thread_increment, self._callback_thread_done)
        except Exception as e:  # any type of exception
            self._callback_thread_done(False, "Error occurred! " + str(e))
            return

    def _update_status_bar(self, extra_message: str) -> None:
        """
        Updates the status bar at the bottom of the window, providing data based on flags and displaying the message

        :param extra_message: String message to show on the right side of the status bar
        :return: Nothing
        """
        if self._equip_instance is None:
            self._tk_var_status_equip.set("Selected Equipment: NONE")
        else:
            self._tk_var_status_equip.set(f"Selected Equipment: {self._equip_instance.short_name()}")
        if not self._catalog_data_manager.data_processed:
            self._tk_var_status_data.set("Catalog data: NOT READY")
        else:
            self._tk_var_status_data.set("Catalog Data: READY")
        self._tk_var_status_status.set(extra_message)

    def _handler_thread_increment(self) -> None:
        """Main thread handler for a progress increment step"""
        self._tk_var_progress.set(self._tk_var_progress.get() + 1)

    def _callback_thread_increment(self) -> None:
        """Background thread callback function for inserting a progress increment step in the GUI queue"""
        self._gui_queue.put(self._handler_thread_increment)

    def _update_par_box(self, content: str) -> None:
        """
        Minimal worker function to update the data in the parameter summary output box

        :param content: String data to display in the output box
        :return: Nothing
        """
        self._output_box_par.delete('1.0', END)
        self._output_box_par.insert(END, content)

    def _update_idf_box(self, content: str) -> None:
        """
        Minimal worker function to update the data in the IDF Object output box

        :param content: String data to display in the output box
        :return: Nothing
        """
        self._output_box_idf.delete('1.0', END)
        self._output_box_idf.insert(END, content)

    def _update_json_box(self, content: str) -> None:
        """
        Minimal worker function to update the data in the EpJSON output box

        :param content: String data to display in the output box
        :return: Nothing
        """
        self._output_box_json.delete('1.0', END)
        self._output_box_json.insert(END, content)

    def _update_all_output_boxes(self, content: str) -> None:
        """
        Minimal worker function to update the data in all output boxes at once

        :param content: String data to display in the output boxes
        :return: Nothing
        """
        self._update_par_box(content)
        self._update_idf_box(content)
        self._update_json_box(content)

    def _handler_thread_done(self, success: bool, err_message: str = '') -> None:
        """
        Main thread handler for the background thread being completed

        :param success: Boolean flag for whether the process was a success or not
        :param err_message: Optional error message in case something went wrong
        :return: Nothing
        """
        self._thread_running = False
        self._refresh_gui_state()
        self._update_status_bar('Finished Parameter Generation')
        if success:
            self._update_par_box(self._equip_instance.to_parameter_summary())
            self._update_idf_box(self._equip_instance.to_eplus_idf_object())
            self._update_json_box(self._equip_instance.to_eplus_epjson_object())
            self.wait_window(ComparisonPlot(self, self._catalog_data_manager, self._equip_instance))
            self._tk_var_progress.set(100)
        else:
            self._update_all_output_boxes(err_message)

    def _callback_thread_done(self, success: bool, err_message: str = '') -> None:
        """Background thread callback function for inserting a progress done step in the GUI queue"""
        self._gui_queue.put(lambda: self._handler_thread_done(success, err_message))

    def run(self) -> None:
        """Executes the Tk main loop to handle all GUI events and update"""
        self.mainloop()
