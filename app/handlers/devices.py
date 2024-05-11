from telebot import types
from lib.db import execute_query
import logging
import cv2
import numpy as np

# Настройка логирования
logger = logging.getLogger(__name__)


def register_handlers(bot):
    @bot.message_handler(commands=['add_device'])
    def cmd_add_device(message):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Добавить контроллер", callback_data="add_controller"))
        keyboard.add(types.InlineKeyboardButton("Добавить датчик", callback_data="add_sensor"))
        bot.reply_to(message, "Выберите тип устройства для добавления:", reply_markup=keyboard)
        logger.info(f"User {message.from_user.id} requested to add a new device")

    @bot.callback_query_handler(func=lambda call: call.data == "add_controller" or call.data == "add_sensor")
    def cb_add_device(call):
        device_type = "контроллер" if call.data == "add_controller" else "датчик"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("По QR-коду", callback_data=f"{call.data}_qr"))
        keyboard.add(types.InlineKeyboardButton("По серийному номеру", callback_data=f"{call.data}_sn"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Выберите способ добавления {device_type}а:", reply_markup=keyboard)
        logger.info(f"User {call.from_user.id} requested to add a {device_type} by QR code or serial number")

    @bot.callback_query_handler(func=lambda call: call.data.endswith("_qr"))
    def cb_add_device_qr(call):
        bot.answer_callback_query(call.id)
        device_type = "контроллера" if call.data.startswith("add_controller") else "датчика"
        keyboard = types.InlineKeyboardMarkup()
        if device_type == "контроллера":
            keyboard.add(types.InlineKeyboardButton("Контроллер 1", callback_data="device_type_controller1"))
            keyboard.add(types.InlineKeyboardButton("Контроллер 2", callback_data="device_type_controller2"))
        else:
            keyboard.add(types.InlineKeyboardButton("Датчик температуры", callback_data="device_type_temperature"))
            keyboard.add(types.InlineKeyboardButton("Датчик влажности", callback_data="device_type_humidity"))
            keyboard.add(types.InlineKeyboardButton("Датчик движения", callback_data="device_type_motion"))
        bot.send_message(call.message.chat.id, f"Выберите тип {device_type}:", reply_markup=keyboard)
        logger.info(f"User {call.from_user.id} requested to select device type for {device_type}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("device_type_") and 'sn' not in call.data)
    def cb_device_type(call):
        bot.answer_callback_query(call.id)
        device_type = call.data.split("_")[2]
        bot.send_message(call.message.chat.id, f"Отправьте фото QR-кода для {device_type}.")
        bot.register_next_step_handler(call.message, process_qr_photo, device_type)
        logger.info(f"User {call.from_user.id} selected device type: {device_type}")

    def process_qr_photo(message, device_type):
        file_info = bot.get_file(message.photo[-1].file_id)
        file = bot.download_file(file_info.file_path)
        nparr = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)

        if data:
            qr_data = data.strip()
            if device_type.startswith("controller"):
                query = "INSERT INTO controllers (user_id, serial_number, type) VALUES (%s, %s, %s)"
            else:
                query = "INSERT INTO sensors (user_id, serial_number, type) VALUES (%s, %s, %s)"
            execute_query(query, (message.from_user.id, qr_data, device_type))
            bot.reply_to(message, f"{device_type} успешно добавлен.")
            logger.info(f"User {message.from_user.id} added a {device_type} with QR data: {qr_data}")
        else:
            bot.reply_to(message, "QR-код не найден на изображении. Попробуйте еще раз.")
            logger.warning(f"User {message.from_user.id} sent an image without a QR code")

    @bot.callback_query_handler(func=lambda call: call.data.endswith("_sn"))
    def cb_add_device_sn(call):
        bot.answer_callback_query(call.id)
        device_type = "контроллера" if call.data.startswith("add_controller") else "датчика"
        keyboard = types.InlineKeyboardMarkup()
        if device_type == "контроллера":
            keyboard.add(types.InlineKeyboardButton("Контроллер 1", callback_data="device_type_sn_controller1"))
            keyboard.add(types.InlineKeyboardButton("Контроллер 2", callback_data="device_type_sn_controller2"))
        else:
            keyboard.add(types.InlineKeyboardButton("Датчик температуры", callback_data="device_type_sn_temperature"))
            keyboard.add(types.InlineKeyboardButton("Датчик влажности", callback_data="device_type_sn_humidity"))
            keyboard.add(types.InlineKeyboardButton("Датчик движения", callback_data="device_type_sn_motion"))
        bot.send_message(call.message.chat.id, f"Выберите тип {device_type}:", reply_markup=keyboard)
        logger.info(f"User {call.from_user.id} requested to select device type for {device_type} (serial number)")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("device_type_sn_"))
    def cb_device_type_sn(call):
        bot.answer_callback_query(call.id)
        device_type = call.data.split("_")[3]
        bot.send_message(call.message.chat.id, f"Введите серийный номер для {device_type}.")
        bot.register_next_step_handler(call.message, process_serial_number, device_type)
        logger.info(f"User {call.from_user.id} selected device type: {device_type} (serial number)")

    def process_serial_number(message, device_type):
        serial_number = message.text.strip()
        if device_type.startswith("controller"):
            query = "INSERT INTO controllers (user_id, serial_number, type) VALUES (%s, %s, %s)"
        else:
            query = "INSERT INTO sensors (user_id, serial_number, type) VALUES (%s, %s, %s)"
        execute_query(query, (message.from_user.id, serial_number, device_type))
        bot.reply_to(message, f"{device_type} успешно добавлен.")
        logger.info(f"User {message.from_user.id} added a {device_type} with serial number: {serial_number}")

    @bot.message_handler(commands=['list_devices'])
    def cmd_list_devices(message):
        user_id = message.from_user.id
        query = "SELECT id, type, serial_number FROM controllers WHERE user_id = %s"
        devices = execute_query(query, (user_id,))

        if devices:
            keyboard = types.InlineKeyboardMarkup()
            for device_id, device_type, serial_number in devices:
                device_info = f"{device_type} ({serial_number})"
                keyboard.add(types.InlineKeyboardButton(device_info, callback_data=f"delete_device_{device_id}"))
            bot.reply_to(message, "Список ваших устройств:", reply_markup=keyboard)
            logger.info(f"User {user_id} requested device list")
        else:
            bot.reply_to(message, "У вас пока нет добавленных устройств.")
            logger.info(f"User {user_id} has no devices")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_device_"))
    def cb_delete_device(call):
        user_id = call.from_user.id
        device_id = call.data.split("_")[2]
        query = "DELETE FROM devices WHERE id = %s AND user_id = %s"
        execute_query(query, (device_id, user_id))

        bot.answer_callback_query(call.id, text=f"Устройство с ID {device_id} успешно удалено.")
        logger.info(f"User {user_id} deleted device with ID {device_id}")

    @bot.message_handler(commands=['list_sensors'])
    def cmd_list_sensors(message):
        user_id = message.from_user.id
        query = "SELECT id, type, serial_number FROM sensors WHERE user_id = %s"
        sensors = execute_query(query, (user_id,))

        if sensors:
            keyboard = types.InlineKeyboardMarkup()
            for sensor_id, sensor_type, serial_number in sensors:
                sensor_info = f"{sensor_type} ({serial_number})"
                keyboard.add(types.InlineKeyboardButton(sensor_info, callback_data=f"delete_sensor_{sensor_id}"))
            bot.reply_to(message, "Список ваших датчиков:", reply_markup=keyboard)
            logger.info(f"User {user_id} requested sensor list")
        else:
            bot.reply_to(message, "У вас пока нет добавленных датчиков.")
            logger.info(f"User {user_id} has no sensors")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_sensor_"))
    def cb_delete_sensor(call):
        user_id = call.from_user.id
        sensor_id = call.data.split("_")[2]
        query = "DELETE FROM sensors WHERE id = %s AND user_id = %s"
        execute_query(query, (sensor_id, user_id))

        bot.answer_callback_query(call.id, text=f"Датчик с ID {sensor_id} успешно удален.")
        logger.info(f"User {user_id} deleted sensor with ID {sensor_id}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_scenario_"))
    def cb_delete_scenario(call):
        user_id = call.from_user.id
        scenario_id = call.data.split("_")[2]
        query = "DELETE FROM scenarios WHERE id = %s AND user_id = %s"
        execute_query(query, (scenario_id, user_id))

        bot.answer_callback_query(call.id, text=f"Сценарий с ID {scenario_id} успешно удален.")
        logger.info(f"User {user_id} deleted scenario with ID {scenario_id}")

    @bot.message_handler(commands=['sensors'])
    def cmd_sensors(message):
        user_id = message.from_user.id
        query = "SELECT id, type, value FROM sensors WHERE user_id = %s"
        sensors = execute_query(query, (user_id,))

        if sensors:
            sensor_list = "Ваши датчики:\n"
            for sensor_id, sensor_type, sensor_value in sensors:
                sensor_list += f"{sensor_type}: {sensor_value}\n"
            bot.reply_to(message, sensor_list)
            logger.info(f"User {user_id} requested sensor list")
        else:
            bot.reply_to(message, "У вас пока нет датчиков.")
            logger.info(f"User {user_id} has no sensors")

    @bot.message_handler(commands=['sensor_info'])
    def cmd_sensor_info(message):
        sensor_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        if sensor_id:
            query = "SELECT type, serial_number, status FROM sensors WHERE id = %s"
            result = execute_query(query, (sensor_id,))
            if result:
                sensor_type, sensor_serial, sensor_status = result[0]
                sensor_info = f"Информация о датчике {sensor_id}:\nТип: {sensor_type}\nСерийный номер: {sensor_serial}\nСостояние: {sensor_status}"
                bot.reply_to(message, sensor_info)
                logger.info(f"User {message.from_user.id} requested info for sensor {sensor_id}")
            else:
                bot.reply_to(message, "Датчик не найден.")
                logger.warning(f"User {message.from_user.id} requested info for non-existent sensor {sensor_id}")
        else:
            bot.reply_to(message, "Укажите ID датчика.")
            logger.warning(f"User {message.from_user.id} requested sensor info without providing sensor ID")

    @bot.message_handler(commands=['siren'])
    def cmd_siren(message):
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if len(args) == 2:
            device_id, sound_message = args
            bot.reply_to(message, f"Звуковое оповещение «{sound_message}» включено на устройстве {device_id}.")
            logger.info(
                f"User {message.from_user.id} triggered siren on device {device_id} with message: {sound_message}")
        else:
            bot.reply_to(message, "Укажите ID устройства и звуковое сообщение.")
            logger.warning(f"User {message.from_user.id} triggered siren without providing device ID and sound message")

    @bot.message_handler(commands=['motor'])
    def cmd_motor(message):
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if len(args) == 2:
            device_id, duration = args
            bot.reply_to(message, f"Моторчик устройства {device_id} включен на {duration} секунд.")
            logger.info(f"User {message.from_user.id} triggered motor on device {device_id} for {duration} seconds")
        else:
            bot.reply_to(message, "Укажите ID устройства и длительность работы моторчика.")
            logger.warning(f"User {message.from_user.id} triggered motor without providing device ID and duration")

    @bot.message_handler(commands=['notify'])
    def cmd_notify(message):
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if len(args) == 2:
            phone_number, notification = args
            bot.reply_to(message, f"Уведомление «{notification}» отправлено на номер {phone_number}.")
            logger.info(f"User {message.from_user.id} sent notification to {phone_number}: {notification}")
        else:
            bot.reply_to(message, "Укажите номер телефона и текст уведомления.")
            logger.warning(
                f"User {message.from_user.id} tried to send notification without providing phone number and text")

    @bot.message_handler(commands=['relay'])
    def cmd_relay(message):
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if len(args) == 2:
            device_id, signal = args
            bot.reply_to(message, f"Реле устройства {device_id} переключено сигналом «{signal}».")
            logger.info(f"User {message.from_user.id} switched relay on device {device_id} with signal {signal}")
        else:
            bot.reply_to(message, "Укажите ID устройства и управляющий сигнал.")
            logger.warning(f"User {message.from_user.id} switched relay without providing device ID and signal")