from project import PhoenixStruct, FieldState


# 0 - имя массива Modbus
# 1 - имя переменной-указателя для массива Modbus
# 2 - номер бита в слове для битовых переменных
# 3 - имя массива структур для обработки
# 4 - имя поля в структуре
templates_to_mb = {
    'bool':  '{0}[{1}].X{2} := {3}{4};',
    'real':  '{0}[{1}] := REAL_TO_WORD({3}{4} * 100.0);',
    'int':   '{0}[{1}] := INT_TO_WORD({3}{4});',
    'dint':  'TempDword := DINT_TO_DWORD({3}{4}); {0}[{1}] := TempDword.W0;{5} {0}[{6}] := TempDword.W1;',
    'time':  '{0}[{1}] := DINT_TO_WORD(TIME_TO_DINT({3}{4}) / DINT#1000);',
    'word':  '{0}[{1}] := {3}{4};',
    'dword': '{0}[{1}] := {3}{4}.W0;{5} {0}[{6}] := {3}{4}.W1;'
}
templates_to_plc = {
    'bool':  '{3}{4} := {0}[{1}].X{2};',
    'real':  '{3}{4} := WORD_TO_REAL({0}[{1}]) / 100.0;',
    'int':   '{3}{4} := WORD_TO_INT({0}[{1}]);',
    'dint':  'TempDword.W0 := {0}[{1}];{5} TempDword.W1 := {0}[{6}]; {3}{4} := DWORD_TO_DINT(TempDword);',
    'time':  '{3}{4} := DINT_TO_TIME(WORD_TO_DINT({0}[{1}]) * DINT#1000)',
    'word':  '{3}{4} := {0}[{1}];',
    'dword': '{3}{4}.W0 := {0}[{1}];{5} {3}{4}.W1 := {0}[{6}];'
}
template_bidir = 'if {0} <> {1}{2} then\n{3}\nelse\n{4}\nend_if;\n{0} := {1}{2};'
templates_hmi = {
    'bool':  ('4x_Bit', 'Undesignated'),
    'real':  ('4x', 'Undesignated'),
    'int':   ('4x', 'Undesignated'),
    'dint':  ('4x', '32-bit SIGNED'),
    'time':  ('4x', 'Undesignated'),
    'word':  ('4x', 'Undesignated'),
    'dword': ('4x', '32-bit UNSIGNED')
}
# Приращение курсора при относительной адресации
cursor_advance = {
    'bool':  0,
    'real':  1,
    'int':   1,
    'dint':  1,
    'time':  1,
    'word':  1,
    'dword': 1
}
# Приращение курсора при абсолютной адресации
type_size = {
    'bool':  0,
    'real':  1,
    'int':   1,
    'dint':  2,
    'time':  1,
    'word':  1,
    'dword': 2
}


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


class AddressTag:
    def __init__(self, address, bit, instance, field):
        self.address = address
        self.bit = bit
        self.instance = instance
        self.field = field
        self.size = type_size[field.type.lower()]

    def generate_hmi_tag(self, plc_name):
        type_name = self.field.type.lower()
        hmi_params = templates_hmi[type_name]
        if type_name == 'bool':
            hmi_address = self.address * 100 + self.bit
        else:
            hmi_address = self.address
        instance_name = self.instance
        if self.instance != '':
            instance_name += '.'
        return '{}{},{},{},{},,{}'.format(instance_name, self.field.name, plc_name,
                                          hmi_params[0], hmi_address, hmi_params[1])

    def __repr__(self):
        return '{} @ {}.{}'.format(self.field.name, self.address, self.bit)


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


