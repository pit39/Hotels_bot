from peewee import *

db = SqliteDatabase('TelebotDatabase.db')


class BaseModel(Model):
    """
    Базовая модель, содержит указание на то, какую БД использовать
    """

    class Meta:
        database = db


class User(BaseModel):
    """
    Содержит данные отдельных пользователей
    """
    id = IntegerField(primary_key=True)
    city = IntegerField(null=True)
    check_in = DateField(null=True)
    check_out = DateField(null=True)
    hotels_amount = IntegerField(null=True)
    sort_method = CharField(null=True)
    current_command = CharField(null=True)
    search_start_time = CharField(null=True)
    date_state = CharField(null=True)
    distance = IntegerField(null=True)
    max_price = IntegerField(null=True)
    hotel = IntegerField(null=True)


class City(BaseModel):
    """
    Содержит id и имена городов
    """
    id = IntegerField(primary_key=True)
    name = CharField(null=True)


class Hotel(BaseModel):
    """
    Содержит данные отелей
    """
    id = IntegerField(primary_key=True)
    name = CharField(null=True)
    address = CharField(null=True)
    distance = FloatField(null=True)
    price = FloatField(null=True)
    url = CharField(null=True)


class History(BaseModel):
    """
    Содержит данные по запросам
    """
    id = PrimaryKeyField()
    user = IntegerField(null=True)
    command = CharField(null=True)
    search_start_time = DateTimeField(null=True)
    hotel_names = TextField(null=True)


def info(tab_string: Hotel) -> str:
    """
    :param tab_string: Принимает строку из таблицы Hotel
    :return: данные по отелям в виде текстовой строки
    """
    return f'{tab_string.name}\n' \
           f'адрес - {tab_string.address}\n' \
           f'цена за период - {tab_string.price}\n' \
           f'дистанция до центра - {tab_string.distance}\n ' \
           f'ссылка на сайт - {tab_string.url}'


def hist_info(tab_string: History) -> str:
    """
    :param tab_string: Принимает строку из таблицы History
    :return: данные по запросам в виде текстовой строки
    """
    return f'{tab_string.search_start_time} - ' \
           f'{tab_string.command}:\n ' \
           f'{tab_string.hotel_names}'
