
alarm_def_file_name = 'AlarmText.csv'
alarm_defs = '{};1;0.000000;0.000000;@GV.{}\n'
alarm_text = 'ALRLIST0_{};{}\n'
default_text = """\tTimestamp\tValue;\tВремя\tЗначение
/\;/\
< scroll;< перемотать
<< scroll;<< перемотать
ACK;ПТВ
Acknowledge By: ;Квитировать по:
Active;Активные
Add;Добавить
AlarmText    V;ТекстСообщения  V
AlarmText   /\;ТекстСообщения   /\
AlarmText;ТекстСообщения
All;Все
Clear;Очистить
DEC_SYMB;.
Delete All;Удалить все
Delete;Удалить
Export CSV File:;Экспорт CSV файла:
Filter by alarm state:;Фильтр по состоянию:
Inactive;Неактивные
Item;Выделению
LANG_SYMB;RU
Load Alarm History:;Загрузка архива сообщений:
Load Info;Обновить данные
Loading Alarms ...;Идет загрузка ...
Loading Data ...;Загрузка данных ...
Locked;Заблокировано
Multi;Множественный
Newest;Последние
No Filter\nAlarms Off\nAlarms On;Без фильтра\nНеактивные\nАктивные
Not sorted\nOldest alarm first\nNewest alarm first;Несортированные\nСначала старые\nСначала последние
Offline Alarm History: List Showing All Alarms (Updated on demand);Архив сообщений (оффлайн): Список всех аварий/ предупреждений (Обновление по запросу)
Oldest;Старые
Online Alarm History: List Showing All Alarms (Updated each Applet period);Список сообщений/предупреждений (онлайн)
PM_AM;0
Remove;Удалить
Restart;Перезапустить
Save;Сохранить
Selection Mode:;Режим выбора:
Single;Одиночный
Sort by time on:;Сортировка по времени:
Sorting Alarms ...;Построение списка ...
Start Load;Начать загрузку
Start;Старт
StateColor\tIID\tTID\tAlarm Text\tOn\tOff\tACK;StateColor\tIID\tТип\tТекст\tВкл\tВыкл\tПТВ
Stop Load;Stop Load
Stop;Стоп
TID;TID
Time Off    V;Время отключения    V
Time Off   /\;Время отключения   /\
Time Off;Время отключения
Time On    V;Время включения    V
Time On   /\;Время включения   /\
Time On;Время включения
Type;Типу
Unlocked;Разблокировать
Update;Обновить
V;V
Zoom In;Приблизить
Zoom Out;Отдалить
scroll >;перемотать >
scroll >>;перемотать >>"""


# Класс, который генерирует файлы для WebVisit
class WebVisitGenerator:
    def __init__(self, generator):
        self.generator = generator
        self.settings = generator.project.settings
        self.address_spaces = generator.addr_spaces

    # Склейка всех тэгов в один большой список
    def get_event_tags(self):
        tags = list()
        for addr_space in self.address_spaces:
            for instance in addr_space.instances:
                tags.extend(instance)
        return list(filter(lambda t: t.field.event(), tags))

    def generate(self):
        tags = self.get_event_tags()
        tag_defs = ''
        text_defs = ''
        for i, tag in zip(range(len(tags)), tags):
            tag_defs += alarm_defs.format(i + 1, tag.get_name())
            text_defs += alarm_text.format(i + 1, tag.get_description())
        tag_defs = alarm_def_file_name + '\n' + str(len(tags)) + '\n' + tag_defs
        text_defs = default_text + '\n' + text_defs
        f = open(self.settings.webvisit_file(), 'w')
        f.write(tag_defs)
        f.close()
        f = open(self.settings.webvisit_text_file(), 'w')
        f.write(text_defs)
        f.close()