class Skeleton:
    def __init__(self, generator, struct, address_space):
        self.generator = generator
        self.struct = struct
        self.address_space = address_space
        self.tag_list = address_space.instances[0]
        self.num_instances = 0
        self.restore = list()
        self.settings = list()
        self.indication = list()
        self.phoenix_vars = list()
        self.phoenix_type_names = list()
        self.phoenix_type_decls = list()
        self.generate()

    def generate(self):
        # Подсчет количества экземпляров
        if isinstance(self.struct, PhoenixStruct):
            self.num_instances = len(self.struct.instance_list)
        else:
            self.num_instances = 1
        # Лупить только при надобности
        do_loop = self.num_instances > 1
        # Разделить переменные по назначению
        settings, indication = self.separate_tags()
        section_list = list()
        section_list.append(self.settings)
        section_list.append(self.restore)
        self.generate_code(settings, do_loop, section_list, False)
        section_list.clear()
        section_list.append(self.indication)
        self.generate_code(indication, do_loop, section_list, True)
        # Добавить цикл для пакетной обработки
        if do_loop:
            loop_begin = 'for i := 1 to {} do'.format(self.num_instances)
            loop_end = 'end_if;'
            if len(settings) > 0:
                self.restore.insert(1, loop_begin)
                self.settings.insert(1, loop_begin)
                self.restore.append(loop_end)
                self.settings.append(loop_end)
            if len(indication) > 0:
                self.indication.insert(1, loop_begin)
                self.indication.append(loop_end)
        self.generate_locals()

    def generate_code(self, tag_list, do_loop, lists_to_append, is_indication_section):
        # Строковые шаблоны для удобства
        advance_template = '{0} := {0} + '.format(self.generator.settings.mb_cursor_name()) + '{};'
        advance_by_one = ' ' + advance_template.format(1)
        ptr_jump = self.generator.settings.mb_cursor_name() + ' := {};'

        def append_advance(addr_diff):
            if addr_diff > 0 and do_loop:
                # Разница из-за 32-битных типов и приращений курсора внутри шаблонов
                relative_diff = type_size[type_name] - cursor_advance[type_name]
                addr_diff -= relative_diff
                advance = advance_template.format(addr_diff)
                for l in lists_to_append:
                    l.append(advance)

        # Определить имя структуры
        struct_name = ''
        if do_loop:
            struct_name = self.get_array_name(self.struct) + '[i].'
        # Для каждого тэга нагенерить код
        if len(tag_list) > 0:
            first_address = tag_list[0].address
            if do_loop:
                for l in lists_to_append:
                    l.append(ptr_jump.format(first_address))
            prev_address = first_address
            for tag in tag_list:
                addr_diff = tag.address - prev_address
                prev_address = tag.address
                append_advance(addr_diff)
                type_name = tag.field.type.lower()
                if do_loop:
                    cursor = self.generator.settings.mb_cursor_name()
                    custom_advance = advance_by_one
                    second_cursor = cursor
                else:
                    cursor = str(tag.address)
                    custom_advance = ''
                    second_cursor = str(tag.address + 1)
                params = (self.generator.settings.mb_arr_name(), cursor, tag.bit, struct_name,
                          tag.field.name, custom_advance, second_cursor)
                to_mb = templates_to_mb[type_name].format(*params)
                to_plc = templates_to_plc[type_name].format(*params)
                if is_indication_section:
                    field_state = tag.field.state()
                    if field_state == FieldState.control.str():
                        self.indication.append(to_plc)
                    elif field_state == FieldState.control_change.str():
                        old_var = self.get_old_var_name(tag.field.name, do_loop, type_name)
                        line = template_bidir.format(old_var, struct_name, tag.field.name, to_mb, to_plc)
                        self.indication.append(line)
                    else:
                        self.indication.append(to_mb)
                else:
                    self.restore.append(to_mb)
                    self.settings.append(to_plc)
            # Определить сдвиг между экземплярами структур
            addr_diff = self.address_space.single_length - (prev_address - first_address)
            append_advance(addr_diff)

    def separate_tags(self):
        settings = list()
        indication = list()
        for tag in self.tag_list:
            if tag.field.state() == FieldState.setting.str():
                settings.append(tag)
            else:
                indication.append(tag)
        return settings, indication

    def get_old_var_name(self, field_name, indexed, type_name):
        var_decl_template = '{}\t{}\tVAR\t{}'
        array_decl_template = '\t{}: ARRAY [1..{}] of {}; (* {} *)'
        old_name = field_name + 'Old'
        if isinstance(self.struct, PhoenixStruct):
            old_name += self.struct.name
        old_name = self.shorten_var_name(old_name)
        if indexed:
            comment = 'Массив старых значений ' + field_name
            arr_type_name = 'ArrOf' + type_name.capitalize() + self.struct.name
            self.phoenix_vars.append(var_decl_template.format(old_name, arr_type_name, comment))
            if arr_type_name not in self.phoenix_type_names:
                self.phoenix_type_names.append(arr_type_name)
                new_array = array_decl_template.format(arr_type_name, self.num_instances, type_name.upper(), comment)
                self.phoenix_type_decls.append(new_array)
            old_name += '[i]'
        else:
            new_var = var_decl_template.format(old_name, type_name.upper(), 'Старое значение ' + field_name)
            self.phoenix_vars.append(new_var)
        return old_name

    def generate_locals(self):
        var_decl_template = '{}\t{}\tVAR\t{}'
        array_decl_template = '\t{}: ARRAY [1..{}] of {}; (* {} *)'
        if self.num_instances > 1:
            name = self.struct.name
            vars = var_decl_template.format(self.get_array_name(self.struct), self.get_array_type_name(self.struct),
                                            'Обработка массивом прототипов структур ' + name)
            types = array_decl_template.format(self.get_array_type_name(self.struct), self.num_instances,
                                               name, 'Массив для групповой обработки прототипов структуры ' + name)
            self.phoenix_vars.append(vars)
            self.phoenix_type_decls.append(types)

    @staticmethod
    def get_array_name(struct):
        return Skeleton.shorten_var_name(struct.name + '_Arr')

    @staticmethod
    def shorten_var_name(name):
        max_name_length = 30
        vowels = ('a', 'e', 'i', 'o', 'y', 'u')
        if len(name) > max_name_length:
            name.capwords('_')
            name.replace('_', '')
            if len(name) > max_name_length:
                for vowel in vowels:
                    name.replace(vowel, '')
                if len(name) > max_name_length:
                    name = name[0:max_name_length]
        return name

    @staticmethod
    def get_array_type_name(struct):
        return 'Arr_' + struct.name

    @staticmethod
    def format_code(text):
        lines = text.splitlines()
        result = list()
        num_tabs = 0
        for line in lines:
            line = line.strip()
            line_low = line.lower()
            if line_low.startswith('end_if') or line_low.startswith('end_for'):
                num_tabs -= 1
            if line_low.startswith('else'):
                res_line = '\t' * (num_tabs - 1) + line
            else:
                res_line = '\t' * num_tabs + line
            if line_low.startswith('if') or line_low.startswith('for'):
                num_tabs += 1
            result.append(res_line)
        return '\n'.join(result)


