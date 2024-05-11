import logging
from dotenv import load_dotenv
import telebot

from lib import db
from handlers import devices, profiles, scenarios

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = telebot.TeleBot('6520198641:AAHx0GTw6CxPU3B7hmQPfqPH-uOAJlS6tEo')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    logger.info(f"User {user_id} started the bot")
    bot.reply_to(message, f"Приветствую, {user_name}! Добро пожаловать в Telemetry Bot.")

    user = db.execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
    if not user:
        db.execute_query("INSERT INTO users (user_id, name) VALUES (%s, %s)", (user_id, user_name,))


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def cmd_help(message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested help")
    help_message = "Доступные команды:\n" \
                   "/start - Запустить бота\n" \
                   "/help - Показать это сообщение с помощью\n\n" \
                   "/add_device - Добавить новое устройство\n" \
                   "/list_devices - Показать список ваших устройств\n" \
                   "/delete_device - Удалить устройство\n\n" \
                   "/list_sensors - Показать список ваших датчиков\n\n" \
                   "/profile - Показать ваш профиль\n\n" \
                   "/scenarios - Управление сценариями\n" \
                   "/list_scenarios - Показать список ваших сценариев\n" \
                   "/delete_scenario - Удалить сценарий\n\n" \
                   "/siren - Включить звуковое оповещение на устройстве\n" \
                   "/motor - Включить моторчик на устройстве\n" \
                   "/notify - Отправить уведомление на телефон\n" \
                   "/relay - Переключить реле на устройстве"
    bot.reply_to(message, help_message)


# Обработчик неизвестных команд
# @bot.message_handler(func=lambda message: True)
# def unknown_command(message):
#     user_id = message.from_user.id
#     logger.warning(f"User {user_id} sent an unknown command: {message.text}")
#     bot.reply_to(message, "Sorry, I don't understand that command. Please use /help to see the available commands.")


# Запуск бота
if __name__ == '__main__':
    logger.info("Starting the bot...")
    devices.register_handlers(bot)
    profiles.register_handlers(bot)
    scenarios.register_handlers(bot)
    logger.info("Bot started")
    db.connect_db()
    logger.info("DB connected")
    bot.polling()
