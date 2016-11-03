from tkinter import *


# Функция преобразования кракозябр из PC-Worx'а
# Если во входной строке попадаются корректные русские символы,
# то возвращает исходный текст вне зависимости от наличия кракозябр в нем
def fix_encoding(text):
    try:
        return text.encode('cp1252').decode('cp1251')
    except UnicodeEncodeError:
        return text


# Вкладка для ввода текста структур
class InputFrame(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Вертикальный скроллбар
        self.scrollbar = Scrollbar(self)
        self.scrollbar.grid(column=1, row=0, sticky=(N, S, E))
        # Поле ввода
        self.text_pane = Text(self, undo=True, maxundo=25, yscrollcommand=self.scrollbar.set)
        self.text_pane.bind('<Control-v>', self.paste)
        self.text_pane.grid(column=0, row=0, sticky=(N, S, W, E))
        self.text_pane.focus()
        self.scrollbar.config(command=self.text_pane.yview)

    # Переопределенный метод вставки текста в поле
    def paste(self, event):
        clip_text = ''
        try:
            # Получаем текст из буфера обмена
            clip_text = self.clipboard_get()
            # Удаляем весь выделенный текст из поля ввода
            start = self.text_pane.index(SEL_FIRST)
            end = self.text_pane.index(SEL_LAST)
            self.text_pane.delete(start, end)
        except TclError:
            pass
        # Исправляем кодировку текста из буфера
        clip_text = fix_encoding(clip_text)
        # Вставляем исправленный текст в поле
        self.text_pane.insert(INSERT, clip_text)
        self.text_pane.see(INSERT)
        return 'break'

    # Метод-обёртка, исправляющий кодировку всего текста в поле ввода
    def fix_encoding(self):
        text = self.text_pane.get(1.0, END)
        text = fix_encoding(text)
        self.text_pane.delete(1.0, END)
        self.text_pane.insert(1.0, text)
