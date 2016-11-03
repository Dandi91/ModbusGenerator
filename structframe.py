from tkinter import *
from scrollableframe import VerticalScrolledFrame
from project import *


# Вкладка для отображения структур PC-Worx
class StructFrame(Frame):

    def __init__(self, master=None, struct=PhoenixStruct()):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Создаем окно, которое скроллится
        self.frame = VerticalScrolledFrame(self)
        self.frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.frame.interior.columnconfigure(2, weight=1)

        self.num_rows = 0
        self.struct = struct
        self.tab_name = self.struct.name
        # Вставляем заголовок таблицы
        self.insert_header()
        # Создаем строки для полей структуры
        for field in self.struct.fields:
            self.append_row(field)

    # Метод добавления заголовка
    def insert_header(self):

        # Функция-хелпер, создает надпись с текстом text в колонке col
        def header_lb(col, text):
            lb = Label(self.frame.interior, text=text)
            lb.grid(column=col, row=self.num_rows, sticky=(W, E))

        header_lb(0, 'Название')
        header_lb(1, 'Тип')
        header_lb(2, 'Комментарий')
        header_lb(3, 'Передача')
        header_lb(4, 'Настройка')
        header_lb(5, 'Контроль')
        header_lb(6, 'Отдельно')
        self.num_rows += 1

    # Метод добавления строки для поля field структуры
    def append_row(self, field=PhoenixField()):
        # Список всех компонентов в данной строке
        row_controls = list()
        # Чередование цветов строк
        if self.num_rows % 2 == 0: bg_color = '#d0d0d0'
        else: bg_color = '#f0f0f0'

        # Функция-колбэк, вызываемая при наведении мыши на строку
        def _mark_row(event):
            # При этом все компоненты в строке меняют цвет, выделяя текущую строку
            for ctrl in row_controls:
                ctrl.config(bg='#efe4b0')

        # Функция-колбэк, вызываемая при выходе мыши за строку
        def _unmark_row(event):
            # При этом все компоненты в строке меняют цвет на цвет по умолчанию
            for ctrl in row_controls:
                ctrl.config(bg=bg_color)

        # Функция-хелпер для создания надписей в колонке col с текстом text,
        # шириной width символов, и центровкой anchor
        def create_lb(col, text, width, anchor):
            lb = Label(self.frame.interior, text=text, width=width, anchor=anchor, bg=bg_color, pady=2)
            lb.bind('<Enter>', _mark_row)
            lb.bind('<Leave>', _unmark_row)
            lb.grid(column=col, row=self.num_rows, sticky=(W, E))
            row_controls.append(lb)

        # Функция-хелпер для создания чекбокса в колонке col
        # Возвращает переменную, значение которой синхронизировано с состоянием чекбокса
        def create_cb(col):
            cb = Checkbutton(self.frame.interior, width=0, height=0, bg=bg_color, pady=0)
            cb.bind('<Enter>', _mark_row)
            cb.bind('<Leave>', _unmark_row)
            var = BooleanVar(cb)
            cb.config(variable=var)
            cb.grid(column=col, row=self.num_rows, sticky=(W, E))
            row_controls.append(cb)
            return var

        # Создаем надписи
        create_lb(0, field.name, 32, W)
        create_lb(1, field.type, 24, CENTER)
        create_lb(2, field.comment, 24, W)
        # Создаем чекбоксы, присваивая их переменные настройкам поля
        # для динамического обновления данных
        field.exported.assign(create_cb(3))
        field.is_setting.assign(create_cb(4))
        field.is_control.assign(create_cb(5))
        field.is_separate.assign(create_cb(6))
        self.num_rows += 1
