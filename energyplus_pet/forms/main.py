import tkinter as tk


class EnergyPlusPetWindow:
    """A really great parameter estimation tool main window"""

    def __init__(self) -> None:
        """
        The main window of the parameter estimation tool GUI workflow
        """
        self.window = tk.Tk()
        greeting = tk.Label(text="Hello, Tkinter")
        greeting.pack()

    def run(self) -> None:
        """
        Runs the main GUI loop
        """
        self.window.mainloop()
