from tkinter.ttk import *
from tkinter import filedialog, messagebox
from inputframe import *
from structframe import *
from project import Project


# Главный класс приложения - реализует окно верхнего уровня
# с меню и компонентом для закладок
class Application(Frame):
    title = 'Генератор модбаса v0.2'

    # Конструктор класса
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        top_win = self.winfo_toplevel()
        top_win.rowconfigure(0, weight=1)
        top_win.columnconfigure(0, weight=1)
        top_win.minsize(width=1024, height=500)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.project = None
        self.file_menu = None
        self.proj_menu = None
        self.notebook = None
        self.input_frame = None

        self.create_menus()
        self.update_wnd_state()

    # Метод создания пунктов меню
    def create_menus(self):
        main_menu = Menu(self.master)
        self.file_menu = Menu(main_menu, tearoff=0)
        self.file_menu.add_command(label='Новый проект', command=self.new_project)
        self.file_menu.add_command(label='Открыть проект...', command=self.open_project)
        self.file_menu.add_command(label='Сохранить проект', command=self.save_project)
        self.file_menu.add_command(label='Сохранить проект как...', command=self.save_project_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Выйти', command=self.master.quit)
        main_menu.add_cascade(label='Файл', menu=self.file_menu)

        self.proj_menu = Menu(main_menu, tearoff=0)
        self.proj_menu.add_command(label='Анализировать структуры заново', command=self.analyze_anew)
        self.proj_menu.add_command(label='Анализировать и добавить', command=self.analyze_add)
        main_menu.add_cascade(label='Проект', menu=self.proj_menu)

        self.master.config(menu=main_menu)

    # Метод создания многостраничного компонента с вкладками
    # Вызывается при переоткрытии проекта
    def create_notebook(self):
        self.notebook = Notebook(self)
        self.notebook.grid(column=0, row=0, sticky=(N, S, W, E))
        self.notebook.rowconfigure(0, weight=1)
        self.notebook.columnconfigure(0, weight=1)
        # Поле ввода текста
        self.input_frame = InputFrame(self.notebook)
        self.notebook.add(self.input_frame, text='Ввод структур', padding='4px')
        self.update_tabs()

    # Метод обновления вкладок со структурами
    # Вызывается каждый раз при новом анализе структур
    def update_tabs(self):
        # Удалить все закладки кроме первой
        while len(self.notebook.tabs()) > 1:
            self.notebook.forget(1)
        # Добавить нужные согласно project
        for struct in self.project.structs:
            struct_frame = StructFrame(self.notebook, struct)
            self.notebook.add(struct_frame, text=struct_frame.tab_name, padding='4px')
        if len(self.notebook.tabs()) > 1:
            self.notebook.select(1)

    # Анализировать заново, будет создан новый проект взамен существующего
    def analyze_anew(self):
        if len(self.project.structs) > 0:
            if not messagebox.askyesno('Внимание', 'Все существующие данные будут утеряны. Продолжить?',
                                       parent=self.master):
                return
            self.project = Project(callback=self.update_title)
        self.analyze_add()

    # Анализировать с добавлением, при обнаружении дубликатов будет выполнено слияние
    def analyze_add(self):
        text = self.input_frame.text_pane.get(1.0, END)
        self.project.analyze_input(text)
        self.update_tabs()

    # Процедура обновления состояний меню и окна
    # Запрещает вызов некоторых меню, если нет открытого проекта
    def update_wnd_state(self):
        if self.project is None:
            self.file_menu.entryconfigure(2, state=DISABLED)
            self.file_menu.entryconfigure(3, state=DISABLED)
            self.proj_menu.entryconfigure(0, state=DISABLED)
            self.proj_menu.entryconfigure(1, state=DISABLED)
            if self.notebook is not None:
                self.notebook.destroy()
                self.notebook = None
        else:
            self.file_menu.entryconfigure(2, state=NORMAL)
            self.file_menu.entryconfigure(3, state=NORMAL)
            self.proj_menu.entryconfigure(0, state=NORMAL)
            self.proj_menu.entryconfigure(1, state=NORMAL)
            if self.notebook is not None:
                self.notebook.destroy()
            self.create_notebook()
        self.update_title()

    # Метод для обновления заголовка окна
    def update_title(self):
        if self.project is None:
            self.master.title(self.title)
        else:
            # Добавляем имя файла в заголовок окна
            if self.project.filename is None:
                self.master.title('<Без имени>* - ' + self.title)
            elif self.project.modified:
                self.master.title(self.project.filename + '* - ' + self.title)
            else:
                self.master.title(self.project.filename + ' - ' + self.title)

    # Новый проект
    def new_project(self):
        if self.project is not None and self.project.modified:
            result = messagebox.askyesnocancel('Внимание', 'Сохранить текущий проект?', parent=self.master)
            if result is None:
                return
            elif result:
                self.save_project()
        self.project = Project(callback=self.update_title)
        self.update_wnd_state()

    # Открыть проект
    def open_project(self):
        if self.project is not None and self.project.modified:
            result = messagebox.askyesnocancel('Внимание','Сохранить текущий проект?', parent=self.master)
            if result is None:
                return
            elif result:
                self.save_project()
        filename = filedialog.askopenfilename(title='Открыть проект',
                                              multiple=False,
                                              parent=self.master,
                                              defaultextension='.mbgp',
                                              filetypes=[('Проекты генератора модбаса', '.mbgp'), ('Все файлы', '.*')])
        if filename != '':
            self.project = Project(filename, self.update_title)
            if not self.project.loaded_ok:
                self.project = None
            else:
                self.update_wnd_state()

    # Сохранить проект
    def save_project(self):
        if self.project.filename is not None:
            self.project.save(self.project.filename)
        else:
            self.save_project_as()

    # Сохранить проект как
    def save_project_as(self):
        filename = filedialog.asksaveasfilename(title='Сохранить проект',
                                                confirmoverwrite=True,
                                                parent=self.master,
                                                defaultextension='.mbgp',
                                                filetypes=[('Проекты генератора модбаса', '.mbgp'), ('Все файлы', '.*')])
        if filename != '':
            self.project.save(filename)


# Инициализация библиотеки Tkinter
root = Tk()
# Создание экземпляра приложения
app = Application(master=root)

# Колбэк для запроса на сохранение
def _quit_callback():
    if app.project is not None and app.project.modified:
        result = messagebox.askyesnocancel('Внимание', 'Сохранить проект перед выходом?', parent=root)
        if result is None:
            # Отмена выхода
            return
        elif result:
            app.save_project()
    root.destroy()

# Регистрируем колбэк
root.protocol('WM_DELETE_WINDOW', _quit_callback)
# Вход в цикл обработки сообщений
app.mainloop()
