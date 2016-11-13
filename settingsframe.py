from tkinter import *
from tkinter import filedialog
from scrollableframe import VerticalScrolledFrame


class SettingsFrame(Frame):
    def __init__(self, master, project):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, minsize='25px')
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.project = project
        self.settings = project.settings
        self.tab_name = 'Настройки'
        self.interior = self

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
        frame.grid(row=2, column=0, sticky=(W, E), pady='1px', columnspan=2)
        frame = self.create_bit_setting('Генерировать бит возврата настроек:', self.settings.gen_cancel,
                                        self.settings.gen_cancel_word, self.settings.gen_cancel_bit)
        frame.grid(row=3, column=0, sticky=(W, E), pady='1px', columnspan=2)
        frame = self.create_file_setting('Файл экспорта адресных меток в Weintek:', self.settings.weintek_tag_file,
                                         '.csv', [('Файл данных, разделенных запятыми', '.csv')])
        frame.grid(row=4, column=0, sticky=(W, E), pady='1px', columnspan=2)
        frame = self.create_file_setting('Файл экспорта событий в Weintek:', self.settings.weintek_event_file,
                                         '.xls', [('Файл Microsoft Excel', '.xls')])
        frame.grid(row=5, column=0, sticky=(W, E), pady='1px', columnspan=2)
        frame = self.create_file_setting('Файл экспорта событий в WebVisit:', self.settings.webvisit_file,
                                         '.csv', [('Файл данных, разделенных запятыми', '.csv')])
        frame.grid(row=6, column=0, sticky=(W, E), pady='1px', columnspan=2)
        frame = self.create_file_setting('Файл экспорта описаний событий в WebVisit:', self.settings.webvisit_text_file,
                                         '.csv', [('Файл данных, разделенных запятыми', '.csv')])
        frame.grid(row=7, column=0, sticky=(W, E), pady='1px', columnspan=2)

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
        label = Label(frame, text='Слово')
        label.grid(row=0, column=2, sticky=W, padx='1px')
        entry = Entry(frame, textvariable=address.var, width=5)
        entry.grid(row=0, column=3, sticky=(W, E), padx='2px')
        label = Label(frame, text='Бит')
        label.grid(row=0, column=4, sticky=W, padx='1px')
        entry = Entry(frame, textvariable=bit.var, width=5)
        entry.grid(row=0, column=5, sticky=(W, E), padx='2px')
        return frame

    def create_file_setting(self, caption, file_name, *args):

        def browse():
            prompt = caption.replace('Файл', '')[0:-1]
            self.browse_for_file(prompt, *args, file_name)

        frame = Frame(self.interior)
        frame.columnconfigure(1, weight=1)
        label = Label(frame, text=caption, width=37, anchor=W)
        label.grid(row=0, column=0, sticky=W, padx='5px')
        entry = Entry(frame, textvariable=file_name.var)
        entry.grid(row=0, column=1, sticky=(W, E), padx='3px')
        button = Button(frame, text='Обзор...', width=10, command=browse)
        button.grid(row=0, column=2, padx='7px')
        return frame

    def browse_for_file(self, caption, ext, file_types, text_var):
        filename = filedialog.asksaveasfilename(title='Выберите файл' + caption, confirmoverwrite=True,
                                                parent=self.master, defaultextension=ext, filetypes=file_types)
        if filename != '':
            text_var.var.set(filename)
