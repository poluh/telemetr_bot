import random
import logging

from app.lib.db import execute_query

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_sensor_data(sensor_type):
    if sensor_type == "temperature":
        value = round(random.uniform(-10, 40), 1)
        logger.debug(f"Generated temperature value: {value}")
        return value
    elif sensor_type == "humidity":
        value = random.randint(0, 100)
        logger.debug(f"Generated humidity value: {value}")
        return value
    elif sensor_type == "motion":
        value = random.choice([0, 1])
        logger.debug(f"Generated motion value: {value}")
        return value
    else:
        logger.warning(f"Unknown sensor type: {sensor_type}")
        return None

def update_sensor_data():
    query = "SELECT id, type FROM sensors"
    sensors = execute_query(query)
    for sensor_id, sensor_type in sensors:
        sensor_value = generate_sensor_data(sensor_type)
        if sensor_value is not None:
            query = "UPDATE sensors SET value = %s WHERE id = %s"
            execute_query(query, (sensor_value, sensor_id))
            logger.info(f"Updated sensor {sensor_id} with value {sensor_value}")
        else:
            logger.warning(f"Failed to update sensor {sensor_id} due to unknown type")