from tkinter import *


# Вкладка для вывода кода PCWorx
class OutputFrame(Frame):
    tab_name = 'Импорт в PCWorx'

    def __init__(self, master=None, generator=None):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        if generator is not None:
            code = self.create_text_pane('Код для Modbus сервера', generator.get_mb_code())
            code.grid(column=0, row=0, sticky=(N, S, W, E))
            code.config(height='200px')
            local_vars, type_decls = generator.generate_locals()
            variables = self.create_text_pane('Переменные', local_vars.strip())
            variables.grid(column=0, row=1, sticky=(N, S, W, E))
            variables.grid_propagate(False)
            variables.config(height='100px')
            types = self.create_text_pane('Типы', type_decls)
            types.grid(column=0, row=2, sticky=(N, S, W, E))
            types.grid_propagate(False)
            types.config(height='100px')

    def create_text_pane(self, caption, text):
        frame = Frame(self)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        label = Label(frame, text=caption)
        label.grid(column=0, columnspan=2, row=0, sticky=(N, S, W, E))
        # Вертикальный скроллбар
        scrollbar = Scrollbar(frame)
        scrollbar.grid(column=1, row=1, sticky=(N, S, E))
        # Поле вывода кода
        code = Text(frame, yscrollcommand=scrollbar.set, wrap=NONE)
        code.grid(column=0, row=1, sticky=(N, S, W, E))
        scrollbar.config(command=code.yview)
        code.insert(1.0, text)
        code.config(state=DISABLED)
        code.bind('<Control-c>', self.copy)
        return frame

    def copy(self, event=None):
        try:
            text = event.widget.get(SEL_FIRST, SEL_LAST)
            text = text.encode('cp1251')
            self.clipboard_clear()
            self.clipboard_append(text)
        except UnicodeEncodeError:
            pass
        return 'break'
