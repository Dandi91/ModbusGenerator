from tkinter import *
from scrollableframe import VerticalScrolledFrame


class SettingsFrame(Frame):
    def __init__(self, master, project):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Создаем окно, которое скроллится
        self.frame = VerticalScrolledFrame(self)
        self.frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.frame.interior.rowconfigure(0, minsize='25px')
        self.frame.interior.columnconfigure(0, weight=1)
        self.frame.interior.columnconfigure(1, weight=1)

        self.project = project
        self.settings = project.generator_settings
        self.tab_name = 'Настройки'
        self.interior = self.frame.interior

        frame = self.create_labeled_entry('Имя массива Modbus:', self.settings.mb_arr_name)
        frame.grid(row=0, column=0, sticky=(W, E, S), pady='3px')
        frame = self.create_labeled_entry('Имя указателя Modbus:', self.settings.mb_cursor_name)
        frame.grid(row=0, column=1, sticky=(W, E, S), pady='3px')
        frame = self.create_labeled_entry('Имя ПЛК в Weintek:', self.settings.plc_name)
        frame.grid(row=1, column=0, sticky=(W, E), pady='3px')
        frame = self.create_labeled_entry('Начальный адрес Modbus:', self.settings.start_address)
        frame.grid(row=1, column=1, sticky=(W, E), pady='3px')
        frame = self.create_bit_setting('Генерировать бит сохранения настроек:', self.settings.gen_save,
                                        self.settings.gen_save_word, self.settings.gen_save_bit)
        frame.grid(row=2, column=0, sticky=(W, E), pady='1px')
        frame = self.create_bit_setting('Генерировать бит возврата настроек:', self.settings.gen_cancel,
                                        self.settings.gen_cancel_word, self.settings.gen_cancel_bit)
        frame.grid(row=3, column=0, sticky=(W, E), pady='1px')

    def create_labeled_entry(self, caption, text):
        frame = Frame(self.interior)
        frame.columnconfigure(1, weight=1)
        label = Label(frame, text=caption, width=25, anchor=W)
        label.grid(row=0, column=0, sticky=W, padx='5px')
        entry = Entry(frame, textvariable=text.var)
        entry.grid(row=0, column=1, sticky=(W, E), padx='5px')
        return frame

    def create_bit_setting(self, caption, flag, address, bit):
        frame = Frame(self.interior)
        label = Label(frame, text=caption, width=35, anchor=W)
        label.grid(row=0, column=0, sticky=W, padx='5px')
        cb = Checkbutton(frame, variable=flag.var)
        cb.grid(row=0, column=1, sticky=W, padx='5px', pady=0)
        entry = Entry(frame, textvariable=address.var, width=5)
        entry.grid(row=0, column=2, sticky=(W, E), padx='5px')
        entry = Entry(frame, textvariable=bit.var, width=5)
        entry.grid(row=0, column=3, sticky=(W, E), padx='5px')
        return frame
