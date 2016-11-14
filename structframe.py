from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
from scrollableframe import VerticalScrolledFrame
from project import states, PhoenixField
from generator import type_size


# Строка таблицы, описывающей поля структуры
class TableRow(Frame):
    mismatch_color = '#ff9797'

    def __init__(self, master, field, color, parent):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.columnconfigure(2, weight=1)

        self.controls = list()
        self.bg_color = color
        self.temp_entry = None
        self.hidden_label = None
        self.temp_text = StringVar()
        self.column_num = 0
        self.parent = parent
        self.field = field
        self.bind('<Enter>', self._mark_row)
        self.bind('<Leave>', self._unmark_row)

        # Создаем надписи
        self.create_lb(0, field.name, 32, W)
        self.create_lb(1, field.type, 24, CENTER)
        self.create_lb(2, field.comment, 24, W)

        # Создаем выпадающий список с вариантами статуса
        cbb = Combobox(self, textvariable=field.state.var, values=states, width=25)
        cbb.state(['readonly'])
        cbb.grid(column=3, row=0, sticky=(W, E))

        # Создаем чекбокс для отметки события
        self.create_cb(field.event.var, 4)

    # Функция-хелпер для создания надписей в колонке col с текстом text,
    # шириной width символов, и центровкой anchor
    def create_lb(self, col, text, width, anchor):
        lb = Label(self, text=text, width=width, anchor=anchor, bg=self.bg_color, pady=2)
        lb.grid(column=col, row=0, sticky=(W, E))
        lb.bind('<Double-Button-1>', self._dblclick)
        lb.bind('<Button-3>', self._right_click)
        self.controls.append(lb)

    # Функция-хелпер для создания чекбокса в колонке col шириной width
    # Возвращает переменную, значение которой синхронизировано с состоянием чекбокса
    def create_cb(self, var, col, width=0):
        cb = Checkbutton(self, width=width, height=0, bg=self.bg_color, pady=0)
        cb.config(variable=var)
        cb.grid(column=col, row=0, sticky=E)
        self.controls.append(cb)

    def add(self):
        self._endedit(None)
        self.parent.add(self.field)

    def delete(self):
        self._endedit(None)
        self.parent.delete(self.field)

    # Функция-колбэк, вызываемая при наведении мыши на строку
    def _mark_row(self, event):
        # При этом все компоненты в строке меняют цвет, выделяя текущую строку
        for ctrl in self.controls:
            ctrl.config(bg='#efe4b0')

    # Функция-колбэк, вызываемая при выходе мыши за строку
    def _unmark_row(self, event):
        # При этом все компоненты в строке меняют цвет на цвет по умолчанию
        if self.field.mismatch:
            color_to_use = self.mismatch_color
        else:
            color_to_use = self.bg_color
        for ctrl in self.controls:
            ctrl.config(bg=color_to_use)

    # Функция-колбэк, вызываемая при двойном клике на определенный компонент
    def _dblclick(self, event):
        # Отменить текущее изменение (во всех строках)
        self._endedit(None)
        self.parent.cancel_editing()
        # Создать текстовое поле и скрыть надпись
        label = event.widget
        options = label.grid_info()
        label.grid_forget()
        self.hidden_label = label
        self.column_num = options['column']
        if self.column_num == 1:
            values = list()
            for type_name in type_size.keys():
                values.append(type_name.upper())
            values.sort()
            self.temp_entry = Combobox(self, textvariable=self.temp_text, values=values, width=24)
            self.temp_entry.state(['readonly'])
        else:
            self.temp_entry = Entry(self, textvariable=self.temp_text, width=37)
        self.temp_text.set(label.cget('text'))
        self.temp_entry.grid(column=self.column_num, row=0, sticky=(W, E), padx=2, pady=2)
        if self.column_num == 1:
            self.temp_entry.grid(pady=0, padx=3)
        self.temp_entry.focus()
        self.temp_entry.bind('<Return>', self._confirm)
        self.temp_entry.bind('<Escape>', self._endedit)

    # Функция-колбэк, вызываемая при нажатии Enter во временном поле ввода
    def _endedit(self, event):
        if self.temp_entry is not None:
            self.temp_entry.grid_forget()
            self.hidden_label.grid(column=self.column_num, row=0, sticky=(W, E))
            self.temp_entry = None

    def _confirm(self, event):
        properties = {0: 'name', 1: 'type', 2: 'comment'}
        prop = properties[self.column_num]
        new_text = self.temp_text.get()
        if new_text != getattr(self.field, prop):
            setattr(self.field, prop, self.temp_text.get())
            self.field.changed()
            self.hidden_label.config(text=new_text)
        self._endedit(event)
        self.parent.update_rows()

    def _right_click(self, event):
        popup = Menu(self, tearoff=0)
        popup.add_command(label='Добавить переменную', command=self.add)
        popup.add_command(label='Удалить переменную', command=self.delete)
        try:
            popup.tk_popup(event.x_root + 82, event.y_root + 11, 0)
        finally:
            popup.grab_release()


# Базовый класс для ввода полей/переменных
class TableFrame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        # Создаем окно, которое скроллится
        self.frame = VerticalScrolledFrame(self)
        self.frame.grid(column=0, columnspan=5, row=2, sticky=(N, S, E, W))
        self.frame.interior.columnconfigure(2, weight=1)

        self.num_rows = 0
        self.rows = list()
        self.fields = None
        self.struct_callback = None
        self.frame.canvas.bind('<Button-3>', self._right_click)

    # Метод добавления заголовка
    def insert_header(self):

        # Функция-хелпер, создает надпись с текстом text в колонке col шириной width
        def header_lb(col, text, width=0):
            lb = Label(self, text=text, width=width)
            lb.grid(column=col, row=1, sticky=(W, E))

        header_lb(0, 'Название', 32)
        header_lb(1, 'Тип', 23)
        header_lb(2, 'Комментарий')
        header_lb(3, 'Назначение', 18)
        header_lb(4, 'Событие', 9)

    # Метод добавления строки для поля field структуры
    def append_row(self, field):
        # Чередование цветов строк
        if self.num_rows % 2 == 0:
            bg_color = '#d0d0d0'
        else:
            bg_color = '#f0f0f0'

        row = TableRow(self.frame.interior, field, bg_color, self)
        row.grid(column=0, columnspan=5, row=self.num_rows, sticky=(W, E))
        self.rows.append(row)
        self.num_rows += 1

    def cancel_editing(self):
        for row in self.rows:
            row._endedit(None)

    def add(self, field=None):
        if field is not None:
            insertion_point = self.fields.index(field)
        else:
            insertion_point = len(self.fields)
        self.fields.insert(insertion_point, PhoenixField(callback=self.struct_callback))
        self.fill_in()

    def delete(self, field):
        if messagebox.askyesno('Внимание', 'Вы действительно хотите удалить переменную \'{}\'?'.format(field.name)):
            self.fields.remove(field)
            self.struct_callback()
            self.fill_in()

    def update_rows(self):
        duplicates = list()
        for field in self.fields:
            if self.fields.count(field) > 1 and field not in duplicates:
                duplicates.append(field)
        if len(duplicates) > 0:
            message = 'Следующие поля имеют не уникальные имена:\n'
            for dup in duplicates:
                message += dup.name + '\n'
            messagebox.showerror('Ошибка', message)
        self.fields.sort(key=lambda f: f.name)
        self.fill_in()

    def fill_in(self):
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        # Создаем строки для полей структуры
        self.num_rows = 0
        for field in self.fields:
            self.append_row(field)

    def _right_click(self, event):
        popup = Menu(self, tearoff=0)
        popup.add_command(label='Добавить переменную', command=self.add)
        try:
            popup.tk_popup(event.x_root + 82, event.y_root + 11, 0)
        finally:
            popup.grab_release()


# Вкладка для отображения структур PC-Worx
class StructFrame(TableFrame):
    def __init__(self, master, struct):
        TableFrame.__init__(self, master)
        self.tab_name = struct.name
        # Вставить строчку с экземплярами
        lb = Label(self, text='Экземпляры:')
        lb.grid(row=0, column=0, sticky=E, padx=3)
        instances = Entry(self, textvariable=struct.instances_str.var)
        instances.grid(row=0, column=1, columnspan=4, sticky=(W, E), padx=4, pady=4)
        # Вставляем заголовок таблицы
        self.insert_header()
        self.fields = struct.fields
        self.struct_callback = struct.changed
        self.fill_in()


# Вкладка для отображения отдельных переменных
class SinglesFrame(TableFrame):
    def __init__(self, master, project):
        TableFrame.__init__(self, master)
        self.tab_name = 'Отдельные переменные'
        self.insert_header()
        self.fields = project.singles
        self.struct_callback = project.changed
        self.fill_in()
