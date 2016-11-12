import re
from xml.dom.minidom import getDOMImplementation, parse, Node
from xml.parsers.expat import ExpatError
from tkinter import messagebox, StringVar, BooleanVar, IntVar
from enum import Enum


# Класс-хелпер, обеспечивающий синхронизацию переменных граф. интерфейса
# с внутренним представлением полей структур
class FieldVar:
    def __init__(self, value, tk_var, callback=None):
        self.var = tk_var
        self.var.set(value)
        self.var.trace("w", self.__callback__)
        self.callback = callback

    def __call__(self, value=None):
        if value is not None:
            self.var.set(value)
        else:
            return self.var.get()

    def __callback__(self, *args):
        if self.callback is not None:
            self.callback()


states = ['Не передавать', 'Показание', 'Настройка', 'Управление', 'Управление с изменением']


class FieldState(Enum):
    dont_trasmit = 0
    indication = 1
    setting = 2
    control = 3
    control_change = 4

    def str(self):
        return states[self.value]


# Класс, описывающий одно поле структуры PC-Worx
class PhoenixField:
    def __init__(self, name='', field_type='', comment='', state=None, callback=None):
        self.name = name                                                    # Иия поля
        self.type = field_type                                              # Тип данных
        self.comment = comment                                              # Комментарий (описание события HMI)
        self.state = FieldVar(state, StringVar(), self.changed)             # Статус переменной
        self.callback = callback
        # При создании поля, если не указано явного статуса, то смотрим на префикс имени
        if state is None:
            name = name.lower()
            if name.startswith('s_') or name.startswith('set_'):
                self.state(FieldState.setting.str())
            elif name.startswith('mnl_'):
                self.state(FieldState.control.str())
            else:
                self.state(FieldState.indication.str())
        else:
            self.state(state)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        else:
            return self.name == other.name

    def __repr__(self):
        return '{}: {} // {}'.format(self.name, self.type, self.comment)

    def __hash__(self):
        return self.name.__hash__()

    def changed(self):
        if self.callback is not None:
            self.callback()

    def merge_with(self, other):
        self.type = other.type
        if other.comment != '':
            self.comment = other.comment

    # Метод сериализации поля в XML
    def serialize(self, document):
        field_node = document.createElement('field')
        comment_node = document.createTextNode(self.comment)
        field_node.appendChild(comment_node)
        field_node.setAttribute('name', self.name)
        field_node.setAttribute('type', self.type)
        field_node.setAttribute('state', self.state())
        return field_node

    # Метод де-сериализации (загрузки) поля из XML
    def deserialize(self, node):
        if node.tagName != 'field':
            return
        self.name = node.getAttribute('name')
        self.type = node.getAttribute('type')
        self.state(node.getAttribute('state'))
        if node.firstChild is not None:
            self.comment = node.firstChild.data


# Класс, описывающий структуру PC-Worx. Содержит список полей PhoenixField и список экземпляров данной структуры
class PhoenixStruct:
    def __init__(self, name='', fields=None, callback=None):
        self.name = name
        self.callback = callback
        self.instances_str = FieldVar('', StringVar(), self.parse_instances)
        self.instance_list = list()
        if fields is not None:
            self.fields = fields
            for field in fields:
                field.callback = self.changed
        else:
            self.fields = list()

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        else:
            return self.name == other.name

    def __repr__(self):
        return self.name

    def changed(self):
        if self.callback is not None:
            self.callback()

    def length(self):
        length = 0
        for field in self.fields:
            length += field.length()
        return length

    def parse_instances(self):
        string = self.instances_str()
        self.instance_list = string.replace(',', ' ').split()
        self.changed()

    # Метод слияния двух структур
    def merge_with(self, other):
        self_set = set(self.fields)
        other_set = set(other.fields)
        added = other_set.difference(self_set)
        deleted = self_set.difference(other_set)
        if len(added) > 0 or len(deleted) > 0:
            text = ''
            for i in added:
                text += 'Добавлено поле ' + i.name + '\n'
            for i in deleted:
                text += 'Удалено поле ' + i.name + '\n'
            if messagebox.askyesno('Найдены отличия', text + '\nВнести изменения?'):
                self.fields = list(other_set.intersection(self_set))
                self.fields.extend(list(added))
                self.sort()
        for field in self.fields:
            other_field = other.fields[other.fields.index(field)]
            field.merge_with(other_field)
            field.callback = self.changed
        return self

    # Метод сортировки полей данной структуры для вывода в таблицу
    def sort(self):
        self.fields.sort(key=lambda f: f.name.lower())

    # Метод сериализации структуры в XML
    def serialize(self, document):
        struct_node = document.createElement('struct')
        struct_node.setAttribute('name', self.name)
        instances_node = document.createElement('instances')
        instances_text = document.createTextNode(','.join(self.instance_list))
        instances_node.appendChild(instances_text)
        struct_node.appendChild(instances_node)
        for field in self.fields:
            node = field.serialize(document)
            struct_node.appendChild(node)
        return struct_node

    # Метод де-сериализации (загрузки) структуры из XML
    def deserialize(self, node):
        if node.tagName != 'struct':
            return
        self.name = node.getAttribute('name')
        instances_node = node.firstChild
        if instances_node.tagName == 'instances':
            if instances_node.hasChildNodes():
                text = instances_node.firstChild.data.replace(',,', ',')
                self.instance_list = text.split(',')
                self.instances_str(','.join(self.instance_list))
            field_node = instances_node.nextSibling
        else:
            field_node = instances_node
        while field_node is not None:
            new_field = PhoenixField()
            new_field.deserialize(field_node)
            self.fields.append(new_field)
            new_field.callback = self.changed
            field_node = field_node.nextSibling


