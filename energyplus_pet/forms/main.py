from tkinter import (
    Tk,
    Button,
    Frame,
    Label,
    LEFT,
)

from energyplus_pet import NICE_NAME, VERSION


class EnergyPlusPetWindow:
    """A really great parameter estimation tool main window"""

    def __init__(self) -> None:
        """
        The main window of the parameter estimation tool GUI workflow.
        This window stores an instance of tk.Tk since everything GUI-related
        starts with this form.
        """
        self.root = Tk()
        self.window = Frame(self.root, borderwidth=10)
        self.window.pack()
        self.root.title(f"{NICE_NAME}: {VERSION}")

        lbl1 = Label(self.window, bg='SlateGray3', width=15, height=10)
        lbl1.pack(side=LEFT, padx=3)

        lbl2 = Label(self.window, bg='SlateGray4', width=15, height=10)
        lbl2.pack(side=LEFT)

        lbl3 = Label(self.window, bg='DarkSeaGreen3', width=15, height=10)
        lbl3.pack(side=LEFT, padx=3)

        lbl4 = Label(self.window, bg='DarkSeaGreen4', width=15, height=10)
        lbl4.pack(side=LEFT)

        btn1 = Button(self.window, text='Button', command=self.greet)
        btn1.pack(side=LEFT, padx=5)

        self.window.pack()

    def greet(self) -> None:
        """
        Small helper function to handle a button press event
        """
        print("HEY!")

    def run(self) -> None:
        """
        Executes the Tk main loop to handle all GUI events and update
        """
        self.root.mainloop()
