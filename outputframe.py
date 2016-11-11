from tkinter import *


# Вкладка для вывода кода PCWorx
class OutputFrame(Frame):
    def __init__(self, master=None, text=''):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Вертикальный скроллбар
        self.scrollbar = Scrollbar(self)
        self.scrollbar.grid(column=1, row=0, sticky=(N, S, E))
        # Поле вывода кода
        self.text_pane = Text(self, undo=True, maxundo=25, yscrollcommand=self.scrollbar.set)
        self.text_pane.grid(column=0, row=0, sticky=(N, S, W, E))
        self.text_pane.focus()
        self.scrollbar.config(command=self.text_pane.yview)
        self.text_pane.insert(1.0, text)
        self.text_pane.config(state=DISABLED)