class GeneratorSettings:
    labels = {
        'pcworx_modbus': 'Генерировать код для Modbus сервера в PCWorx',
        'weintek_tags': 'Генерировать файл для импорта адресных меток в Weintek',
        'weintek_events': 'Генерировать файл для импорта событий в Weintek',
        'pcworx_structures': 'Генерировать код для импорта структур и переменных в PCWorx',
        'webvisit': 'Генерировать файл для импорта в WebVisit'
    }

    def __init__(self, callback):
        # Настройки вывода
        self.save_gen_settings = FieldVar(False, BooleanVar(), callback)
        self.pcworx_modbus = FieldVar(True, BooleanVar(), callback)
        self.weintek_tags = FieldVar(True, BooleanVar(), callback)
        self.weintek_events = FieldVar(True, BooleanVar(), callback)
        self.pcworx_structures = FieldVar(True, BooleanVar(), callback)
        self.webvisit = FieldVar(True, BooleanVar(), callback)
        # Общие настройки
        self.mb_arr_name = FieldVar('MB_Data_HMI', StringVar(), callback)
        self.mb_cursor_name = FieldVar('MBcurrPos', StringVar(), callback)
        self.plc_name = FieldVar('PLC', StringVar(), callback)
        self.start_address = FieldVar(1, IntVar(), callback)
        self.gen_save = FieldVar(False, BooleanVar(), callback)
        self.gen_save_word = FieldVar(0, IntVar(), callback)
        self.gen_save_bit = FieldVar(0, IntVar(), callback)
        self.gen_cancel = FieldVar(False, BooleanVar(), callback)
        self.gen_cancel_word = FieldVar(0, IntVar(), callback)
        self.gen_cancel_bit = FieldVar(1, IntVar(), callback)
        # Пути файлов для экспорта
        self.weintek_tag_file = FieldVar('', StringVar(), callback)
        self.weintek_event_file = FieldVar('', StringVar(), callback)
        self.webvisit_file = FieldVar('', StringVar(), callback)

    # Метод сериализации настроек в XML
    def serialize(self, document):
        settings_node = document.createElement('settings')
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, FieldVar):
                new_node = document.createElement('setting')
                new_node.setAttribute('name', attr_name)
                node_text = document.createTextNode(str(attr()))
                new_node.appendChild(node_text)
                settings_node.appendChild(new_node)
        return settings_node

    # Метод де-сериализации (загрузки) настроек из XML
    def deserialize(self, node):
        if node.tagName != 'settings':
            return
        setting = node.firstChild
        while setting is not None:
            if setting.tagName == 'setting':
                attr_name = setting.getAttribute('name')
                if hasattr(self, attr_name):
                    attr = getattr(self, attr_name)
                    if isinstance(attr, FieldVar) and setting.hasChildNodes():
                        attr(setting.firstChild.data)
            setting = setting.nextSibling


