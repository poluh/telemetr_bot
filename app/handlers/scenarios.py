from telebot import types
from lib.db import execute_query
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


def register_handlers(bot):
    @bot.message_handler(commands=['scenarios'])
    def cmd_scenarios(message):
        user_id = message.from_user.id
        query = "SELECT id, name, type FROM scenarios WHERE user_id = %s"
        scenarios = execute_query(query, (user_id,))

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Создать новый сценарий", callback_data="create_scenario"))
        if scenarios:
            for scenario_id, scenario_name, scenario_type in scenarios:
                keyboard.add(types.InlineKeyboardButton(scenario_name, callback_data=f"scenario_{scenario_id}"))
            bot.reply_to(message, "Выберите сценарий или создайте новый:", reply_markup=keyboard)
            logger.info(f"User {user_id} requested scenario list")
        else:
            bot.reply_to(message, "У вас пока нет сценариев. Хотите создать новый?", reply_markup=keyboard)
            logger.info(f"User {user_id} has no scenarios")

    @bot.callback_query_handler(func=lambda call: call.data == "create_scenario")
    def cb_create_scenario(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Введите название нового сценария:")
        bot.register_next_step_handler(call.message, process_create_scenario_name)

    def process_create_scenario_name(message):
        scenario_name = message.text
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("По умолчанию", callback_data=f"create_scenario_type_default_{scenario_name}"))
        keyboard.add(types.InlineKeyboardButton("Пользовательский",
                                                callback_data=f"create_scenario_type_custom_{scenario_name}"))
        bot.send_message(message.chat.id, "Выберите тип сценария:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("create_scenario_type_"))
    def cb_create_scenario_type(call):
        scenario_name = call.data.split("_")[4]
        scenario_type = call.data.split("_")[3]
        if scenario_type == "default":
            query = "INSERT INTO scenarios (user_id, name, type) VALUES (%s, %s, %s)"
            scenario_id = execute_query(query, (call.from_user.id, scenario_name, scenario_type), return_id=True)
            bot.answer_callback_query(call.id, f"Сценарий '{scenario_name}' создан.")
            logger.info(f"User {call.from_user.id} created default scenario '{scenario_name}' with ID {scenario_id}")
        else:
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id,
                             f"Введите условия для сценария '{scenario_name}' в формате: Датчик_1(ЕСЛИ(><)ХХХ)ИДатчик2(=1/0)ИЛИДатчик3(>17:00)ТоДатчик4")
            bot.register_next_step_handler(call.message, process_create_scenario_conditions, scenario_name)

    def process_create_scenario_conditions(message, scenario_name):
        scenario_conditions = message.text
        bot.send_message(message.chat.id, f"Введите действия для сценария '{scenario_name}':")
        bot.register_next_step_handler(message, process_create_scenario_actions, scenario_name, scenario_conditions)

    def process_create_scenario_actions(message, scenario_name, scenario_conditions):
        scenario_actions = message.text
        query = "INSERT INTO scenarios (user_id, name, type, conditions, actions) VALUES (%s, %s, %s, %s, %s)"
        execute_query(query, (
            message.from_user.id, scenario_name, "custom", scenario_conditions, scenario_actions))
        bot.send_message(message.chat.id, f"Сценарий '{scenario_name}' создан.")
        logger.info(f"User {message.from_user.id} created custom scenario '{scenario_name}'")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("scenario_"))
    def cb_scenario(call):
        scenario_id = int(call.data.split("_")[1])
        query = "SELECT name, type, conditions, actions FROM scenarios WHERE id = %s"
        result = execute_query(query, (scenario_id,))
        if result:
            scenario_name, scenario_type, scenario_conditions, scenario_actions = result[0]
            scenario_text = f"Сценарий: {scenario_name}\nТип: {scenario_type}\nУсловия: {scenario_conditions}\nДействия: {scenario_actions}"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Запустить", callback_data=f"run_scenario_{scenario_id}"))
            keyboard.add(types.InlineKeyboardButton("Редактировать", callback_data=f"edit_scenario_{scenario_id}"))
            keyboard.add(types.InlineKeyboardButton("Удалить", callback_data=f"delete_scenario_{scenario_id}"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=scenario_text,
                                  reply_markup=keyboard)
            logger.info(f"User {call.from_user.id} requested info for scenario {scenario_id}")
        else:
            bot.answer_callback_query(call.id, "Сценарий не найден.")
            logger.warning(f"User {call.from_user.id} requested info for non-existent scenario {scenario_id}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("run_scenario_"))
    def cb_run_scenario(call):
        scenario_id = int(call.data.split("_")[2])
        query = "SELECT conditions, actions FROM scenarios WHERE id = %s"
        result = execute_query(query, (scenario_id,))
        if result:
            conditions, actions = result[0]
            # Здесь нужно реализовать логику проверки условий и выполнения действий
            # В данном примере просто отправляем сообщение о запуске сценария
            bot.answer_callback_query(call.id, f"Сценарий {scenario_id} запущен.")
            logger.info(f"User {call.from_user.id} triggered scenario {scenario_id}")
        else:
            bot.answer_callback_query(call.id, "Сценарий не найден.")
            logger.warning(f"User {call.from_user.id} tried to run non-existent scenario {scenario_id}")

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("edit_scenario_") and len(call.data.split("_")) < 4)
    def cb_edit_scenario(call):
        scenario_id = int(call.data.split("_")[2])
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Выберите параметр для редактирования:",
                         reply_markup=get_edit_scenario_keyboard(scenario_id))
        logger.info(f"User {call.from_user.id} requested to edit scenario {scenario_id}")

    def get_edit_scenario_keyboard(scenario_id):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Название", callback_data=f"edit_scenario_name_{scenario_id}"))
        keyboard.add(types.InlineKeyboardButton("Тип", callback_data=f"edit_scenario_type_{scenario_id}"))
        keyboard.add(types.InlineKeyboardButton("Условия", callback_data=f"edit_scenario_conditions_{scenario_id}"))
        keyboard.add(types.InlineKeyboardButton("Действия", callback_data=f"edit_scenario_actions_{scenario_id}"))
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_scenario_name_"))
    def cb_edit_scenario_name(call):
        scenario_id = int(call.data.split("_")[3])
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Введите новое название сценария:")
        bot.register_next_step_handler(call.message, process_edit_scenario_name, scenario_id)

    def process_edit_scenario_name(message, scenario_id):
        new_name = message.text
        query = "UPDATE scenarios SET name = %s WHERE id = %s"
        execute_query(query, (new_name, scenario_id))
        bot.send_message(message.chat.id, f"Название сценария обновлено.")
        logger.info(f"User {message.from_user.id} edited name of scenario {scenario_id}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_scenario_type_"))
    def cb_edit_scenario_type(call):
        scenario_id = int(call.data.split("_")[3])
        bot.answer_callback_query(call.id)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("По умолчанию", callback_data=f"set_scenario_type_default_{scenario_id}"))
        keyboard.add(
            types.InlineKeyboardButton("Пользовательский", callback_data=f"set_scenario_type_custom_{scenario_id}"))
        bot.send_message(call.message.chat.id, "Выберите тип сценария:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_scenario_type_"))
    def cb_set_scenario_type(call):
        scenario_id = int(call.data.split("_")[3])
        scenario_type = call.data.split("_")[2]
        query = "UPDATE scenarios SET type = %s WHERE id = %s"
        execute_query(query, (scenario_type, scenario_id))
        bot.answer_callback_query(call.id, f"Тип сценария {scenario_id} изменен на {scenario_type}.")
        logger.info(f"User {call.from_user.id} set type of scenario {scenario_id} to {scenario_type}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_scenario_conditions_"))
    def cb_edit_scenario_conditions(call):
        scenario_id = int(call.data.split("_")[3])
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                         "Введите новые условия сценария в формате: Датчик_1(ЕСЛИ(><)ХХХ)ИДатчик2(=1/0)ИЛИДатчик3(>17:00)ТоДатчик4")
        bot.register_next_step_handler(call.message, process_edit_scenario_conditions, scenario_id)

    def process_edit_scenario_conditions(message, scenario_id):
        new_conditions = message.text
        query = "UPDATE scenarios SET conditions = %s WHERE id = %s"
        execute_query(query, (new_conditions, scenario_id))
        bot.send_message(message.chat.id, f"Условия сценария {scenario_id} обновлены.")
        logger.info(f"User {message.from_user.id} edited conditions of scenario {scenario_id}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_scenario_actions_"))
    def cb_edit_scenario_actions(call):
        scenario_id = int(call.data.split("_")[3])
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Введите новые действия сценария:")
        bot.register_next_step_handler(call.message, process_edit_scenario_actions, scenario_id)

    def process_edit_scenario_actions(message, scenario_id):
        new_actions = message.text
        query = "UPDATE scenarios SET actions = %s WHERE id = %s"
        execute_query(query, (new_actions, scenario_id))
        bot.send_message(message.chat.id, f"Действия сценария {scenario_id} обновлены.")
        logger.info(f"User {message.from_user.id} edited actions of scenario {scenario_id}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_scenario_"))
    def cb_delete_scenario(call):
        scenario_id = int(call.data.split("_")[2])
        query = "DELETE FROM scenarios WHERE id = %s"
        execute_query(query, (scenario_id,))
        bot.answer_callback_query(call.id, f"Сценарий {scenario_id} удален.")
        logger.info(f"User {call.from_user.id} deleted scenario {scenario_id}")
