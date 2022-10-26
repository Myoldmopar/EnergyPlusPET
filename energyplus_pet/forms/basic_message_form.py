from tkinter import Toplevel, Button, Label, TOP, X, CENTER, HORIZONTAL, LEFT
from tkinter.ttk import Separator


class PetMessageForm(Toplevel):
    """Tkinter dialogs look a little funny on Linux, just building a basic form myself"""
    def __init__(self, parent_window, title: str, message: str, subtitle: str = '', justify_message_left: bool = False):
        super().__init__(parent_window)
        self.title(title)
        if subtitle:
            Label(self, text=subtitle).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
            Separator(self, orient=HORIZONTAL).pack(side=TOP, fill=X, expand=False, padx=3, pady=3)
        justify = LEFT if justify_message_left else CENTER
        Label(self, text=message, justify=justify).pack(side=TOP, fill=X, expand=True, padx=3, pady=3)
        Button(self, text="OK", command=self._done).pack(side=TOP, expand=False, anchor=CENTER, padx=3, pady=3)
        self.grab_set()
        self.transient(parent_window)

    def _done(self):
        self.grab_release()
        self.destroy()
