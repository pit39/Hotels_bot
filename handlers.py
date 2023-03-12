from loader import *
from telebot import types
from datetime import datetime


def bot_commands_respond(message: types.Message) -> None:
    """
    Записывает соответствующие команде параметры в строку пользователя таблицы User,
    запускает следующий шаг
    """
    current_user = User.get_or_create(id=message.from_user.id)[0]
    current_user.search_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if message.text == '/lowprice':
        current_user.sort_method = "PRICE"
        current_user.current_command = 'lowprice'

    elif message.text == '/highprice':
        current_user.sort_method = "PRICE_HIGHEST_FIRST"
        current_user.current_command = 'highprice'
    else:
        current_user.sort_method = "DISTANCE_FROM_LANDMARK"
        current_user.current_command = 'bestdeal'
    current_user.max_price = None
    current_user.distance = None
    current_user.save()
    bot.send_message(message.from_user.id, 'Введите город:')
    bot.register_next_step_handler(message, get_city)


def bot_help_respond(message: types.Message) -> None:
    """
    Выводит пользователю данные по доступным возможностям
    """
    bot.send_message(message.from_user.id,
                     "Доступные команды:\n"
                     "/help - список доступных комманд\n"
                     "/lowprice - топ самых дешевых отелей\n"
                     "/highprice - топ самых дорогих отелей\n"
                     "/bestdeal - лучшее предложение по цене и расстоянию от центра\n"
                     "/history - показывает историю ваших запросов"
                     )


def bot_start_respond(message: types.Message) -> None:
    """
    Функция приветствует пользователя
    """
    bot.send_message(message.from_user.id, "Привет, я бот, который ищет лучшие предложения по отелям на сайте "
                                           "hotels.com, напиши любой текст или команду /help чтобы узнать мои "
                                           "возможности")


def get_city(message: types.Message) -> None:
    """
    Функция выводит кнопки с выбором из найденных результатов по городам
    """
    bot.send_message(message.from_user.id, 'Ищу город {}'.format(message.text))
    city_list = api_getter.get_cities(message.text)
    if type(city_list) == str:
        bot.send_message(message.from_user.id, city_list)
        return
    if len(city_list) == 0:
        bot.send_message(message.from_user.id, 'Город с таким названием не найден')
        return
    keyboard = types.InlineKeyboardMarkup()
    for city in city_list:
        city_button = types.InlineKeyboardButton(text=city.name, callback_data=('city {}'.format(city.id)))
        keyboard.add(city_button)
    bot.send_message(message.chat.id, "Результаты поиска:", reply_markup=keyboard)


def bot_button_respond(call: types.CallbackQuery) -> None:
    """
    Функция обрабатывает нажатие пользователем inline кнопок за исключением календаря
    """
    respond_type, data = call.data.split()
    current_user = User[call.from_user.id]
    if respond_type == 'city':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        current_user.city = data
        current_user.save()
        current_city = City.get_or_none(id=data)
        bot.send_message(call.from_user.id, 'Выбран город {}'.format(current_city.name))
        start_check_in(call)
    elif respond_type == 'hotel':
        current_user.hotel = data
        current_user.save()
        bot.send_message(call.from_user.id, 'Сколько фото? (Max={})'.format(max_photos))
        bot.register_next_step_handler(call.message, get_photos)


def start_check_in(message: types.CallbackQuery) -> None:
    """
    Запускает вывод календаря для выбора даты заезда
    """
    current_user = User[message.from_user.id]
    current_user.date_state = "check_in"
    current_user.save()
    bot.send_message(message.from_user.id, 'Заезд:')
    make_calendar(message)


def start_check_out(message: types.CallbackQuery) -> None:
    """
    Запускает вывод календаря для выбора даты выезда
    """
    current_user = User[message.from_user.id]
    current_user.date_state = "check_out"
    current_user.save()
    bot.send_message(message.from_user.id, 'Выезд:')
    make_calendar(message)


