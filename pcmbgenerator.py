from project import FieldState, PhoenixStruct


# 0 - имя массива Modbus
# 1 - имя переменной-указателя для массива Modbus
# 2 - номер бита в слове для битовых переменных
# 3 - имя массива структур для обработки
# 4 - имя поля в структуре
templates_to_mb = {
    'bool':  '{0}[{1}].X{2} := {3}{4};\n',
    'real':  '{0}[{1}] := REAL_TO_WORD({3}{4} * 100.0);\n',
    'int':   '{0}[{1}] := INT_TO_WORD({3}{4});\n',
    'dint':  'TempDword := DINT_TO_DWORD({3}{4}); {0}[{1}] := TempDword.W0;{5} {0}[{6}] := TempDword.W1;\n',
    'time':  '{0}[{1}] := DINT_TO_WORD(TIME_TO_DINT({3}{4}) / DINT#1000);\n',
    'word':  '{0}[{1}] := {3}{4};\n',
    'dword': '{0}[{1}] := {3}{4}.W0;{5} {0}[{6}] := {3}{4}.W1;\n'
}
templates_to_plc = {
    'bool':  '{3}{4} := {0}[{1}].X{2};\n',
    'real':  '{3}{4} := WORD_TO_REAL({0}[{1}]) / 100.0;\n',
    'int':   '{3}{4} := WORD_TO_INT({0}[{1}]);\n',
    'dint':  'TempDword.W0 := {0}[{1}];{5} TempDword.W1 := {0}[{6}]; {3}{4} := DWORD_TO_DINT(TempDword);\n',
    'time':  '{3}{4} := DINT_TO_TIME(WORD_TO_DINT({0}[{1}]) * DINT#1000)\n',
    'word':  '{3}{4} := {0}[{1}];\n',
    'dword': '{3}{4}.W0 := {0}[{1}];{5} {3}{4}.W1 := {0}[{6}];\n'
}
template_bidir = 'if {0} <> {1}{2} then\n{3}else\n{4}end_if;\n{0} := {1}{2};\n'


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





