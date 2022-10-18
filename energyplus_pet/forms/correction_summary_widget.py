from enum import Enum, auto
from tkinter import Button, Frame, Label, LabelFrame, TOP, Spinbox, IntVar, Scrollbar, LEFT, BOTH, RIGHT, EW, \
    VERTICAL, Radiobutton, StringVar, W, NS, OptionMenu, MULTIPLE, Listbox, Variable
from tkinter.ttk import Separator
from typing import List, Callable

from energyplus_pet.equipment.base import BaseEquipment


class CorrectionFactorType(Enum):
    Multiplier = auto()
    Replacement = auto()


class CorrectionFactor:
    def __init__(self, name: str, eq: BaseEquipment):
        self.name = name
        self.equip_instance = eq
        # Once we start supporting the wb/db replacement, we'll need to check from the equipment instance
        # to see if it should be offered for this catalog data.  Then we'll need to track whether the user
        # wants it for this particular correction factor.  Then if so I think we need to track the db/wb value separate.
        # The following are the variables that define this correction factor summary, initialize them as needed and the
        # widget should reflect the initialized values by setting Tk Variables appropriately.
        self.num_corrections: int = 5
        # self.correction_is_wb_db: bool
        # self.correction_db_value: float
        self.correction_type: CorrectionFactorType = CorrectionFactorType.Multiplier
        self.base_column_index: int = 0
        self.columns_to_modify: List[int] = []


class CorrectionSummaryWidget(LabelFrame):
    """
    Defines the correction factor information and can return a Tk Frame
    """

    def __init__(self, parent: Frame, name: str, equipment_instance: BaseEquipment, remove_callback: Callable):
        super().__init__(parent, name=name, text=name)
        self.cf = CorrectionFactor(name, equipment_instance)

        # these are Tk variables for tracking dynamic changes and tracing
        self.var_base_column = StringVar(value=self.cf.equip_instance.headers().name_array()[self.cf.base_column_index])
        self.var_num_corrections = IntVar(value=self.cf.num_corrections)
        # self.wb_db_var = BooleanVar(value=False)
        self.var_mod_type = StringVar(value=self.cf.correction_type.name)

        # finally build out the gui ahead of setting up the traces
        self._build_gui()

        # set up tracing
        self.var_num_corrections.trace('w', self._update_from_traces)
        self.var_mod_type.trace('w', self._update_from_traces)
        self.var_base_column.trace('w', self._update_from_traces)

        # other misc GUI functions
        self._setup_removal_callback(remove_callback)

    def _update_from_traces(self, *_):  # pragma: no cover
        self.cf.num_corrections = self.var_num_corrections.get()
        # self.correction_is_wb_db = self.wb_db_var().get
        if self.var_mod_type.get() == CorrectionFactorType.Multiplier.name:
            self.cf.correction_type = CorrectionFactorType.Multiplier
        elif self.var_mod_type.get() == CorrectionFactorType.Replacement.name:
            self.cf.correction_type = CorrectionFactorType.Replacement
        mod_column = self.var_base_column.get()
        self.cf.base_column_index = self.cf.equip_instance.headers().name_array().index(mod_column)
        self.cf.columns_to_modify = self.columns_listbox.curselection()

    def _setup_removal_callback(self, remove_callback: Callable):
        self.remove_me = False
        self.remove_callback = remove_callback

    def _build_gui(self):  # pragma: no cover
        p = 4
        Button(self, text="❌ Remove This Factor", command=self._remove).grid(
            row=0, column=0, padx=p, pady=p
        )
        corr_frame = Frame(self)
        Label(corr_frame, text="# Correction Values").grid(
            row=0, column=0, padx=p, pady=p
        )
        Spinbox(corr_frame, from_=2, to=15, width=4, textvariable=self.var_num_corrections).grid(
            row=0, column=1, padx=p, pady=p
        )
        corr_frame.grid(
            row=1, column=0, padx=p, pady=p
        )
        # Checkbutton(f, text="This is a WB/DB Factor", variable=self.wb_db_factor, state="disabled").grid(
        #     row=2, column=1, columnspan=2, rowspan=2, padx=p, pady=p
        # )
        # Separator(f, orient=VERTICAL).grid(
        #     row=0, column=3, rowspan=4, sticky=NS, padx=p, pady=p
        # )
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
        lf.grid(row=2, column=0, rowspan=2, columnspan=2, padx=p, pady=p)
        Separator(self, orient=VERTICAL).grid(
            row=0, column=1, rowspan=4, sticky=NS, padx=p, pady=p
        )
        options = Variable(value=self.cf.equip_instance.headers().name_array())
        Label(self, text="Base data column for this correction factor:").grid(
            row=0, column=2, padx=p, pady=p
        )
        OptionMenu(self, self.var_base_column, *options.get()).grid(
            row=1, column=2, sticky=EW, padx=p, pady=p
        )
        Label(self, text="Data affected by this correction factor:").grid(
            row=2, column=2, padx=p, pady=p
        )
        columns_frame = Frame(self)
        self.columns_listbox = Listbox(columns_frame, height=5, listvariable=options, selectmode=MULTIPLE)
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

    def description(self):
        return f"CorrectionFactor {self.cf.equip_instance.name}; {self.cf.num_corrections} corrections"
