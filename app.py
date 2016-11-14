from tkinter.ttk import *
from tkinter import filedialog, messagebox
from notebook import AppNotebook
from outputframe import *
from project import Project
from generator import Generator
from generatemodal import GeneratorDialog
from international import bind_int


# Колбэк для запроса на сохранение
def quit_callback(event=None):
    if app.project is not None and app.project.modified:
        result = messagebox.askyesnocancel('Внимание', 'Сохранить проект перед выходом?', parent=root)
        if result is None:
            # Отмена выхода
            return
        elif result:
            app.save_project()
    root.destroy()


# Главный класс приложения - реализует окно верхнего уровня
# с меню и компонентом для закладок
class Application(Frame):
    title = 'Генератор модбаса v0.6'

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
        self.struct_menu = None
        self.notebook = None
        self.input_frame = None
        bind_int('<Control-v>', self.bind_all, self.paste)

        self.create_menus()
        self.update_wnd_state()

    # Метод создания пунктов меню
    def create_menus(self):
        main_menu = Menu(self.master)
        self.file_menu = Menu(main_menu, tearoff=0)
        self.file_menu.add_command(label='Новый проект', command=self.new_project, accelerator='Ctrl+N')
        bind_int('<Control-n>', self.bind_all, self.new_project)
        self.file_menu.add_command(label='Открыть проект...', command=self.open_project, accelerator='Ctrl+O')
        bind_int('<Control-o>', self.bind_all, self.open_project)
        self.file_menu.add_command(label='Сохранить проект', command=self.save_project, accelerator='Ctrl+S')
        bind_int('<Control-s>', self.bind_all, self.save_project)
        self.file_menu.add_command(label='Сохранить проект как...', command=self.save_project_as,
                                   accelerator='Ctrl+Shift+S')
        bind_int('<Control-S>', self.bind_all, self.save_project_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Выйти', command=quit_callback, accelerator='Ctrl+Q')
        bind_int('<Control-q>', self.bind_all, quit_callback)
        main_menu.add_cascade(label='Файл', menu=self.file_menu)

        self.proj_menu = Menu(main_menu, tearoff=0)
        self.proj_menu.add_command(label='Распознать события', command=self.detect_events)
        self.proj_menu.add_command(label='Генерировать', command=self.generate, accelerator='Ctrl+G')
        bind_int('<Control-g>', self.bind_all, self.generate)
        self.proj_menu.add_command(label='Настройки генератора...', command=self.generation_settings)
        main_menu.add_cascade(label='Проект', menu=self.proj_menu)

        self.struct_menu = Menu(main_menu, tearoff=0)
        self.struct_menu.add_command(label='Добавить', command=self.new_struct)
        self.struct_menu.add_command(label='Переименовать', command=self.rename_struct)
        self.struct_menu.add_command(label='Удалить', command=self.delete_struct)
        main_menu.add_cascade(label='Структуры', menu=self.struct_menu)

        self.master.config(menu=main_menu)

    def new_struct(self, event=None):
        if self.notebook is not None:
            self.notebook.new_struct()

    def rename_struct(self, event=None):
        if self.notebook is not None:
            self.notebook.rename_struct()

    def delete_struct(self, event=None):
        if self.notebook is not None:
            self.notebook.delete_struct()

    # Процедура обновления состояний меню и окна
    def update_wnd_state(self):
        if self.project is None:
            if self.notebook is not None:
                self.notebook.destroy()
                self.notebook = None
        else:
            selected_tab = None
            if self.notebook is not None:
                selected_tab = self.notebook.index('current')
                self.notebook.destroy()
            self.notebook = AppNotebook(self, self.project)
            self.notebook.on_tab_change = self.update_menu_state
            if selected_tab is not None:
                self.notebook.select(selected_tab)
        self.update_title()
        self.update_menu_state()

    # Метод обновления состояния пунктов меню
    def update_menu_state(self):
        if self.project is None:
            self.file_menu.entryconfigure(2, state=DISABLED)
            self.file_menu.entryconfigure(3, state=DISABLED)
            self.proj_menu.entryconfigure(0, state=DISABLED)
            self.proj_menu.entryconfigure(1, state=DISABLED)
            self.proj_menu.entryconfigure(2, state=DISABLED)
            self.struct_menu.entryconfigure(0, state=DISABLED)
            self.struct_menu.entryconfigure(1, state=DISABLED)
            self.struct_menu.entryconfigure(2, state=DISABLED)
        else:
            self.file_menu.entryconfigure(2, state=NORMAL)
            self.file_menu.entryconfigure(3, state=NORMAL)
            self.proj_menu.entryconfigure(0, state=NORMAL)
            self.proj_menu.entryconfigure(1, state=NORMAL)
            self.proj_menu.entryconfigure(2, state=NORMAL)
            self.struct_menu.entryconfigure(0, state=NORMAL)
            if self.notebook is not None:
                if self.notebook.can_edit_tab:
                    self.struct_menu.entryconfigure(1, state=NORMAL)
                    self.struct_menu.entryconfigure(2, state=NORMAL)
                else:
                    self.struct_menu.entryconfigure(1, state=DISABLED)
                    self.struct_menu.entryconfigure(2, state=DISABLED)

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
    def new_project(self, event=None):
        if self.project is not None and self.project.modified:
            result = messagebox.askyesnocancel('Внимание', 'Сохранить текущий проект?', parent=self.master)
            if result is None:
                return
            elif result:
                self.save_project()
        self.project = Project(callback=self.update_title)
        self.update_wnd_state()

    # Открыть проект
    def open_project(self, event=None):
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
    def save_project(self, event=None):
        if self.project is not None:
            if self.project.filename is not None:
                self.project.save(self.project.filename)
            else:
                self.save_project_as()

    # Сохранить проект как
    def save_project_as(self, event=None):
        if self.project is not None:
            filename = filedialog.asksaveasfilename(title='Сохранить проект',
                                                    confirmoverwrite=True,
                                                    parent=self.master,
                                                    defaultextension='.mbgp',
                                                    filetypes=[('Проекты генератора модбаса', '.mbgp'),
                                                               ('Все файлы', '.*')])
            if filename != '':
                self.project.save(filename)

    # Генерировать код
    def generate(self, event=None):

        def generate_impl():
            gen = Generator(self.project)
            gen.generate_address_space()
            tab = self.notebook.index_by_text(MBOutputFrame.tab_name)
            while tab > -1:
                self.notebook.forget(tab)
                tab = self.notebook.index_by_text(MBOutputFrame.tab_name)
            if self.project.settings.pcworx_modbus():
                # Добавить вкладку с выводом
                output = MBOutputFrame(self.notebook, gen)
                self.notebook.add(output, text=output.tab_name, padding='4px')
                self.notebook.select(len(self.notebook.tabs()) - 1)
            if self.project.settings.pcworx_structures():
                pass
                # Добавить вкладку с выводом
                # tab = self.notebook.index_by_text(MBOutputFrame.tab_name)
                # if tab > -1:
                #     self.notebook.forget(tab)
                # output = MBOutputFrame(self.notebook, gen)
                # self.notebook.add(output, text=output.tab_name, padding='4px')
                # self.notebook.select(len(self.notebook.tabs()) - 1)
            if self.project.settings.weintek():
                gen.gen_weintek()
            if self.project.settings.webvisit():
                gen.gen_webvisit()

        if self.project is not None:
            if not self.project.settings.save_gen_settings():
                dlg = GeneratorDialog(self, self.project)
                if dlg.result:
                    generate_impl()
            else:
                generate_impl()

    def paste(self, event):
        if self.project is not None:
            self.project.analyze_input(self.clipboard_get())
            self.update_wnd_state()

    def generation_settings(self, event=None):
        GeneratorDialog(self, self.project, False)

    def detect_events(self, event=None):
        if self.project is not None:
            self.project.detect_events()


# Инициализация библиотеки Tkinter
root = Tk()
# Создание экземпляра приложения
app = Application(master=root)
# Регистрируем колбэк
root.protocol('WM_DELETE_WINDOW', quit_callback)
# Вход в цикл обработки сообщений
app.mainloop()
