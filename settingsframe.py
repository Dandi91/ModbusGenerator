from tkinter import *
from tkinter import filedialog
from tkinter import colorchooser
from project import EventType


class EventFrame(Frame):
    def __init__(self, master, event_type, right_click):
        Frame.__init__(self, master)
        self.event_type = event_type
        self.bind('<Button-3>', right_click)
        check = Checkbutton(self, variable=event_type.use.var, pady=0, width=2)
        check.grid(row=0, column=0, padx='10px')
        check.bind('<Button-3>', right_click)
        entry = Entry(self, textvariable=event_type.prefix.var, width=10)
        entry.grid(row=0, column=1, padx='5px', sticky=W)
        entry.bind('<Button-3>', right_click)
        color_box = Canvas(self, width=16, height=16, bg=event_type.color())
        color_box.grid(row=0, column=2, padx='4px')
        color_box.bind('<Button-1>', self.color_pick)
        color_box.bind('<Button-3>', right_click)

    def color_pick(self, event):
        triple, color = colorchooser.askcolor(event.widget.cget('bg'),
                                              title='Выберите цвет для префикса {}'.format(self.event_type.prefix()))
        if triple is None and color is None:
            return
        else:
            event.widget.config(bg=color)
            self.event_type.color(color)


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
        frame = self.create_event_setting(self.project.event_types)
        frame.grid(row=8, column=0, sticky=W, padx='5px', pady='3px')

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

    def create_event_setting(self, event_types):

        def add():
            new_event = EventType(callback=self.project.changed)
            event_types.append(new_event)
            self.project.changed()
            ef = EventFrame(frame, new_event, _right_click)
            ef.grid(column=0, row=len(event_types) + 1, pady='2px', columnspan=3)

        def delete(ef):
            self.project.event_types.remove(ef.event_type)
            self.project.changed()
            ef.destroy()

        def _right_click(event):

            def wrapper():
                if not isinstance(event.widget, EventFrame):
                    p = event.widget.nametowidget(event.widget.winfo_parent())
                    delete(p)
                else:
                    delete(event.widget)

            popup = Menu(frame, tearoff=0)
            popup.add_command(label='Добавить тип событий', command=add)
            parent = event.widget.nametowidget(event.widget.winfo_parent())
            if isinstance(event.widget, EventFrame) or isinstance(parent, EventFrame):
                popup.add_command(label='Удалить тип событий', command=wrapper)
            try:
                popup.tk_popup(event.x_root + 82, event.y_root + 11, 0)
            finally:
                popup.grab_release()

        frame = Frame(self.interior, borderwidth=2, relief=GROOVE, padx=5, pady=5)
        caption = Label(frame, text='Конфигурация событий:', anchor=W)
        caption.grid(row=0, column=0, sticky=(W, E), columnspan=3)
        caption.bind('<Button-3>', _right_click)
        caption = Label(frame, text='Автоопред.')
        caption.grid(row=1, column=0)
        caption.bind('<Button-3>', _right_click)
        caption = Label(frame, text='Префикс', width=10)
        caption.grid(row=1, column=1)
        caption.bind('<Button-3>', _right_click)
        caption = Label(frame, text='Цвет')
        caption.grid(row=1, column=2)
        caption.bind('<Button-3>', _right_click)
        for i, event in zip(range(len(event_types)), event_types):
            ef = EventFrame(frame, event, _right_click)
            ef.grid(column=0, row=i + 2, pady='2px', columnspan=3)
        frame.bind('<Button-3>', _right_click)
        return frame