class Generator:
    def __init__(self, project):
        self.project = project
        self.settings = project.settings
        self.addr_spaces = list()
        self.skeletons = list()

    def generate_all(self):
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
                self.skeletons.append(Skeleton(self, struct, addr_space))

    def generate_inout(self):
        in_code = ''
        out_code = ''
        for struct in self.project.structs:
            if len(struct.instance_list) > 1:
                index = 1
                for instance in struct.instance_list:
                    in_code += '{0}[{1}] := {2};\n'.format(Skeleton.get_array_name(struct), index, instance)
                    out_code += '{2} := {0}[{1}];\n'.format(Skeleton.get_array_name(struct), index, instance)
                    index += 1
        return in_code, out_code

    def generate_locals(self):
        code_vars = 'i\tINT\tVAR\tСчетчик для циклов\n'
        code_vars += '{}\tINT\tVAR\tУказатель позиции регистра Modbus\n'.format(self.settings.mb_cursor_name())
        types = ''
        for skeleton in self.skeletons:
            if len(skeleton.phoenix_vars) > 0:
                code_vars += '\n'.join(skeleton.phoenix_vars) + '\n'
            if len(skeleton.phoenix_type_decls) > 0:
                types += '\n'.join(skeleton.phoenix_type_decls) + '\n'
        types = 'TYPE\n' + types + 'END_TYPE\n'
        return code_vars, types

    def get_mb_code(self):
        restore = list()
        settings = list()
        indication = list()
        for skeleton in self.skeletons:
            restore.extend(skeleton.restore)
            settings.extend(skeleton.settings)
            indication.extend(skeleton.indication)
        if self.settings.gen_cancel():
            restore.insert(0, 'if Restore or {}[{}].X{} then'.format(self.settings.mb_arr_name(),
                                                                     self.settings.gen_cancel_word(),
                                                                     self.settings.gen_cancel_bit()))
        else:
            restore.insert(0, 'if Restore then')
        restore.append('end_if;')
        if self.settings.gen_save():
            settings.insert(0, 'if {}[{}].X{} then'.format(self.settings.mb_arr_name(), self.settings.gen_save_word(),
                                                           self.settings.gen_save_bit()))
            settings.append('end_if;')
        result = '(* --------- Восстановление настроек в Modbus после перезапуска ПЛК --------- *)\n'
        result += '\n'.join(restore) + '\n'
        result += '\n\n(* --------------------- Прием настроек в ПЛК из Modbus --------------------- *)\n'
        result += '\n'.join(settings) + '\n'
        result += '\n\n(* -------------------- Работа с показаниями и командами -------------------- *)\n'
        result += '\n'.join(indication) + '\n'
        in_code, out_code = self.generate_inout()
        result = in_code + '\n\n' + result + '\n\n' + out_code + 'Restore := false;\n'
        return Skeleton.format_code(result)

    def get_hmi_tags(self):
        for addr_space in self.addr_spaces:
            for instance in addr_space.instances:
                for tag in instance:
                    return tag.generate_hmi_tag(self.settings.plc_name())
