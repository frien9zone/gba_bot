import mysql.connector
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()

# Функция для подключения к базе данных
def get_db():
    """Возвращает подключение к MySQL с поддержкой SSL."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca="/root/gba_bot/ca-certificate.crt"  # путь к сертификату на сервере
    )