def make_calendar(call: types.CallbackQuery) -> None:
    """
    Создает inline календарь
    """
    now = datetime.now()
    bot.send_message(
        call.from_user.id,
        "Выберите дату",
        reply_markup=calendar.create_calendar(
            name=calendar_1_callback.prefix,
            year=now.year,
            month=now.month,
        ),
    )


def calendar_response(call: types.CallbackQuery) -> None:
    """
    Обрабатывает нажатие кнопок календаря и запускает соответствующий команде следующий шаг
    """
    name, action, year, month, day = call.data.split(calendar_1_callback.sep)
    date = calendar.calendar_query_handler(
        bot=bot, call=call, name=name, action=action, year=year, month=month, day=day
    )
    current_user = User[call.from_user.id]
    if action == "DAY":
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы выбрали {date.strftime('%Y-%m-%d')}",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        if current_user.date_state == "check_in":
            current_user.check_in = date.date()
            current_user.save()
            start_check_out(call)

        elif current_user.date_state == "check_out":
            current_user.check_out = date.date()
            current_user.save()
            bot.send_message(call.from_user.id,
                             "Check in - {check_in}\nCheck out - {check_out}".format(
                                 check_in=current_user.check_in,
                                 check_out=current_user.check_out
                             )
                             )

            if current_user.current_command == 'lowprice' or \
                    current_user.current_command == 'highprice':
                bot.send_message(call.from_user.id, 'Сколько отелей показать? (Max={})'.format(max_hotels))
                bot.register_next_step_handler(call.message, get_hotels_amount)

            elif current_user.current_command == 'bestdeal':
                bot.send_message(call.from_user.id, 'Укажите максимальную дистанцию от центра, км:')
                bot.register_next_step_handler(call.message, get_distance)

        print(f"{calendar_1_callback}: Day: {date.strftime('%Y-%m-%d')}")

    elif action == "CANCEL":
        bot.send_message(
            chat_id=call.from_user.id,
            text="Отмена",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        print(f"{calendar_1_callback}: Cancellation")


def get_distance(message: types.Message) -> None:
    """
    Записывает полученную от пользователя дистанцию до центра, или, если некорректно, запрашивает снова
    """
    if not message.text.isdigit():
        bot.reply_to(message, 'Ввести надо положительное число '
                              'цифрами, попробуйте еще раз')
        bot.register_next_step_handler(message, get_distance)
        return
    current_user = User[message.from_user.id]
    current_user.distance = message.text
    current_user.save()
    bot.send_message(message.from_user.id, 'Введите максимальную стоимость за период, руб')
    bot.register_next_step_handler(message, get_price)


def get_price(message: types.Message) -> None:
    """
    Записывает полученную от пользователя максимальную стоимость, или, если некорректно, запрашивает снова
    """
    if not message.text.isdigit():
        bot.reply_to(message, 'Ввести надо положительное число '
                              'цифрами, попробуйте еще раз')
        bot.register_next_step_handler(message, get_price)
        return
    current_user = User[message.from_user.id]
    current_user.max_price = message.text
    current_user.save()
    bot.send_message(message.from_user.id, 'Сколько отелей показать? (Max={})'.format(max_hotels))
    bot.register_next_step_handler(message, get_hotels_amount)


def get_hotels_amount(message: types.Message) -> None:
    """
    Сохраняет количество выводимых отелей от пользователя,
    если некорректно, то запрашивает снова, иначе запускает get_hotels
    """
    current_user = User[message.from_user.id]
    if not message.text.isdigit() or int(message.text) <= 0:
        bot.reply_to(message, 'Ввести надо положительное число '
                              'цифрами, попробуйте еще раз')
        bot.register_next_step_handler(message, get_hotels_amount)
        return
    elif int(message.text) > max_hotels:
        bot.send_message(message.from_user.id, 'Слишком много, покажу до {max}'.format(max=max_hotels))
        current_user.hotels_amount = max_hotels
    else:
        current_user.hotels_amount = int(message.text)
    current_user.save()
    get_hotels(message)


def get_hotels(message: types.Message) -> None:
    """
    Выводит информацию об отелях в отдельных сообщения, также под каждым отелем выводит
    кнопку для показа фотографий, сохраняет данные о запросе в таблицу History
    """
    current_user = User[message.from_user.id]
    current_history = History.create(
        user=current_user.id,
        command=current_user.current_command,
        search_start_time=current_user.search_start_time
    )
    hotel_names = ''
    bot.send_message(message.from_user.id, 'Ищу отели...')
    hotels_list = api_getter.get_hotels(
        city_id=current_user.city,
        hotels_amount=current_user.hotels_amount,
        check_in=current_user.check_in,
        check_out=current_user.check_out,
        sort=current_user.sort_method,
        distance=current_user.distance,
        max_price=current_user.max_price
    )
    if type(hotels_list) == str:
        bot.send_message(message.from_user.id, hotels_list)
        current_history.hotel_names = hotels_list
        current_history.save()
        return
    if len(hotels_list) == 0:
        bot.send_message(message.from_user.id, 'Отели по заданным параметрам не найдены')
        current_history.hotel_names = 'Отели не найдены'
        current_history.save()
        return
    else:
        for num, hotel in enumerate(hotels_list, 1):
            hotel_names += f'{num} - {hotel.name}\n'
            keyboard = types.InlineKeyboardMarkup()
            hotel_button = types.InlineKeyboardButton(
                text='Показать фотографии',
                callback_data=('hotel {}'.format(hotel.id)
                               )
            )
            keyboard.add(hotel_button)
            bot.send_message(message.chat.id, info(hotel), reply_markup=keyboard)
        current_history.hotel_names = hotel_names
        current_history.save()


def get_photos(message: types.Message) -> None:
    """
    Принимает от пользователя количество фотографий, если некорректно,
    то запрашивает снова, иначе выводит каждую фотографию отдельным сообщением
    """
    current_user = User[message.from_user.id]
    if not message.text.isdigit() or int(message.text) <= 0:
        bot.reply_to(message, 'Ввести надо целое положительное число '
                              'цифрами, попробуйте еще раз')
        bot.register_next_step_handler(message, get_photos)
        return
    elif int(message.text) >= max_photos:
        photos = max_photos
    else:
        photos = int(message.text)
    bot.send_message(message.from_user.id, 'Отель:\n {}'.format(info(Hotel[current_user.hotel])))
    bot.send_message(message.from_user.id, 'Покажу {} фото'.format(photos))
    photos_list = api_getter.get_photos(hotel_id=current_user.hotel, photos_count=photos)
    for photo in photos_list:
        bot.send_message(message.from_user.id, photo)


def bot_history_respond(message: types.Message) -> None:
    """
    Запрашивает у пользователя количество выводимых запросов истории
    """
    bot.send_message(message.from_user.id, 'Сколько запросов показать? (Max={})'.format(max_history))
    bot.register_next_step_handler(message, get_history_amount)


def get_history_amount(message: types.Message) -> None:
    """
    Принимает количество выводимых запросов от пользователя, если некорректно,
    то запрашивает снова, иначе выводит не более указанного количества запросов
    """
    if not message.text.isdigit() or int(message.text) <= 0:
        bot.reply_to(message, 'Ввести надо положительное число '
                              'цифрами, попробуйте еще раз')
        bot.register_next_step_handler(message, get_history_amount)
        return
    history_count = int(message.text)
    if history_count > max_hotels:
        bot.send_message(message.from_user.id, 'Слишком много, покажу до {max} запросов'.format(max=max_history))
        history_count = max_history

    for history in reversed(History.select().where(
            History.user == message.from_user.id).limit(history_count).order_by(History.id.desc())):
        bot.send_message(message.from_user.id, hist_info(history))