# Класс, описывающий проект. Содержит список структур PC-Worx, а также настройки генератора
class Project:
    def __init__(self, filename=None, callback=None):
        self.structs = list()
        self.singles = list()
        self.loaded_ok = False
        self.filename = None
        self.modified = False
        self.callback = callback
        self.generator_settings = GeneratorSettings(self.changed)
        if filename is not None and filename != '':
            self.loaded_ok = self.load(filename)
            self.modified = not self.loaded_ok
        self.notify()

    def changed(self):
        self.modified = True
        self.notify()

    def notify(self):
        if self.callback is not None:
            self.callback()

    # Метод загрузки проекта из файла
    def load(self, filename):
        try:
            doc = parse(filename)
        except ExpatError:
            messagebox.showerror('Ошибка', 'Некорректный файл для обработки')
            return False
        root = doc.documentElement
        if root.tagName != 'mbgen_doc':
            return False
        self.remove_blanks(root)
        root.normalize()
        struct_node = root.getElementsByTagName('structs')[0]
        singles_node = root.getElementsByTagName('singles')[0]
        settings_node = root.getElementsByTagName('settings')[0]
        node = struct_node.firstChild
        while node is not None:
            new_struct = PhoenixStruct(callback=self.changed)
            new_struct.deserialize(node)
            self.structs.append(new_struct)
            node = node.nextSibling
        node = singles_node.firstChild
        while node is not None:
            new_field = PhoenixField(callback=self.changed)
            new_field.deserialize(node)
            self.singles.append(new_field)
            node = node.nextSibling
        self.generator_settings.deserialize(settings_node)
        self.filename = filename
        return True

    # Метод сохранения проекта в файл
    def save(self, filename):
        impl = getDOMImplementation()
        doc = impl.createDocument(None, 'mbgen_doc', None)
        root = doc.documentElement
        struct_node = doc.createElement('structs')
        root.appendChild(struct_node)
        for struct in self.structs:
            node = struct.serialize(doc)
            struct_node.appendChild(node)
        singles_node = doc.createElement('singles')
        root.appendChild(singles_node)
        for single in self.singles:
            node = single.serialize(doc)
            singles_node.appendChild(node)
        root.appendChild(self.generator_settings.serialize(doc))
        f = open(filename, 'w', encoding='utf-8')
        f.write(doc.toprettyxml())
        f.close()
        self.filename = filename
        self.modified = False
        self.notify()

    # Метод, анализирующий входной текст text
    def analyze_input(self, text):
        text = self.fix_encoding(text)
        text = self.analyze_singles(text)
        raw_structs = re.findall('\s(\S+?)\s*:\s*STRUCT(.+?)END_STRUCT;.*?', text, re.MULTILINE and re.DOTALL)
        for struct in raw_structs:
            # Для каждой найденной структуры вызывается отдельный метод
            # для разбиения данной структуры на поля и распознание атрибутов
            new_struct = self.analyze_struct(struct)
            new_struct.sort()
            new_struct.callback = self.changed
            if new_struct in self.structs:
                # Обработка дубликатов (структур с одинаковым именем)
                if messagebox.askyesno('Внимание',
                                       'Обнаружен дубликат структуры ' + new_struct.name + '. Произвести слияние?'):
                    i = self.structs.index(new_struct)
                    self.structs[i] = self.structs[i].merge_with(new_struct)
                    self.modified = True
            else:
                self.structs.append(new_struct)
                self.modified = True
        self.structs.sort(key=lambda s: s.name)

    # Метод анализирующий отдельные переменные
    def analyze_singles(self, text):
        lines = text.strip().splitlines()
        result = list()
        for line in lines:
            line = line.strip()
            if line.find('VAR_GLOBAL') > -1:
                fields = re.search('^(\S+)\s+(\S+)\s+VAR_GLOBAL\s+(.*)$', line)
                var_name = fields.group(1)
                if var_name in self.singles:
                    if messagebox.askyesno('Внимание',
                                           'Глобальная переменная {} уже существует. Заменить новой?'.format(var_name)):
                        self.singles.remove(var_name)
                    else:
                        continue
                self.singles.append(PhoenixField(fields.group(1), fields.group(2), fields.group(3)))
                self.modified = True
            else:
                result.append(line)
        self.singles.sort(key=lambda f: f.name)
        return '\n'.join(result)

    @staticmethod
    # Метод, анализирующий отдельную структуру из пары pair
    def analyze_struct(pair):
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

    @staticmethod
    # Функция-хелпер, удаляющая пустые ноды из дерева XML
    def remove_blanks(node):
        for x in node.childNodes:
            if x.nodeType == Node.TEXT_NODE:
                if x.nodeValue:
                    x.nodeValue = x.nodeValue.strip()
            elif x.nodeType == Node.ELEMENT_NODE:
                Project.remove_blanks(x)

    @staticmethod
    # Функция преобразования кракозябр из PC-Worx'а
    # Если во входной строке попадаются корректные русские символы,
    # то возвращает исходный текст вне зависимости от наличия кракозябр в нем
    def fix_encoding(text):
        try:
            return text.encode('cp1252').decode('cp1251')
        except UnicodeEncodeError:
            return text
