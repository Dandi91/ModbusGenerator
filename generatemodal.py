from tkinter import *


# Базовый класс для создания модального диалога
class Dialog(Toplevel):
    def __init__(self, parent, title=None):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = False
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.pack_slaves()
        left = parent.winfo_rootx() + (parent.winfo_width() - 412) / 2
        top = parent.winfo_rooty() + (parent.winfo_height() - 250) / 2
        self.resizable(0, 0)
        self.geometry("+%d+%d" % (left, top))
        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Отмена", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    # standard button semantics
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.result = True
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    # command hooks
    def validate(self):
        return 1  # override

    def apply(self):
        pass  # override


class GeneratorDialog(Dialog):
    def __init__(self, parent, project):
        self.project = project
        self.gen_settings = project.generator_settings
        self.save_settings = project.gen_settings.save_gen_settings.var
        self.variables = dict()
        self.setting_list = list(self.gen_settings.labels.keys())
        self.setting_list.sort()
        for setting in self.setting_list:
            self.variables[setting] = getattr(self.gen_settings, setting).var
        Dialog.__init__(self, parent, 'Настройки генератора')

    def body(self, master):
        current_row = 0

        def create_cb(label, control_var):
            result = Checkbutton(master, text=label, variable=control_var)
            result.grid(column=0, row=current_row, sticky=W)
            return result

        for setting in self.setting_list:
            create_cb(self.gen_settings.labels[setting], self.variables[setting])
            current_row += 1
        create_cb('Больше не спрашивать при генерации', self.save_settings).grid(sticky=SW)
        master.rowconfigure(current_row, minsize='30px')
        return None
