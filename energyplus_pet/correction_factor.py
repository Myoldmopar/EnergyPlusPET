from enum import Enum, auto
from tkinter import Button, Frame, Label, LabelFrame, TOP, Spinbox, IntVar, Scrollbar, LEFT, BOTH, RIGHT, EW, \
    BooleanVar, VERTICAL, Radiobutton, StringVar, W, NS, OptionMenu, MULTIPLE, Listbox, Variable
from tkinter.ttk import Separator
from typing import List, Tuple, Callable


class CorrectionFactorType(Enum):
    Multiplier = auto()
    Replacement = auto()


# TODO: Separate the GUI rendering out of here


class CorrectionFactor:
    """
    Defines the correction factor information and can return a Tk Frame
    """

    def __init__(self, name: str, remove_callback: Callable):
        self.name = name
        self.base_column_index: int  # TODO: Use this as the OptionMenu current selection ideally
        self.columns_to_modify: Tuple[int]  # TODO: Use this as the list of columns selected in the Listbox
        self.num_corrections: int
        self.base_data: List[float]
        self.affected_data: List[List[float]]
        # self.correction_is_wbdb: bool
        self.correction_db_value: float
        self.is_new_or_blank: bool = True
        self.remove_me = False
        self.remove_callback = remove_callback
        self.num_corrections = 0
        # eventually Tk Variables, but assigned to None here to allow unit testing to pass on non-GUI terminals
        self.base_column_str = None
        self.num_corrections_var = None
        self.wb_db_factor = None
        self.mod_type = None

    def not_new_anymore(self):
        self.is_new_or_blank = False

    def update_num_corrections(self, *_):  # pragma: no cover
        self.num_corrections = self.num_corrections_var.get()

    def render_as_tk_frame(self, parent: Frame) -> LabelFrame:  # pragma: no cover
        self.base_column_str = StringVar(value="Monday")  # TODO: Select a reasonable guess from data columns
        self.num_corrections_var = IntVar()
        self.num_corrections_var.trace('w', self.update_num_corrections)
        self.wb_db_factor = BooleanVar()
        self.mod_type = StringVar(value=CorrectionFactorType.Multiplier.name)
        f = LabelFrame(parent, text=self.name)
        p = 4
        Button(f, text="❌ Remove", command=self.remove).grid(
            row=0, column=0, padx=p, pady=p
        )
        Label(f, text="# Correction Values").grid(
            row=1, column=1, padx=p, pady=p
        )
        Spinbox(f, from_=2, to=15, width=4, textvariable=self.num_corrections_var).grid(
            row=1, column=2, padx=p, pady=p
        )
        # Checkbutton(f, text="This is a WB/DB Factor", variable=self.wb_db_factor, state="disabled").grid(
        #     row=2, column=1, columnspan=2, rowspan=2, padx=p, pady=p
        # )
        # Separator(f, orient=VERTICAL).grid(
        #     row=0, column=3, rowspan=4, sticky=NS, padx=p, pady=p
        # )
        lf = LabelFrame(f, text="Correction Factor Type")
        Radiobutton(lf, text="Multiplier", value=CorrectionFactorType.Multiplier.name, variable=self.mod_type).pack(
            side=TOP, anchor=W, padx=p, pady=p
        )
        Radiobutton(lf, text="Replacement", value=CorrectionFactorType.Replacement.name, variable=self.mod_type).pack(
            side=TOP, anchor=W, padx=p, pady=p
        )
        lf.grid(row=2, column=1, rowspan=2, columnspan=2, padx=p, pady=p)
        Separator(f, orient=VERTICAL).grid(
            row=0, column=3, rowspan=4, sticky=NS, padx=p, pady=p
        )
        options = Variable(value=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        Label(f, text="Base data column for this correction factor:").grid(
            row=0, column=4, padx=p, pady=p
        )
        OptionMenu(f, self.base_column_str, *options.get()).grid(
            row=1, column=4, sticky=EW, padx=p, pady=p
        )
        Label(f, text="Data affected by this correction factor:").grid(
            row=2, column=4, padx=p, pady=p
        )
        columns_frame = Frame(f)
        columns_listbox = Listbox(columns_frame, height=5, listvariable=options, selectmode=MULTIPLE)
        columns_listbox.pack(side=LEFT, fill=BOTH, expand=True, padx=p, pady=3)
        columns_scroll = Scrollbar(columns_frame)
        columns_scroll.pack(side=RIGHT, fill=BOTH)
        columns_listbox.config(yscrollcommand=columns_scroll.set)
        columns_scroll.config(command=columns_listbox.yview)
        columns_frame.grid(
            row=3, column=4, sticky=EW, padx=p, pady=p
        )
        return f

    def remove(self):
        self.remove_me = True
        self.remove_callback()

    def description(self):
        return f"CorrectionFactor {self.name}; {self.num_corrections} corrections"
