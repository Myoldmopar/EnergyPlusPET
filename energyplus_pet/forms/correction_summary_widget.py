from tkinter import Button, Frame, Label, LabelFrame, TOP, Spinbox, IntVar, Scrollbar, LEFT, BOTH, RIGHT, EW, \
    VERTICAL, Radiobutton, StringVar, W, NS, OptionMenu, MULTIPLE, Listbox, Variable, BooleanVar, \
    ACTIVE, DISABLED, HORIZONTAL, TclError
from tkinter.ttk import Separator
from typing import Callable

from energyplus_pet.correction_factor import CorrectionFactor, CorrectionFactorType
from energyplus_pet.equipment.base import BaseEquipment


class CorrectionSummaryWidget(LabelFrame):
    """
    This widget returns a Tk.LabelFrame that displays a correction factor summary and is shown on the summary form.
    """

    def __init__(self, parent: Frame, name: str, equipment_instance: BaseEquipment, remove_callback: Callable):
        super().__init__(parent, name=name, text=name)
        self.cf = CorrectionFactor(name)
        self.equip_instance = equipment_instance

        # these are Tk variables for tracking dynamic changes and tracing
        self.var_base_column = StringVar(value=self.equip_instance.headers().name_array()[0])
        self.var_num_corrections = IntVar(value=self.cf.num_corrections)
        self.var_wb_db = BooleanVar(value=False)
        self.var_mod_type = StringVar(value=self.cf.correction_type.name)

        # finally build out the gui ahead of setting up the traces
        self._build_gui()

        # set up tracing
        self.var_num_corrections.trace('w', self._update_from_traces)
        self.var_mod_type.trace('w', self._update_from_traces)
        self.var_base_column.trace('w', self._update_from_traces)
        self.var_wb_db.trace('w', self._update_from_traces)

        # other misc GUI functions
        self._setup_removal_callback(remove_callback)

    def _update_from_traces(self, *_):  # pragma: no cover
        try:
            self.cf.num_corrections = self.var_num_corrections.get()
        except TclError:
            self.cf.num_corrections = 0  # if blank, set to zero for now
        if self.var_mod_type.get() == CorrectionFactorType.Multiplier.name:
            self.cf.correction_type = CorrectionFactorType.Multiplier
        elif self.var_mod_type.get() == CorrectionFactorType.Replacement.name:
            self.cf.correction_type = CorrectionFactorType.Replacement
        elif self.var_mod_type.get() == CorrectionFactorType.CombinedDbWb.name:
            self.cf.correction_type = CorrectionFactorType.CombinedDbWb
        mod_column = self.var_base_column.get()
        self.cf.base_column_index = self.equip_instance.headers().name_array().index(mod_column)
        self.cf.columns_to_modify = self.columns_listbox.curselection()
        if self.cf.correction_type == CorrectionFactorType.CombinedDbWb:
            self.base_column_dropdown['state'] = DISABLED
        else:
            self.base_column_dropdown['state'] = ACTIVE

    def _setup_removal_callback(self, remove_callback: Callable):
        self.remove_me = False
        self.remove_callback = remove_callback

    def _build_gui(self):  # pragma: no cover
        p = 4
        Button(self, text="❌ Remove This Factor", command=self._remove).grid(
            row=0, column=0, padx=p, pady=p
        )
        Separator(self, orient=HORIZONTAL).grid(
            row=1, column=0, sticky=EW, padx=p, pady=p
        )
        corr_frame = Frame(self)
        Label(corr_frame, text="# Correction Values").grid(
            row=0, column=0, padx=p, pady=p
        )
        Spinbox(corr_frame, from_=1, to=99, width=4, textvariable=self.var_num_corrections).grid(
            row=0, column=1, padx=p, pady=p
        )
        corr_frame.grid(
            row=2, column=0, padx=p, pady=p
        )
        lf = LabelFrame(self, text="Correction Factor Type")
        Radiobutton(
            lf, text="Multiplier", value=CorrectionFactorType.Multiplier.name, variable=self.var_mod_type
        ).pack(
            side=TOP, anchor=W, padx=p, pady=p
        )
        Radiobutton(
            lf, text="Replacement", value=CorrectionFactorType.Replacement.name, variable=self.var_mod_type
        ).pack(
            side=TOP, anchor=W, padx=p, pady=p
        )
        headers = self.equip_instance.headers()
        state = ACTIVE if headers.get_db_column() >= 0 and headers.get_wb_column() >= 0 else DISABLED
        Radiobutton(
            lf, text="Combined DB/WB Factor", value=CorrectionFactorType.CombinedDbWb.name, variable=self.var_mod_type,
            state=state
        ).pack(
            side=TOP, anchor=W, padx=p, pady=p
        )
        lf.grid(row=3, column=0, columnspan=2, padx=p, pady=p)
        Separator(self, orient=VERTICAL).grid(
            row=0, column=1, rowspan=5, sticky=NS, padx=p, pady=p
        )
        options = Variable(value=self.equip_instance.headers().name_array())
        Label(self, text="Base data column for this correction factor:").grid(
            row=0, column=2, padx=p, pady=p
        )
        self.base_column_dropdown = OptionMenu(self, self.var_base_column, *options.get())
        self.base_column_dropdown.grid(row=1, column=2, sticky=EW, padx=p, pady=p)
        Label(self, text="Data affected by this correction factor:").grid(
            row=2, column=2, padx=p, pady=p
        )
        columns_frame = Frame(self)
        self.columns_listbox = Listbox(columns_frame, height=5, listvariable=options, selectmode=MULTIPLE)
        self.columns_listbox.configure(exportselection=False)
        self.columns_listbox.pack(side=LEFT, fill=BOTH, expand=True, padx=p, pady=3)
        self.columns_listbox.bind('<<ListboxSelect>>', self._update_from_traces)
        columns_scroll = Scrollbar(columns_frame)
        columns_scroll.pack(side=RIGHT, fill=BOTH)
        self.columns_listbox.config(yscrollcommand=columns_scroll.set)
        columns_scroll.config(command=self.columns_listbox.yview)
        columns_frame.grid(
            row=3, column=2, sticky=EW, padx=p, pady=p
        )

    def _remove(self):
        self.remove_me = True
        self.remove_callback()

    def check_ok(self) -> bool:
        """Checks the underlying correction factor for validity"""
        db = self.equip_instance.headers().get_db_column()
        wb = self.equip_instance.headers().get_wb_column()
        return self.cf.check_ok(db, wb, summary_only=True)

    def description(self):
        return f"CorrectionFactor {self.equip_instance.name}; {self.cf.num_corrections} corrections"
