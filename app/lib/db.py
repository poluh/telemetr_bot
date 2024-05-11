import os
import logging
import psycopg2
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)


# Подключение к базе данных
def connect_db():
    try:
        conn = psycopg2.connect(
            host='147.45.137.120',
            port='5432',
            database='postgres',
            user='strong_user',
            password='strong_pass$4'
        )
        logger.info("Connected to the database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        return None


# Функция для выполнения SQL-запросов
def execute_query(query, params=None, return_id=False):
    conn = connect_db()
    if return_id:
        query = query + " RETURNING id"
    logger.info(f"Executed query: {query}")
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if return_id:
                    query_result = cur.fetchone()
                    if query_result:
                        return query_result[0]
                else:
                    if cur.description:
                        query_result = cur.fetchall()
                    else:
                        query_result = None
                conn.commit()
                return query_result
        except psycopg2.Error as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
        finally:
            conn.close()
            logger.info("Disconnected from the database")
    return None