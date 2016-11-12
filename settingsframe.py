from tkinter import *
from scrollableframe import VerticalScrolledFrame


class SettingsFrame(Frame):
    def __init__(self, master, project):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        # Создаем окно, которое скроллится
        self.frame = VerticalScrolledFrame(self)
        self.frame.grid(column=0, columnspan=5, row=2, sticky=(N, S, E, W))
        self.frame.interior.columnconfigure(2, weight=1)

        self.project = project
        self.tab_name = 'Настройки'
