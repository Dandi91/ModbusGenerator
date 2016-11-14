from modbusgenerator import ModbusGenerator, type_size
from hmigenerator import HMIGenerator
from webvisitgenerator import WebVisitGenerator
from project import PhoenixStruct, FieldState


# Класс набор полей определенной структуры
# Умеет фильтровать поля структуры согласно переданному предикату predicate
class FieldSet:
    def __init__(self, struct, predicate):
        self.predicate = predicate
        self.original = None
        if isinstance(struct, list):
            self.var_list = struct
        else:
            self.var_list = struct.fields
            self.original = struct
        self.filtered = list()
        self.filter()
        self.sort()

    # Метод, фильтрующий поля структуры согласно предикату
    def filter(self):
        if self.predicate is not None:
            for field in self.var_list:
                if self.predicate(field):
                    self.filtered.append(field)

    # Метод, сортирующий поля по алфавиту и складывающий битовые поля в начало списка
    def sort(self):
        self.filtered.sort(key=lambda field: field.name.lower())
        self.filtered.sort(key=lambda field: field.type.lower() != 'bool')


# Адресная метка - присваивает область памяти конкретной переменной в конкретном экземпляре структуры
class AddressTag:
    def __init__(self, address, bit, instance, field):
        self.address = address
        self.bit = bit
        self.instance = instance
        self.field = field
        self.size = type_size[field.type.lower()]

    def get_name(self):
        if self.instance != '':
            name = self.instance + '.' + self.field.name
        else:
            name = self.field.name
        return name

    def get_description(self):
        device_prefixes = ('SENS_', 'VLV_', 'PMP_', 'REG_')
        device_name = self.instance
        comment = self.field.comment
        if device_name == '':
            return comment
        for prefix in device_prefixes:
            if device_name.startswith(prefix):
                device_name = device_name.replace(prefix, '')
                break
        if comment.count('{}') < 1:
            comment = '{} - ' + comment
        return comment.format(device_name)


# Адресное пространство - коллекция адресных меток, принадлежащих к одному типу структур
class AddressSpace:
    def __init__(self, fields, first_address, instances=''):
        self.total_length = 0
        self.single_length = 0
        self.first_address = first_address
        self.current_address = first_address
        self.instances = list()
        if instances == '':
            tags, self.total_length = self.generate(fields, instances)
            self.single_length = self.total_length
            self.instances.append(tags)
        elif isinstance(instances, list):
            for instance in instances:
                tags, self.single_length = self.generate(fields, instance)
                self.instances.append(tags)
            self.total_length = self.single_length * len(instances)

    def generate(self, fields, instance):
        tags = list()
        begin = self.current_address
        bit_counter = 0
        for field in fields:
            type_name = field.type.lower()
            current_bit = 0
            if type_name == 'bool':
                current_bit = bit_counter
            elif bit_counter > 0:
                self.current_address += 1
                bit_counter = 0
            tag = AddressTag(self.current_address, current_bit, instance, field)
            tags.append(tag)
            if type_name == 'bool':
                bit_counter += 1
                if bit_counter > 15:
                    bit_counter = 0
                    self.current_address += 1
            else:
                self.current_address += tag.size
        if bit_counter > 0:
            self.current_address += 1
        return tags, self.current_address - begin


class Generator:
    def __init__(self, project):
        self.project = project
        self.settings = project.settings
        self.addr_spaces = list()

    def generate_address_space(self):
        address = self.settings.start_address()
        structs = list(self.project.structs)
        structs.append(self.project.singles)
        for struct in structs:
            fields = FieldSet(struct, lambda f: f.state() != FieldState.dont_trasmit.str())
            if isinstance(struct, PhoenixStruct):
                instance_list = struct.instance_list
            else:
                instance_list = ''
            if len(fields.filtered) > 0:
                addr_space = AddressSpace(fields.filtered, address, instance_list)
                address += addr_space.total_length
                self.addr_spaces.append(addr_space)

    def gen_pcworx_mb(self):
        gen = ModbusGenerator(self)
        variables, types = gen.generate_vars()
        return gen.get_mb_code(), variables, types

    def gen_weintek(self):
        gen = HMIGenerator(self)
        gen.generate()

    def gen_webvisit(self):
        gen = WebVisitGenerator(self)
        gen.generate()
