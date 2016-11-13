from xlwt import *

templates_hmi = {
    'bool':  ('4x_Bit', 'Undesignated'),
    'real':  ('4x', 'Undesignated'),
    'int':   ('4x', 'Undesignated'),
    'dint':  ('4x', '32-bit SIGNED'),
    'time':  ('4x', 'Undesignated'),
    'word':  ('4x', 'Undesignated'),
    'dword': ('4x', '32-bit UNSIGNED')
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
        for i, event in zip(range(len(event_list)), event_list):
            pass
        wb.save(self.settings.weintek_event_file())
