from project import FieldState


# 0 - имя массива Modbus
# 1 - имя переменной-указателя для массива Modbus
# 2 - номер бита в слове для битовых переменных
# 3 - имя массива структур для обработки
# 4 - имя поля в структуре
templates_to_mb = {
    'bool':  '{0}[{1}].X{2} := {3}[i].{4};\n',
    'real':  '{0}[{1}] := REAL_TO_WORD({3}[i].{4} * 100.0);\n',
    'int':   '{0}[{1}] := INT_TO_WORD({3}[i].{4});\n',
    'dint':  'TempDword := DINT_TO_DWORD({3}[i].{4}); {0}[{1}] := TempDword.W0; {1} := {1} + 1; {0}[{1}] := TempDword.W1;\n',
    'time':  '{0}[{1}] := DINT_TO_WORD(TIME_TO_DINT({3}[i].{4}) / DINT#1000);\n',
    'word':  '{0}[{1}] := {3}[i].{4};\n',
    'dword': '{0}[{1}] := {3}[i].{4}.W0; {1} := {1} + 1; {0}[{1}] := {3}[i].{4}.W1;\n',
}

templates_to_plc = {
    'bool':  '{3}[i].{4} := {0}[{1}].X{2};\n',
    'real':  '{3}[i].{4} := WORD_TO_REAL({0}[{1}]) / 100.0;\n',
    'int':   '{3}[i].{4} := WORD_TO_INT({0}[{1}]);\n',
    'dint':  'TempDword.W0 := {0}[{1}]; {1} := {1} + 1; TempDword.W1 := {0}[{1}]; {3}[i].{4} := DWORD_TO_DINT(TempDword);\n',
    'time':  '{3}[i].{4} := DINT_TO_TIME(WORD_TO_DINT({0}[{1}]) * DINT#1000)\n',
    'word':  '{3}[i].{4} := {0}[{1}];\n',
    'dword': '{3}[i].{4}.W0 := {0}[{1}]; {1} := {1} + 1; {3}[i].{4}.W1 := {0}[{1}];\n',
}


# Класс набор полей определенной структуры
# Умеет фильтровать поля структуры согласно переданному предикату predicate
class FieldSet:
    def __init__(self, struct, predicate):
        self.original = struct
        self.predicate = predicate
        self.filtered = list()
        self.filter()
        self.sort()

    # Метод, фильтрующий поля структуры согласно предикату
    def filter(self):
        if self.predicate is not None:
            for field in self.original.fields:
                if self.predicate(field):
                    self.filtered.append(field)

    # Метод, сортирующий поля по алфавиту и складывающий битовые поля в начало списка
    def sort(self):
        self.filtered.sort(key=lambda field: field.name.lower())
        self.filtered.sort(key=lambda field: field.type.lower() != 'bool')


class Loop:
    def __init__(self, generator, field_set, restore_settings=False):
        self.gen = generator
        self.list = field_set
        self.iterations = len(field_set.original.instance_list)
        self.restore = restore_settings

    def generate_code(self):
        # Генерация кода
        if self.restore:
            tts = templates_to_mb
        else:
            tts = templates_to_plc
        code = ''
        if self.iterations > 1:
            code = 'for i := 1 to {} do\n'.format(self.iterations)
        for var in self.list.filtered:
            code += tts[var.type.lower()].format(self.gen.mb_arr_name, self.gen.mb_cursor_name, 0,
                                                 self.list.original.name, var.name)
        if self.iterations > 1:
            code += 'end_for;\n'
        return code


# Базовый класс секции кода. Генерирует секцию кода из нескольких циклов, по одному для каждой структуры
class CodeSection:
    def __init__(self, generator, predicate, loop_args = None):
        self.generator = generator
        self.project = generator.project
        self.predicate = predicate
        self.loop_args = loop_args
        self.field_sets = list()
        self.loops = list()

        for struct in self.project.structs:
            field_set = FieldSet(struct, self.predicate)
            if len(field_set.filtered) == 0:
                continue
            self.field_sets.append(field_set)

    def generate_code(self):
        code = ''
        for field_set in self.field_sets:
            loop = Loop(self.generator, field_set, self.loop_args)
            self.loops.append(loop)
            code += loop.generate_code()
        print(code)
        return code


class PCModbusGenerator:
    def __init__(self, project):
        self.project = project
        self.mb_arr_name = 'MB_Data_HMI'
        self.mb_cursor_name = 'MBcurrPos'
        code_sections = list()
        # Создаем секции кода
        code_sections.append(CodeSection(self, self.predicate, True))
        code_sections.append(CodeSection(self, self.predicate, False))
        code_sections.append(CodeSection(self, lambda f: not self.predicate(f)))
        for section in code_sections:
            section.generate_code()

    @staticmethod
    def predicate(field):
        return field.state.var.get() == FieldState.setting.str()
