import re
from xml.dom.minidom import getDOMImplementation, parse, Node
from xml.parsers.expat import ExpatError
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

    def set_str(self, value):
        self.bool = value == '1'

    def get_str(self):
        if self.bool: return '1'
        else: return '0'

    def assign(self, tk_variable):
        self.tk_var = tk_variable
        tk_variable.set(self.bool)

        def _callback(*args):
            self.bool = self.tk_var.get()
        tk_variable.trace("w", _callback)


# Функция-хелпер, удаляющая пустые ноды из дерева XML
def remove_blanks(node):
    for x in node.childNodes:
        if x.nodeType == Node.TEXT_NODE:
            if x.nodeValue:
                x.nodeValue = x.nodeValue.strip()
        elif x.nodeType == Node.ELEMENT_NODE:
            remove_blanks(x)


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

    # Метод сериализации поля в XML
    def serialize(self, document):
        field_node = document.createElement('field')
        comment_node = document.createTextNode(self.comment)
        field_node.appendChild(comment_node)
        field_node.setAttribute('name', self.name)
        field_node.setAttribute('type', self.type)
        field_node.setAttribute('export', self.exported.get_str())
        field_node.setAttribute('setting', self.is_setting.get_str())
        field_node.setAttribute('control', self.is_control.get_str())
        field_node.setAttribute('separate', self.is_separate.get_str())
        return field_node

    # Метод де-сериализации (загрузки) поля из XML
    def deserialize(self, node):
        if node.tagName != 'field': return
        self.name = node.getAttribute('name')
        self.type = node.getAttribute('type')
        self.exported.set_str(node.getAttribute('export'))
        self.is_setting.set_str(node.getAttribute('setting'))
        self.is_control.set_str(node.getAttribute('control'))
        self.is_separate.set_str(node.getAttribute('separate'))
        self.comment = node.firstChild.data


# Класс, описывающий структуру PC-Worx. Содержит список полей PhoenixField
class PhoenixStruct:
    def __init__(self, name='', fields=None):
        self.name = name
        if fields is not None:
            self.fields = fields
        else:
            self.fields = list()

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

    # Метод сериализации структуры в XML
    def serialize(self, document):
        struct_node = document.createElement('struct')
        struct_node.setAttribute('name', self.name)
        for field in self.fields:
            node = field.serialize(document)
            struct_node.appendChild(node)
        return struct_node

    # Метод де-сериализации (загрузки) структуры из XML
    def deserialize(self, node):
        if node.tagName != 'struct': return
        self.name = node.getAttribute('name')
        field_node = node.firstChild
        while field_node is not None:
            new_field = PhoenixField()
            new_field.deserialize(field_node)
            self.fields.append(new_field)
            field_node = field_node.nextSibling


# Класс, описывающий проект. Содержит список структур PC-Worx
class Project:
    def __init__(self, filename=None):
        self.structs = list()
        self.loaded_ok = False
        self.filename = None
        if filename is not None and filename != '':
            self.loaded_ok = self.load(filename)

    # Метод загрузки проекта из файла
    def load(self, filename):
        try:
            doc = parse(filename)
        except ExpatError:
            messagebox.showerror('Ошибка', 'Некорректный файл для обработки')
            return False
        root = doc.documentElement
        if root.tagName != 'mbgen_doc': return False
        remove_blanks(root)
        root.normalize()
        node = root.firstChild
        while node is not None:
            new_struct = PhoenixStruct()
            new_struct.deserialize(node)
            self.structs.append(new_struct)
            node = node.nextSibling
        self.filename = filename
        return True

    # Метод сохранения проекта в файл
    def save(self, filename):
        impl = getDOMImplementation()
        doc = impl.createDocument(None, 'mbgen_doc', None)
        root = doc.documentElement
        for struct in self.structs:
            node = struct.serialize(doc)
            root.appendChild(node)
        f = open(filename, 'w', encoding='utf-8')
        f.write(doc.toprettyxml())
        f.close()
        self.filename = filename

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
