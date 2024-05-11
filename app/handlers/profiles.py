from telebot import types
from lib.db import execute_query
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


def register_handlers(bot):
    @bot.message_handler(commands=['profile'])
    def cmd_profile(message):
        user_id = message.from_user.id
        query = ("SELECT u.full_name, u.city, count(s.id) "
                 "FROM users u "
                 "LEFT JOIN scenarios s ON u.user_id = s.user_id "
                 "WHERE u.user_id = %s "
                 "GROUP BY u.full_name, u.city")
        result = execute_query(query, (user_id,))
        if result:
            full_name, city, user_scenarios = result[0]
            profile_text = f"Ваш профиль:\nФИО: {full_name}\nГород: {city}\nПользовательские сценарии: {user_scenarios}"
            logger.info(f"User {user_id} requested profile info")
        else:
            profile_text = "Ваш профиль пока не заполнен."
            logger.info(f"User {user_id} requested profile info but profile is empty")

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Редактировать", callback_data="edit_profile"))
        bot.reply_to(message, profile_text, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_profile")
    def cb_edit_profile(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Введите новые данные профиля в формате:\nФИО (не более 64 символов)\nГород (не более 50 символов)")
        logger.info(f"User {call.from_user.id} requested to edit profile")
        bot.register_next_step_handler(call.message, process_edit_profile)

    def process_edit_profile(message):
        user_id = message.from_user.id
        try:
            full_name, city = message.text.split('\n')
            if len(full_name) > 192 or len(city) > 50:
                raise ValueError("Превышена максимальная длина ФИО или города")

            query = "UPDATE users SET full_name = %s, city = %s WHERE user_id = %s"
            execute_query(query, (full_name, city, user_id))
            bot.send_message(message.chat.id, "Профиль успешно обновлен.")
            logger.info(f"User {user_id} updated profile: full_name={full_name}, city={city}")
        except ValueError as e:
            bot.send_message(message.chat.id, str(e))
            logger.warning(f"User {user_id} provided invalid data for profile update")
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка при обновлении профиля. Попробуйте еще раз.")
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")