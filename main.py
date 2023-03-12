from aiohttp import web
from loader import *
import handlers
from telebot import types


WEBHOOK_URL_BASE = "https://{}".format(WEBHOOK_HOST)
# WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(bot_token)


app = web.Application()


# Process webhook calls
async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)


app.router.add_post('/{token}/', handle)


# handlers here
@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def command_respond(message: types.Message) -> None:
    """
    Запускает последовательность действий для команд поиска отелей
    """
    handlers.bot_commands_respond(message)


@bot.message_handler(commands=['history'])
def history_respond(message: types.Message) -> None:
    """
    Запускает последовательность действий для вывода истории запросов
    """
    handlers.bot_history_respond(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(handlers.calendar_1_callback.prefix))
def callback_calendar(call: types.CallbackQuery) -> None:
    """
    Обрабатывает нажатие кнопок календаря
    """
    handlers.calendar_response(call)


@bot.callback_query_handler(func=lambda call: True)
def button_respond(call: types.CallbackQuery) -> None:
    """
    Обрабатывает нажатие прочих кнопок
    """
    handlers.bot_button_respond(call)


@bot.message_handler(commands=['start'])
def start_respond(message: types.Message) -> None:
    """
    Запускает функцию вывода стартового сообщения
    """
    handlers.bot_start_respond(message)


@bot.message_handler(content_types=['text'])
@bot.message_handler(commands=['help'])
def help_respond(message: types.Message) -> None:
    """
    Запускает вывод справки при команде help или необработанном тексте
    """
    handlers.bot_help_respond(message)


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)  # certificate=open(WEBHOOK_SSL_CERT, 'r')

# # Build ssl context
# context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
# context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start aiohttp server
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,

)  # ssl_context==context
