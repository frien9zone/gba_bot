import mysql.connector
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()

# Функция для подключения к базе данных
def get_db():
    """Возвращает подключение к MySQL."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )