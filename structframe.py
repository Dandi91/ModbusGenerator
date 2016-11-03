from tkinter import *
from tkinter.ttk import Combobox
from scrollableframe import VerticalScrolledFrame
from project import states


# Строка таблицы, описывающей поля структуры
class TableRow(Frame):

    def __init__(self, master, field, color):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.columnconfigure(2, weight=1)

        self.controls = list()
        self.bg_color = color
        self.bind('<Enter>', self._mark_row)
        self.bind('<Leave>', self._unmark_row)

        # Создаем надписи
        self.create_lb(0, field.name, 32, W)
        self.create_lb(1, field.type, 24, CENTER)
        self.create_lb(2, field.comment, 24, W)

        # Создаем чекбоксы, присваивая их переменные настройкам поля
        # для динамического обновления данных
        field.exported.assign(self.create_cb(3, 8))
        field.separate.assign(self.create_cb(5, 3))

        # Создаем выпадающий список с вариантами статуса
        var = StringVar()
        field.state.assign(var)
        cb = Combobox(self, textvariable=var, values=states, width=25)
        cb.state(['readonly'])
        cb.grid(column=4, row=0, sticky=(W, E))

    # Функция-хелпер для создания надписей в колонке col с текстом text,
    # шириной width символов, и центровкой anchor
    def create_lb(self, col, text, width, anchor):
        lb = Label(self, text=text, width=width, anchor=anchor, bg=self.bg_color, pady=2)
        lb.grid(column=col, row=0, sticky=(W, E))
        self.controls.append(lb)

    # Функция-хелпер для создания чекбокса в колонке col шириной width
    # Возвращает переменную, значение которой синхронизировано с состоянием чекбокса
    def create_cb(self, col, width=0):
        cb = Checkbutton(self, width=width, height=0, bg=self.bg_color, pady=0)
        var = BooleanVar(cb)
        cb.config(variable=var)
        cb.grid(column=col, row=0, sticky=E)
        self.controls.append(cb)
        return var

    # Функция-колбэк, вызываемая при наведении мыши на строку
    def _mark_row(self, event):
        # При этом все компоненты в строке меняют цвет, выделяя текущую строку
        for ctrl in self.controls:
            ctrl.config(bg='#efe4b0')

    # Функция-колбэк, вызываемая при выходе мыши за строку
    def _unmark_row(self, event):
        # При этом все компоненты в строке меняют цвет на цвет по умолчанию
        for ctrl in self.controls:
            ctrl.config(bg=self.bg_color)


# Вкладка для отображения структур PC-Worx
class StructFrame(Frame):

    def __init__(self, master, struct):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(2, weight=1)
        # Создаем окно, которое скроллится
        self.frame = VerticalScrolledFrame(self)
        self.frame.grid(column=0, columnspan=6, row=2, sticky=(N, S, E, W))
        self.frame.interior.columnconfigure(2, weight=1)

        self.num_rows = 0
        self.struct = struct
        self.tab_name = self.struct.name
        # Поле для ввода названий экземпляров структуры
        lb = Label(self, text='Экземпляры:')
        lb.grid(row=0, column=0, sticky=E, padx=3)
        text = StringVar()
        instances = Entry(self, textvariable=text)
        struct.instances_str.assign(text)
        instances.grid(row=0, column=1, columnspan=5, sticky=(W, E), padx=4, pady=4)
        # Вставляем заголовок таблицы
        self.insert_header()
        # Создаем строки для полей структуры
        for field in self.struct.fields:
            self.append_row(field)

    # Метод добавления заголовка
    def insert_header(self):

        # Функция-хелпер, создает надпись с текстом text в колонке col шириной width
        def header_lb(col, text, width = 0):
            lb = Label(self, text=text, width=width)
            lb.grid(column=col, row=1, sticky=(W, E))

        header_lb(0, 'Название', 32)
        header_lb(1, 'Тип', 23)
        header_lb(2, 'Комментарий')
        header_lb(3, 'Передавать', 19)
        header_lb(4, 'Назначение', 17)
        header_lb(5, 'Отдельно', 12)

    # Метод добавления строки для поля field структуры
    def append_row(self, field):
        # Чередование цветов строк
        if self.num_rows % 2 == 0:
            bg_color = '#d0d0d0'
        else:
            bg_color = '#f0f0f0'

        row = TableRow(self.frame.interior, field, bg_color)
        row.grid(column=0, columnspan=6, row=self.num_rows, sticky=(W, E))
        self.num_rows += 1
