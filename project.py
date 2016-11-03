import re
from tkinter import messagebox


# Класс-хелпер, обеспечивающий синхронизацию переменных граф. интерфейса
# с внутренним представлением полей структур
class BoolVar:
    def __init__(self, value=False):
        self.bool = value
        self.tk_var = None

    def set(self, value):
        self.bool = value

    def get(self):
        return self.bool

    def assign(self, tk_variable):
        self.tk_var = tk_variable
        tk_variable.set(self.bool)

        def _callback(*args):
            self.bool = self.tk_var.get()
        tk_variable.trace("w", _callback)


# Класс, описывающий одно поле структуры PC-Worx
class PhoenixField:
    def __init__(self, name='', type='', comment='', exported=True, is_setting=None,
                 is_control=False, is_separate=False):
        self.name = name
        self.type = type
        self.comment = comment
        self.exported = BoolVar(exported)
        self.is_setting = BoolVar(is_setting)
        self.is_control = BoolVar(is_control)
        self.is_separate = BoolVar(is_separate)
        # При создании поля, если не указано явного признака "настройка",
        # то смотрим на префикс имени
        if is_setting is None:
            self.is_setting.set(name.startswith('s_'))
        else:
            self.is_setting.set(is_setting)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return self.name.__hash__()

    def merge_with(self, other):
        self.type = other.type
        self.comment = other.comment


# Класс, описывающий структуру PC-Worx. Содержит список полей PhoenixField
class PhoenixStruct:
    def __init__(self, name='', fields=list()):
        self.name = name
        self.fields = fields

    def __eq__(self, other):
        return self.name == other.name

    # Метод слияния двух структур
    def merge_with(self, other):
        self_set = set(self.fields)
        other_set = set(other.fields)
        added = other_set.difference(self_set)
        deleted = self_set.difference(other_set)
        if len(added) > 0 or len(deleted) > 0:
            text = ''
            for i in added: text += 'Добавлено поле ' + i.name + '\n'
            for i in deleted: text += 'Удалено поле ' + i.name + '\n'
            if messagebox.askyesno('Найдены отличия', text + '\nВнести изменения?'):
                self.fields = list(other_set.intersection(self_set))
                self.fields.extend(list(added))
                self.sort()
        for field in self.fields:
            other_field = other.fields[other.fields.index(field)]
            field.merge_with(other_field)
        return self

    # Метод сортировки полей данной структуры для вывода в таблицу
    def sort(self):
        self.fields.sort(key=lambda f: f.name.lower())


# Класс, описывающий проект. Содержит список структур PC-Worx
class Project:
    def __init__(self, filename=None):
        self.save_path = None
        self.is_modified = False
        self.is_ok = False
        self.structs = list()
        if filename is not None and filename != '':
            self.load(filename)
        else:
            self.is_ok = True

    # Метод загрузки проекта из файла
    def load(self, filename):
        print('Loading', filename)
        self.is_ok = True

    # Метод сохранения проекта в файл
    def save(self, filename):
        print('Saving', filename)

    # Метод, анализирующий входной текст text
    def analyze_input(self, text):
        raw_structs = re.findall('\s(\S+?)\s*:\s*STRUCT(.+?)END_STRUCT;.*?', text, re.MULTILINE and re.DOTALL)
        for struct in raw_structs:
            # Для каждой найденной структуры вызывается отдельный метод
            # для разбиения данной структуры на поля и распознание атрибутов
            new_struct = self.analyze_struct(struct)
            new_struct.sort()
            if new_struct in self.structs:
                # Обработка дубликатов (структур с одинаковым именем)
                if messagebox.askyesno('Внимание',
                                       'Обнаружен дубликат структуры ' + new_struct.name + '. Произвести слияние?'):
                    i = self.structs.index(new_struct)
                    self.structs[i] = self.structs[i].merge_with(new_struct)
            else:
                self.structs.append(new_struct)
        self.structs.sort(key=lambda s: s.name)

    # Метод, анализирующий отдельную структуру из пары pair
    def analyze_struct(self, pair):
        # Первый параметр пары - имя структуры
        struct_name = pair[0].strip()
        field_array = list()
        # Второй параметр пары - текст, содежащий все поля данной структуры
        # Подразумевается, что на каждой строке может быть только одно поле
        raw_fields = pair[1].strip().splitlines()
        for field in raw_fields:
            field = field.strip()
            # Выделение имени поля, его типа, и комментария
            res = re.search('(\S+?)\s*:\s*(\S+?)\s*;\s*(.*)$', field)
            if res is not None:
                comment = res.group(3).strip()
                if comment != '':
                    # Удаление (* *) из текста комментария
                    comment = re.search('^\(\*\s*(.*?)\s*\*\)$', comment).group(1)
                # Добавление нового поля в список полей
                field_array.append(PhoenixField(res.group(1), res.group(2), comment))
        # Создаем и возвращаем новую структуру
        return PhoenixStruct(struct_name, field_array)
