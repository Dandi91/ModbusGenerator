from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Notebook
from structframe import *
from settingsframe import SettingsFrame
from project import PhoenixStruct


class AppNotebook(Notebook):
    def __init__(self, master, project):
        Notebook.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, S, W, E))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.project = project
        self.tab_editor = None
        self.on_tab_change = None
        self.can_edit_tab = False
        self.editor_var = StringVar()
        self.bind('<Double-Button-1>', self._dblclick)
        self.bind('<<NotebookTabChanged>>', self._tab_changed)
        self.update_tabs()

    # Метод обновления вкладок со структурами
    # Вызывается каждый раз при новом анализе структур
    def update_tabs(self):
        if self.project is not None:
            if len(self.tabs()) > 0:
                selected = self.index('current')
            else:
                selected = None
            # Удалить все закладки
            while len(self.tabs()) > 0:
                self.forget(0)
            # Добавить вкладку с настройками
            settings_frame = SettingsFrame(self, self.project)
            self.add(settings_frame, text=settings_frame.tab_name, padding='4px')
            # Добавить нужные согласно project
            singles_frame = SinglesFrame(self, self.project)
            self.add(singles_frame, text=singles_frame.tab_name, padding='4px')
            for struct in self.project.structs:
                struct_frame = StructFrame(self, struct)
                self.add(struct_frame, text=struct_frame.tab_name, padding='4px')
            if selected is not None and len(self.tabs()) > selected:
                self.select(selected)

    # Возвращает индекс вкладки по тексту ярлычка
    def index_by_text(self, tab_text):
        for i in range(len(self.tabs())):
            if self.tab(i, option='text') == tab_text:
                return i
        return -1

    # Возвращает значения для левой и правой границы ярлычка вкладки в пикселях
    def get_tab_position(self, index):
        left = 0
        right = 0
        found = False
        for x in range(self.winfo_width() + 10):
            current_index = -1
            try:
                current_index = self.index('@{},{}'.format(x, 8))
            except TclError:
                pass
            if current_index == index and not found:
                left = x
                found = True
            if current_index != index and found:
                right = x
                break
        return left, right

    # Работа со структурами
    def new_struct(self, event=None):
        if self.project is not None:
            self.project.structs.append(PhoenixStruct(name='Новая структура', callback=self.project.changed))
            self.update_tabs()

    def rename_struct(self, event=None, index=-1):
        if self.project is not None:
            if index == -1:
                index = self.index('current')
            # Не переименовываем служебные табы, только структуры
            if self.tab(index, option='text') not in self.project.structs:
                return
            left, right = self.get_tab_position(index)
            if self.tab_editor is not None:
                self.tab_editor.destroy()
                self.tab_editor = None
            entry = Entry(self.master, textvariable=self.editor_var)
            entry.bind('<Return>', self.confirm_editing)
            entry.bind('<Escape>', self.end_editing)
            entry.place(x=left+2, y=3, width=right-left-4, height=20)
            entry.focus()
            self.tab_editor = entry
            self.editor_var.set(self.tab(index, option='text'))
            entry.select_range(0, END)

    def delete_struct(self):
        if self.project is not None:
            index = self.index('current')
            if index > 0:
                tab_name = self.tab(index, option='text')
                if messagebox.askyesno('Внимание',
                                       'Вы действительно хотите удалить структуру \'{}\'?'.format(tab_name)):
                    struct_index = self.project.structs.index(tab_name)
                    self.project.structs.pop(struct_index)
                    self.project.modified = True
                    self.master.update_title()
                    self.forget(index)

    def end_editing(self, event=None):
        if self.tab_editor is not None:
            self.tab_editor.destroy()
            self.tab_editor = None

    def confirm_editing(self, event=None):
        if self.tab_editor is not None:
            old_text = self.tab('current', option='text')
            new_text = self.editor_var.get()
            if new_text != old_text:
                self.project.structs[self.index('current') - 1].name = new_text
                self.project.modified = True
                self.master.update_title()
                self.tab('current', text=new_text)
            self.end_editing(event)

    def _dblclick(self, event):
        index = -1
        try:
            index = self.index('@{},{}'.format(event.x, event.y))
        except TclError:
            pass
        if index == -1:
            self.new_struct()
        else:
            self.rename_struct()

    def _tab_changed(self, event):
        self.can_edit_tab = self.tab('current', option='text') in self.project.structs
        self.end_editing()
        if self.on_tab_change is not None:
            self.on_tab_change()
