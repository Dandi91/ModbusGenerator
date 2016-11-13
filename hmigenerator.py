from xlwt import *


# Тип адреса, формат данных метки, формат данных события
templates_hmi = {
    'bool':  ('4x_Bit', 'Undesignated', '16-bit Unsigned'),
    'real':  ('4x', 'Undesignated', '16-bit Unsigned'),
    'int':   ('4x', 'Undesignated', '16-bit Unsigned'),
    'dint':  ('4x', '32-bit SIGNED', '32-bit SIGNED'),
    'time':  ('4x', 'Undesignated', '16-bit Unsigned'),
    'word':  ('4x', 'Undesignated', '16-bit Unsigned'),
    'dword': ('4x', '32-bit UNSIGNED', '32-bit SIGNED')
}


# Класс, который генерирует файлы для импорта в HMI
class HMIGenerator:
    def __init__(self, generator):
        self.generator = generator
        self.settings = generator.settings
        self.address_spaces = generator.addr_spaces

    def generate(self):
        tags = self.get_hmi_tags()
        # Пишем метки
        f = open(self.settings.weintek_tag_file(), 'w')
        for tag in tags:
            f.write(self.generate_hmi_tag(tag))
        f.close()
        # Пишем события
        events = list(filter(lambda t: t.field.event(), tags))
        self.write_events(events)

    # Склейка всех тэгов в один большой список
    def get_hmi_tags(self):
        tags = list()
        for addr_space in self.address_spaces:
            for instance in addr_space.instances:
                tags.extend(instance)
        return tags

    # Генерация тэга HMI из адресной метки
    def generate_hmi_tag(self, address_tag):
        type_name = address_tag.field.type.lower()
        hmi_params = templates_hmi[type_name]
        if type_name == 'bool':
            hmi_address = address_tag.address * 100 + address_tag.bit
        else:
            hmi_address = address_tag.address
        instance_name = address_tag.instance
        if address_tag.instance != '':
            instance_name += '.'
        return '{}{},{},{},{},,{}'.format(instance_name, address_tag.field.name, self.settings.plc_name(),
                                          hmi_params[0], hmi_address, hmi_params[1])

    # Генерация Excel-файла с событиями для HMI
    def write_events(self, event_list):
        header = ['Категория', 'Приоритет', 'Тип адреса', 'Имя ПЛК (Чтение)', 'Тип устройства (Чтение)'
                  'Системный тэг (Чтение)', 'Пользовательский тэг (Чтение)', 'Адрес (Чтение)', 'Индекс (Чтение)',
                  'Формат данных (Чтение)', 'Уведомление доступно', 'ON (Уведомление)', 'Имя ПЛК (Уведомление)',
                  'Тип устройства (Уведомление)', 'Системный тэг (Уведомление)', 'Пользовательский тэг (Уведомление)',
                  'Адрес (Уведомление)', 'Индекс (Уведомление)', 'Условие', 'Значение триггера', 'Содержание',
                  'Библиотека меток пользователя', 'Имя метки', 'Шрифт', 'Цвет', 'Подтвержденное значение',
                  'Звук доступен', 'Имя библиотеки звуков', 'Индекс звука', '№ просмотра', 'Продолжительный "бипер"',
                  'Временной интервал "бипера"', 'Отправка e-mail по событию', 'Отправка e-mail при снятии события',
                  'Время задержки', 'Динамическое условие', 'Имя ПЛК (Условие)', 'Тип устройства (Условие)',
                  'Системный тэг (Условие)', 'Тэг определяемый пользователем (Условие)', 'Адрес (Условие)',
                  'Индекс (Условие)']
        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('Event')
        # Записываем заголовок
        for i, text in zip(range(len(header)), header):
            ws.write(0, i, text)
        # Записываем события
        for i, event in zip(range(1, len(event_list) + 1), event_list):
            name, address, data_format = self.get_event_info(event)
            ws.write(i, 0, '0')                             # Категория
            ws.write(i, 1, 'Middle')                        # Приоритет
            ws.write(i, 2, 'Bit')                           # Тип адреса
            ws.write(i, 3, self.settings.plc_name())        # Имя ПЛК (Чтение)
            ws.write(i, 4, name)                            # Тип устройства (Чтение)
            ws.write(i, 5, 'False')                         # Системный тэг (Чтение)
            ws.write(i, 6, 'True')                          # Пользовательский тэг (Чтение)
            ws.write(i, 7, address)                         # Адрес (Чтение)
            ws.write(i, 8, 'null')                          # Индекс (Чтение)
            ws.write(i, 9, data_format)                     # Формат данных (Чтение)
            ws.write(i, 10, 'False')                        # Уведомление доступно
            ws.write(i, 11, 'False')                        # ON (Уведомление)
            ws.write(i, 12, 'Local HMI')                    # Имя ПЛК (Уведомление)
            ws.write(i, 13, 'LB')                           # Тип устройства (Уведомление)
            ws.write(i, 14, 'False')                        # Системный тэг (Уведомление)
            ws.write(i, 15, 'False')                        # Пользовательский тэг (Уведомление)
            ws.write(i, 16, '0')                            # Адрес (Уведомление)
            ws.write(i, 17, 'null')                         # Индекс (Уведомление)
            ws.write(i, 18, 'bt: 1')                        # Условие
            ws.write(i, 19, '0')                            # Значение триггера
            description = self.get_event_description(event)
            ws.write(i, 20, description)                    # Содержание
            ws.write(i, 21, 'False')                        # Библиотека меток пользователя
            ws.write(i, 22, '')                             # Имя метки
            ws.write(i, 23, 'Arial')                        # Шрифт
            color = self.get_event_color(event)
            ws.write(i, 24, color)                          # Цвет
            ws.write(i, 25, 11)                             # Подтвержденное значение
            ws.write(i, 26, 'True')                         # Звук доступен
            ws.write(i, 27, '[ Проект ]')                   # Имя библиотеки звуков
            ws.write(i, 28, '0')                            # Индекс звука
            ws.write(i, 29, '0')                            # № просмотра
            ws.write(i, 30, 'False')                        # Продолжительный "бипер"
            ws.write(i, 31, '10')                           # Временной интервал "бипера"
            ws.write(i, 32, 'False')                        # Отправка e-mail по событию
            ws.write(i, 33, 'False')                        # Отправка e-mail при снятии события
            ws.write(i, 34, '0')                            # Время задержки
            ws.write(i, 35, '0')                            # Динамическое условие
            ws.write(i, 36, self.settings.plc_name())       # Имя ПЛК (Условие)
            ws.write(i, 37, name)                           # Тип устройства (Условие)
            ws.write(i, 38, 'False')                        # Системный тэг (Условие)
            ws.write(i, 39, 'True')                         # Тэг определяемый пользователем (Условие)
            ws.write(i, 40, address)                        # Адрес (Условие)
            ws.write(i, 41, 'null')                         # Индекс (Условие)
            ws.write(i, 42, 'True')                         # ?
        wb.save(self.settings.weintek_event_file())

    @staticmethod
    def get_event_info(event_tag):
        if event_tag.instance != '':
            name = event_tag.instance + '.' + event_tag.field.name
        else:
            name = event_tag.field.name
        type_name = event_tag.field.type.lower()
        hmi_type_params = templates_hmi[type_name]
        hmi_address_type = hmi_type_params[0]
        data_format = hmi_type_params[2]
        if type_name == 'bool':
            address = event_tag.address * 100 + event_tag.bit
        else:
            address = event_tag.address
        hmi_address = '{}-{}'.format(hmi_address_type, address)
        return name, hmi_address, data_format

    @staticmethod
    def get_event_description(event_tag):
        device_prefixes = ('SENS_', 'VLV_', 'PMP_', 'REG_')
        device_name = event_tag.instance
        for prefix in device_prefixes:
            if device_name.startswith(prefix):
                device_name = device_name.replace(prefix, '')
                break
        comment = event_tag.field.comment
        if comment.count('{}') < 1:
            comment = '{} - ' + comment
        return comment.format(device_name)

    def get_event_color(self, event_tag):
        tk_color = '#000'
        for event_type in self.generator.project.event_types:
            if event_tag.field.name.lower().startswith(event_type.prefix().lower()):
                tk_color = event_type.color()
                break
        tk_color = tk_color[1:]
        channel = int(len(tk_color) / 3)
        red = int(tk_color[0:channel], 16)
        green = int(tk_color[channel:channel*2], 16)
        blue = int(tk_color[channel*2:], 16)
        return '{}:{}:{}'.format(red, green, blue)
