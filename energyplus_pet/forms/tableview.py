from tkinter import Frame, Entry, StringVar
from typing import List


class Cell:
    def __init__(self, parent_frame: Frame, initial_value: str = ''):
        self.var = StringVar(value=initial_value)
        self.entry = Entry(parent_frame, textvariable=self.var, width=10)


class TableView:
    def __init__(self, parent_frame: Frame, initial_num_rows: int, initial_num_columns: int):
        self.frame = Frame(parent_frame)
        self.cell_rows: List[List[Cell]] = []
        first_row = True
        for row_num in range(initial_num_rows):
            self.frame.grid_rowconfigure(row_num, weight=1)
            self.cell_rows.append([])
            for col_num in range(initial_num_columns):
                if first_row:
                    self.frame.grid_columnconfigure(col_num, weight=1)
                self.cell_rows[row_num].append(Cell(self.frame))
                self.cell_rows[row_num][col_num].entry.grid(row=row_num, column=col_num)
                # self.cells[row_num][col_num].entry.grid(row=row_num, column=col_num)
                self.cell_rows[row_num][col_num].var.set(f"[{row_num}, {col_num}]")
            first_row = False