class PCModbusGenerator:
    def __init__(self, project):
        self.project = project
        self.mb_arr_name = 'MB_Data_HMI'
        self.mb_cursor_name = 'MBcurrPos'
        self.plc_name = 'PLC'

        self.restore_sect = ''
        self.setting_sect = ''
        self.indication_sect = ''
        self.mb_pos = 1
        self.old_vals = list()
        self.old_vals_str = ''
        self.old_vals_types = list()
        self.old_vals_types_str = ''
        # Шаблон для MBcurrPos := MBcurrPos + х
        self.advance_template = '{0} := {0} + '.format(self.mb_cursor_name) + '{};\n'

        self.hmi_tags = ''

    def generate_all(self):
        lst = list(self.project.structs)
        lst.append(self.project.singles)
        for struct in lst:
            # Выбираем только настройки из структуры
            settings = FieldSet(struct, lambda f: f.state.var.get() == FieldState.setting.str())
            pos_save = self.mb_pos
            if len(settings.filtered) > 0:
                self.restore_sect += self.wrap_loops(settings, templates_to_mb)
                self.mb_pos = pos_save
                self.setting_sect += self.wrap_loops(settings, templates_to_plc)
            settings_length = self.mb_pos - pos_save
            pos_after_settings = self.mb_pos
            # Выбираем остальное
            indication = FieldSet(struct, lambda f: f.state.var.get() != FieldState.setting.str() and
                                  f.state.var.get() != FieldState.dont_trasmit.str())
            if len(indication.filtered) > 0:
                self.indication_sect += self.wrap_loops(indication)
            pos_after_indication = self.mb_pos
            # Вычисляем разницу
            indication_length = pos_after_indication - pos_after_settings
            if isinstance(struct, PhoenixStruct) and len(struct.instance_list) > 1:
                self.mb_pos += (self.mb_pos - pos_save) * (len(struct.instance_list) - 1)
                if settings_length > 0 and indication_length > 0:
                    setting_addition = self.advance_template.format(indication_length + 1)
                    self.restore_sect = self.insert_addition(self.restore_sect, setting_addition)
                    self.setting_sect = self.insert_addition(self.setting_sect, setting_addition)
                    indication_addition = self.advance_template.format(settings_length + 1)
                    self.indication_sect = self.insert_addition(self.indication_sect, indication_addition)
        self.restore_sect = 'if Restore then\n{}end_if;\n'.format(self.restore_sect)
        self.setting_sect = self.setting_sect
        code = '(* Код восстановления настроек после перезапуска *)\n' + self.restore_sect + '\n' +\
               '(* Код приема настроек из Modbus *)\n' + self.setting_sect + '\n' +\
               '(* Код обмена показаниями и командами *)\n' + self.indication_sect
        in_code, out_code = self.generate_inout()
        code = in_code + '\n\n' + code + '\n\n' + out_code
        self.generate_locals()
        print(self.hmi_tags)

    def wrap_loops(self, field_set, templ_dict=None):
        if field_set.original is not None:
            num_instances = len(field_set.original.instance_list)
            pos_save = self.mb_pos
            if num_instances > 1:
                struct_name = self.get_array_name(field_set.original) + '[i]'
            else:
                struct_name = field_set.original.instance_list[0]
            code = self.generate_variables(field_set.filtered, struct_name + '.', num_instances > 1,
                                           templ_dict, field_set.original)
            if num_instances > 1:
                ptr_jump = self.mb_cursor_name + ' := {};\n'.format(pos_save)
                # Обернуть код в цикл
                return ptr_jump + 'for i := 1 to {} do\n{}end_for;\n'.format(num_instances, code)
            else:
                return code
        else:
            return self.generate_variables(field_set.filtered, '', False, templ_dict)

    def generate_hmi_tags(self, field_set):
        if field_set.original is not None:
            for instance in field_set.original.instance_list:
                for field in field_set.filtered:
                    type_name = field.type.lower()


        # Гененрировать строку для импорта в HMI
        hmi_params = templates_hmi[type_name]
        address = self.mb_pos
        if type_name == 'bool':
            address = address * 100 + bit_counter
        hmi_line = '{}{},{},{},{},,{}\n'.format(struct_name, field.name, self.plc_name,
                                                hmi_params[0], address, hmi_params[1])
        self.hmi_tags += hmi_line

    def generate_variables(self, field_list, struct_name, use_relative_indexing, templ_dict=None, struct=None):
        bit_counter = 0
        code = ''
        advance_by_one = ' ' + self.advance_template.format(1).strip()
        for field in field_list:
            type_name = field.type.lower()
            # Если предыдущее поле было битовым, а новое - нет, то нужно начать с нового слова
            if bit_counter > 0 and type_name != 'bool':
                bit_counter = 0
                self.mb_pos += 1
                if use_relative_indexing:
                    code += self.advance_template.format(1)
            # Выбрать нужный шаблон
            if templ_dict is None:
                if field.state.var.get() == FieldState.control.str():
                    tts = templates_to_plc
                else:
                    tts = templates_to_mb
            else:
                tts = templ_dict
            if use_relative_indexing:
                cursor = self.mb_cursor_name
                fifth_param = advance_by_one
                sixth_param = cursor
            else:
                cursor = str(self.mb_pos)
                fifth_param = ''
                sixth_param = str(self.mb_pos + 1)
            # Генерировать код передачи согласно шаблону
            params = (self.mb_arr_name, cursor, bit_counter, struct_name, field.name, fifth_param, sixth_param)
            if field.state.var.get() == FieldState.control_change.str():
                to_plc = templates_to_plc[type_name].format(*params)
                to_mb = templates_to_mb[type_name].format(*params)
                old_var_name = self.get_old_var_name(field.name, use_relative_indexing, struct, type_name)
                code += template_bidir.format(old_var_name, struct_name, field.name, to_mb, to_plc)
            else:
                code += tts[type_name].format(*params)
            # Сместить указатели для битов и слов
            words_to_advance = 0
            if type_name == 'bool':
                bit_counter += 1
                if bit_counter > 15:
                    bit_counter = 0
                    words_to_advance = 1
            else:
                if use_relative_indexing:
                    words_to_advance = cursor_advance[type_name]
                else:
                    words_to_advance = type_size[type_name]
            if words_to_advance > 0:
                self.mb_pos += words_to_advance
                if use_relative_indexing:
                    code += self.advance_template.format(words_to_advance)
        # Последний элемент - бит, надо начать с нового слова
        if bit_counter > 0:
            self.mb_pos += 1
            if use_relative_indexing:
                code += self.advance_template.format(1)
        return code

    def generate_locals(self):
        code_vars = 'i\tINT\tVAR\tСчетчик для циклов\n'
        code_vars += '{}\tINT\tVAR\tУказатель позиции регистра Modbus\n'.format(self.mb_cursor_name)
        types = ''
        for struct in self.project.structs:
            if len(struct.instance_list) > 1:
                code_vars += '{}\t{}\t{}\t{}\n'.format(self.get_array_name(struct), self.get_array_type_name(struct),
                                                       'VAR', 'Обработка массивом прототипов структур ' + struct.name)
                types += '\t{}: ARRAY [1..{}] of {}; (* {} *)\n'.format(
                                self.get_array_type_name(struct), len(struct.instance_list),
                                struct.name, 'Массив для групповой обработки прототипов структуры ' + struct.name)
        code_vars += self.old_vals_str
        types += self.old_vals_types_str
        types = 'TYPE\n' + types + 'END_TYPE\n'
        return code_vars, types

    def generate_inout(self):
        in_code = ''
        out_code = ''
        for struct in self.project.structs:
            if len(struct.instance_list) > 1:
                index = 1
                for instance in struct.instance_list:
                    in_code += '{0}[{1}] := {2};\n'.format(self.get_array_name(struct), index, instance)
                    out_code += '{2} := {0}[{1}];\n'.format(self.get_array_name(struct), index, instance)
                    index += 1
        return in_code, out_code

    def get_old_var_name(self, field_name, indexed, struct, type_name):
        prob = field_name + '_Old'
        idx = 0
        while prob in self.old_vals:
            idx += 1
            prob = field_name + '_Old' + str(idx)
        self.old_vals.append(prob)
        if indexed:
            comment = 'Массив старых значений ' + field_name
            arr_type_name = 'ArrOf' + type_name + struct.name
            self.old_vals_str += '{}\t{}\t{}\t{}\n'.format(prob, arr_type_name, 'VAR', comment)
            if arr_type_name not in self.old_vals_types:
                self.old_vals_types_str += '\t{}: ARRAY [1..{}] of {}; (* {} *)\n'.format(arr_type_name,
                                                                                          len(struct.instance_list),
                                                                                          type_name, comment)
                self.old_vals_types.append(arr_type_name)
            prob += '[i]'
        else:
            self.old_vals_str += '{}\t{}\t{}\t{}\n'.format(prob, type_name, 'VAR', 'Старое значение ' + field_name)
        return prob

    @staticmethod
    def get_array_name(struct):
        return struct.name + '_Arr'

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

    @staticmethod
    def insert_addition(text, addition):
        lines = text.splitlines()
        lines[-2] = addition.strip()
        return '\n'.join(lines) + '\n'
