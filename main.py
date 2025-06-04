# Список разрешенных user_id (узнать можно через @userinfobot в Telegram)
ALLOWED_USERS = {
    504550373,  # Замените на реальные ID
    431085762,
    595500438
}

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackContext, CallbackQueryHandler, ConversationHandler
)
from dotenv import load_dotenv
import os
from database import get_db
import mysql.connector
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Загружаем токен из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Состояния для ConversationHandler
EDIT_SELECT, EDIT_FIELD = range(2)
ADD_DRIVER_NAME, ADD_DRIVER_PHONE, ADD_DRIVER_EMAIL, ADD_DRIVER_LOCATION, ADD_DRIVER_DAY = range(5)
ADD_TRAILER_TYPE, ADD_TRAILER_LENGTH, ADD_TRAILER_BEE_NETS, ADD_TRAILER_EQUIPMENT, ADD_TRAILER_MC = range(5, 10)

# Текущее меню пользователя и данные поиска
user_states = {}
search_results = {}

# Стартовое меню
async def start_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 Access denied!")
        return
    
    user_states[user_id] = {"state": "start"}
    keyboard = [["ℹ️ Drivers information"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "╔Welcome to the management system!\n║⚙️ Select operation:",
        reply_markup=reply_markup
    )

# Меню Drivers information
async def driver_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "driver_menu"}
    
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM driver_info")
    drivers_count = cursor.fetchone()[0]
    connection.close()

    message = (
        f"╔ Driver Management Panel \n"
        f"║👔Total drivers: {drivers_count}\n"
        "║⚙️Select operation:"
    )
    
    keyboard = [
        ["👀 View driver info"],
        ["🆕 Add driver"],
        ["🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Начало добавления водителя
async def add_new_driver(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "add_driver"}
    
    # Инициализация временных данных
    context.user_data['new_driver'] = {}
    
    await update.message.reply_text(
        "📝Fill all information:\n\n"
        "💼Step 1/9: Enter driver's *full name*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_NAME

# Обработка имени водителя
async def add_driver_name(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    
    context.user_data['new_driver']['name'] = update.message.text
    await update.message.reply_text(
        "💼Step 2/9: Enter driver's *phone number* (e.g., 123-456-7890):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_PHONE

# Обработка телефона
async def add_driver_phone(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 1/9: Enter driver's *full name* (current: {}):".format(
                context.user_data['new_driver'].get('name', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_NAME
    
    context.user_data['new_driver']['phone'] = update.message.text
    await update.message.reply_text(
        "💼Step 3/9: Enter driver's *email* (or type 'skip' if none):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_EMAIL

# Обработка email
async def add_driver_email(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 2/9: Enter driver's *phone number* (current: {}):".format(
                context.user_data['new_driver'].get('phone', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_PHONE
    
    email = update.message.text
    if email.lower() != 'skip':
        context.user_data['new_driver']['email'] = email
    await update.message.reply_text(
        "💼Step 4/9: Enter driver's *current location* (state, e.g., TX):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_LOCATION

# Обработка локации
async def add_driver_location(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 3/9: Enter driver's *email* (current: {}):".format(
                context.user_data['new_driver'].get('email', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_EMAIL
    
    context.user_data['new_driver']['location'] = update.message.text
    await update.message.reply_text(
        "💼Step 5/9: Enter driver's *availability* (e.g., Mon-Fri):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_DAY

# Обработка дней работы
async def add_driver_day(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 4/9: Enter driver's *current location* (current: {}):".format(
                context.user_data['new_driver'].get('location', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_LOCATION
    
    context.user_data['new_driver']['day'] = update.message.text
    await update.message.reply_text(
        "💼Step 6/9: Enter *trailer type* (flatbed, stepdeck, van, reefer):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_TYPE

# Обработка типа трейлера
# Обработка типа трейлера (принимаем любой текст)
async def add_trailer_type(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 5/9: Enter driver's *availability* (current: {}):".format(
                context.user_data['new_driver'].get('day', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_DAY
    
    # Принимаем ЛЮБОЙ текст как тип трейлера
    context.user_data['new_driver']['trailer_type'] = update.message.text
    
    # Всегда спрашиваем длину (независимо от типа трейлера)
    await update.message.reply_text(
        "💼Step 7/9: Enter trailer *length* (можно ввести любое число):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_LENGTH

# Обработка длины трейлера (принимаем любое число)
async def add_trailer_length(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 6/9: Enter *trailer type* (current: {}):".format(
                context.user_data['new_driver'].get('trailer_type', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_TRAILER_TYPE
    
    # Проверяем, что введено число (положительное)
    try:
        length = int(update.message.text)
        if length < 0:
            await update.message.reply_text("Длина не может быть отрицательной. Введите положительное число:")
            return ADD_TRAILER_LENGTH
        context.user_data['new_driver']['length'] = length
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число для длины трейлера:")
        return ADD_TRAILER_LENGTH
    
    await update.message.reply_text(
        "💼Step 8/9: Does the trailer have *bee nets*? (можно ввести любой текст):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_BEE_NETS

# Обработка bee nets (принимаем любой текст)
async def add_trailer_bee_nets(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        # Всегда возвращаем к длине, так как она запрашивается для всех типов
        await update.message.reply_text(
            "💼Step 7/9: Enter trailer *length* (current: {}):".format(
                context.user_data['new_driver'].get('length', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_TRAILER_LENGTH
    
    # Принимаем ЛЮБОЙ текст для bee nets
    context.user_data['new_driver']['bee_nets'] = update.message.text
    
    await update.message.reply_text(
        "💼Step 9/9: Enter *special equipment* (можно ввести любой текст или 'none'):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_EQUIPMENT

# Обработка спец. оборудования
async def add_trailer_equipment(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 8/9: Does the trailer have *bee nets*? (current: {}):".format(
                context.user_data['new_driver'].get('bee_nets', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_TRAILER_BEE_NETS
    
    equipment = update.message.text
    if equipment.lower() != 'none':
        context.user_data['new_driver']['equipment'] = equipment
    await update.message.reply_text(
        "💼Final step: Enter *MC number* (or 'skip' if none):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_MC

# Обработка MC номера и сохранение в БД
async def add_trailer_mc(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)  # Возврат в driver_information
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 9/9: Enter *special equipment* (current: {}):".format(
                context.user_data['new_driver'].get('equipment', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_TRAILER_EQUIPMENT
    
    mc = update.message.text
    if mc.lower() != 'skip':
        context.user_data['new_driver']['mc'] = int(mc) if mc.isdigit() else None
    
    try:
        connection = get_db()
        cursor = connection.cursor()
        
        # Добавляем водителя
        cursor.execute(
            """
            INSERT INTO driver_info 
            (name, phone_number, email, current_location, current_day_of_week)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                context.user_data['new_driver']['name'],
                context.user_data['new_driver'].get('phone'),
                context.user_data['new_driver'].get('email'),
                context.user_data['new_driver'].get('location'),
                context.user_data['new_driver'].get('day')
            )
        )
        driver_id = cursor.lastrowid
        
        # Добавляем трейлер
        cursor.execute(
            """
            INSERT INTO trailer_info 
            (driver_id, trailer_type, length, bee_nets, special_equipment, MC)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                driver_id,
                context.user_data['new_driver'].get('trailer_type'),
                context.user_data['new_driver'].get('length'),
                context.user_data['new_driver'].get('bee_nets'),
                context.user_data['new_driver'].get('equipment'),
                context.user_data['new_driver'].get('mc')
            )
        )
        
        connection.commit()
        await update.message.reply_text(
            "✅ Driver added successfully!",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        await driver_information(update, context)  # Возвращаем в меню driver_information
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if connection.is_connected():
            connection.close()
    
    context.user_data.pop('new_driver', None)
    return ConversationHandler.END

# Меню поиска водителей
async def search_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "search_menu"}
    
    message = "║🕵🏻Select search method:"
    keyboard = [
        ["📟 By name"],
        ["🔧 By trailer"],
        ["🗺️ By location"],
        ["🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Меню поиска по имени
async def search_by_name(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "search_by_name"}
    
    message = "║🚧Enter letter/name of the driver:"
    keyboard = [["🔙 Back"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Меню поиска по локации
async def search_by_location(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "search_by_location"}
    
    message = "║🗺️Select current location (enter state abbreviation, e.g. TX):"
    keyboard = [["🔙 Back"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Меню поиска по трейлеру
async def search_by_trailer(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "search_by_trailer"}
    
    message = "║🚚Select trailer:"
    keyboard = [
        ["🚛 Flatbed 48", "🚛 Flatbed 53"],
        ["🚚 Stepdeck 48", "🚚 Stepdeck 53"],
        ["🚐 Van"],
        ["❄️ Reefer"],
        ["🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Обработка выбранного трейлера и вывод результатов
async def by_trailer_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    trailer_text = update.message.text.strip()  # Не применяем .lower() сразу, чтобы сохранить регистр для отображения
    
    # Сопоставляем текст кнопки с реальными значениями в БД
    trailer_mapping = {
        "❄️ Reefer": "reefer",  # Если пользователь нажал "❄️ Reefer", ищем "reefer" в БД
        "🚛 Flatbed 48": "flatbed 48",
        "🚛 Flatbed 53": "flatbed 53",
        "🚚 Stepdeck 48": "stepdeck 48",
        "🚚 Stepdeck 53": "stepdeck 53",
        "🚐 Van": "van"
    }
    
    # Получаем значение для поиска в БД
    trailer_db_value = trailer_mapping.get(trailer_text)
    if not trailer_db_value:
        await update.message.reply_text(
            "Invalid trailer format. Please select from the options.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return
    
    # Разбираем тип и длину трейлера
    if trailer_db_value in ["van", "reefer"]:
        trailer_type = trailer_db_value
        length = None
    else:
        parts = trailer_db_value.split()
        trailer_type, length_str = parts[0], parts[1]
        try:
            length = int(length_str)
        except ValueError:
            await update.message.reply_text(
                "Invalid length. Please select from the options.",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
            )
            return
    
    # Запрос к БД
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    if length is not None:
        cursor.execute(
            """
            SELECT di.driver_id, di.name 
            FROM driver_info di
            JOIN trailer_info ti ON di.driver_id = ti.driver_id
            WHERE ti.trailer_type = %s AND ti.length = %s
            ORDER BY di.name
            """,
            (trailer_type, length)
        )
    else:
        cursor.execute(
            """
            SELECT di.driver_id, di.name 
            FROM driver_info di
            JOIN trailer_info ti ON di.driver_id = ti.driver_id
            WHERE ti.trailer_type = %s
            ORDER BY di.name
            """,
            (trailer_type,)
        )
    
    drivers = cursor.fetchall()
    connection.close()
    
    if not drivers:
        await update.message.reply_text(
            f"There are no drivers with trailer [{trailer_text}]\nPlease try again",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return
    
    # Сохраняем оригинальный текст (с эмодзи) для отображения
    search_results[user_id] = {
        "drivers": drivers,
        "current_page": 0,
        "search_text": trailer_text  # Сохраняем "❄️ Reefer", а не "reefer"
    }
    
    await show_drivers_page(update, context, user_id)

# Обработка введенного имени и вывод результатов
async def by_name_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    search_text = update.message.text.strip()
    
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    # Измененный запрос - ищем подстроку в любом месте имени
    query = """
        SELECT driver_id, name 
        FROM driver_info 
        WHERE name LIKE %s 
        ORDER BY name
    """
    cursor.execute(query, (f"%{search_text}%",))  # Добавляем % с обеих сторон
    
    drivers = cursor.fetchall()
    connection.close()
    
    if not drivers:
        await update.message.reply_text(
            f"There are no drivers with name containing [{search_text}]\nPlease try again",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return
    
    # Сохраняем результаты поиска
    search_results[user_id] = {
        "drivers": drivers,
        "current_page": 0,
        "search_text": search_text
    }
    
    await show_drivers_page(update, context, user_id)

# Обработка введенной локации и вывод результатов
async def by_location_information(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    location_text = update.message.text.strip().upper()
    
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT driver_id, name FROM driver_info WHERE current_location LIKE %s ORDER BY name"
    cursor.execute(query, (f"%{location_text}",))
    drivers = cursor.fetchall()
    connection.close()
    
    if not drivers:
        await update.message.reply_text(
            f"There are no drivers in state [{location_text}]\nPlease try again",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return
    
    # Сохраняем результаты поиска
    search_results[user_id] = {
        "drivers": drivers,
        "current_page": 0,
        "search_text": location_text
    }
    
    await show_drivers_page(update, context, user_id)

# Показать страницу с водителями
async def show_drivers_page(update: Update, context: CallbackContext, user_id: int):
    data = search_results[user_id]
    drivers = data["drivers"]
    current_page = data["current_page"]
    search_text = data["search_text"]
    
    total_pages = (len(drivers) + 9) // 10
    start_index = current_page * 10
    end_index = start_index + 10
    page_drivers = drivers[start_index:end_index]
    
    # Создаем интерактивные кнопки
    keyboard = []
    for driver in page_drivers:
        keyboard.append([InlineKeyboardButton(
            f"{driver['name']} (ID: {driver['driver_id']})",
            callback_data=f"driver_{driver['driver_id']}"
        )])
    
    # Кнопки пагинации
    pagination = []
    if current_page > 0:
        pagination.append(InlineKeyboardButton("⬅️ Previous", callback_data="prev_page"))
    if end_index < len(drivers):
        if pagination:
            pagination.append(InlineKeyboardButton("│", callback_data="none"))
        pagination.append(InlineKeyboardButton("Next ➡️", callback_data="next_page"))
    
    if pagination:
        keyboard.append(pagination)
    
    # Определяем тип поиска для сообщения
    if " " in search_text:  # Для трейлеров с длиной (flatbed 48 и т.д.)
        message = f"║👇Here are all drivers with {search_text} trailer\n(page {current_page + 1} of {total_pages})"
    elif search_text in ["van", "reefer"]:
        message = f"║👇Here are all drivers with {search_text} trailer\n(page {current_page + 1} of {total_pages})"
    elif len(search_text) == 2 and search_text.isupper():  # Для локаций (штатов)
        message = f"║👇Here are all drivers in state '{search_text}'\n(page {current_page + 1} of {total_pages})"
    else:  # Для имен
        message = f"║👇Here are all drivers with name starting with '{search_text}'\n(page {current_page + 1} of {total_pages})"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Показать полную информацию о водителе
async def all_driver_information(update: Update, context: CallbackContext, driver_id: int):
    # Сохраняем driver_id в контексте
    context.user_data['current_driver_id'] = driver_id
    
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT di.*, ti.trailer_type, ti.length, ti.bee_nets, ti.special_equipment, ti.MC 
        FROM driver_info di
        LEFT JOIN trailer_info ti ON di.driver_id = ti.driver_id
        WHERE di.driver_id = %s
    """, (driver_id,))
    
    driver = cursor.fetchone()
    connection.close()
    
    if not driver:
        await update.callback_query.answer("Driver not found!")
        return
    
    # Форматирование длины трейлера
    length_display = str(driver['length']) + " ft" if driver.get('length') is not None else "Not specified"
    
    message = (
        f"👨🏻‍💼 *Driver Information*\n"
        f"🆔 *ID:* {driver['driver_id']}\n\n"
        f"📟 *Name:* {driver['name']}\n"
        f"📞 *Phone:* {driver['phone_number'] or 'Not specified'}\n"
        f"📧 *Email:* {driver['email'] or 'Not specified'}\n\n"
        f"🗺️ *Location:* {driver['current_location'] or 'Not specified'}\n"
        f"📅 *Available:* {driver['current_day_of_week'] or 'Not specified'}\n\n"
        f"🚚 *Trailer information*\n\n"
        f"🔧 *Trailer Type:* {driver['trailer_type'].capitalize() if driver.get('trailer_type') else 'Not specified'}\n"
        f"📏 *Length:* {length_display}\n"
        f"🐝 *Bee Nets:* {driver.get('bee_nets') or 'Not specified'}\n"  # Показываем как есть
        f"🛠️ *Special Equipment:* {driver.get('special_equipment') or 'Not specified'}\n\n"
        f"🔢 *MC Number:* {driver.get('MC') or 'Not specified'}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit information", callback_data="edit_select")],
        [InlineKeyboardButton("🗑️ Delete driver", callback_data=f"confirm_delete_{driver_id}")],
        [InlineKeyboardButton("↩️ Return", callback_data="return_to_list")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def confirm_delete_driver(update: Update, context: CallbackContext, driver_id: int):
    message = "⚠️ *Are You sure?*"
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data=f"delete_yes_{driver_id}")],
        [InlineKeyboardButton("❌ No", callback_data=f"delete_no_{driver_id}")]
    ]
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def delete_driver(update: Update, context: CallbackContext, driver_id: int):
    user_id = update.callback_query.from_user.id
    
    try:
        connection = get_db()
        cursor = connection.cursor()
        
        # Удаляем сначала трейлер (из-за foreign key)
        cursor.execute("DELETE FROM trailer_info WHERE driver_id = %s", (driver_id,))
        # Затем удаляем водителя
        cursor.execute("DELETE FROM driver_info WHERE driver_id = %s", (driver_id,))
        
        connection.commit()
        connection.close()
        
        # Удаляем из результатов поиска, если есть
        if user_id in search_results:
            search_results[user_id]["drivers"] = [
                d for d in search_results[user_id]["drivers"] 
                if d['driver_id'] != driver_id
            ]
        
        await update.callback_query.answer("Driver deleted successfully!")
        await show_drivers_page(update, context, user_id)
        
    except Exception as e:
        await update.callback_query.answer(f"Error deleting driver: {str(e)}", show_alert=True)

async def edit_select(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📟Name", callback_data="edit_name")],
        [InlineKeyboardButton("📞Phone number", callback_data="edit_phone")],
        [InlineKeyboardButton("📧Email", callback_data="edit_email")],
        [InlineKeyboardButton("🗺️Current location", callback_data="edit_location")],
        [InlineKeyboardButton("📅Current day of week", callback_data="edit_day")],
        [InlineKeyboardButton("🔧Trailer type", callback_data="edit_trailer_type")],
        [InlineKeyboardButton("📏Length", callback_data="edit_length")],
        [InlineKeyboardButton("🐝Bee nets", callback_data="edit_bee_nets")],
        [InlineKeyboardButton("🛠️Special equipment", callback_data="edit_equipment")],
        [InlineKeyboardButton("🔢MC Number", callback_data="edit_mc")],
        [InlineKeyboardButton("↩️Come back", callback_data="edit_come_back")]
    ]
    
    await update.callback_query.edit_message_text(
        text="Select what You wanna edit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_SELECT

async def edit_field(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    field = query.data
    
    if field == "edit_come_back":
        driver_id = context.user_data['current_driver_id']
        await all_driver_information(update, context, driver_id)
        return ConversationHandler.END
    
    context.user_data['edit_field'] = field
    
    field_names = {
        "edit_name": "📟Name",
        "edit_phone": "📞Phone number",
        "edit_email": "📧Email",
        "edit_location": "🗺️Current location",
        "edit_day": "📅Current day of week",
        "edit_trailer_type": "🔧Trailer type",
        "edit_length": "📏Length",
        "edit_bee_nets": "🐝Bee nets",
        "edit_equipment": "🛠️Special equipment",
        "edit_mc": "🔢MC Number"
    }
    
    keyboard = [
        [InlineKeyboardButton("Cancel", callback_data="edit_cancel")]
    ]
    
    await query.edit_message_text(
        text=f"Edit {field_names[field]}, write new information",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_FIELD

async def save_edit(update: Update, context: CallbackContext):
    # Проверяем, не является ли текст кнопкой Back
    if update.message.text == "🔙 Back":
        await search_information(update, context)
        return ConversationHandler.END
    
    driver_id = context.user_data['current_driver_id']
    field = context.user_data['edit_field']
    new_value = update.message.text
    
    field_mapping = {
        "edit_name": ("driver_info", "name"),
        "edit_phone": ("driver_info", "phone_number"),
        "edit_email": ("driver_info", "email"),
        "edit_location": ("driver_info", "current_location"),
        "edit_day": ("driver_info", "current_day_of_week"),
        "edit_trailer_type": ("trailer_info", "trailer_type"),
        "edit_length": ("trailer_info", "length"),
        "edit_bee_nets": ("trailer_info", "bee_nets"),
        "edit_equipment": ("trailer_info", "special_equipment"),
        "edit_mc": ("trailer_info", "MC")
    }
    
    table, column = field_mapping[field]
    
    try:
        connection = get_db()
        cursor = connection.cursor()
        
        # Для числовых полей проверяем корректность значения
        if column in ['length', 'MC']:
            try:
                new_value = int(new_value)
            except ValueError:
                raise ValueError(f"Invalid value for {column}. Please enter a number.")
        
        if table == "driver_info":
            cursor.execute(f"""
                UPDATE driver_info SET {column} = %s 
                WHERE driver_id = %s
            """, (new_value, driver_id))
        else:
            # Проверяем, есть ли уже запись в trailer_info
            cursor.execute("""
                SELECT 1 FROM trailer_info WHERE driver_id = %s
            """, (driver_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute(f"""
                    UPDATE trailer_info SET {column} = %s 
                    WHERE driver_id = %s
                """, (new_value, driver_id))
            else:
                # Создаем новую запись, если ее нет
                cursor.execute("""
                    INSERT INTO trailer_info 
                    (driver_id, trailer_type, length, bee_nets, special_equipment, MC)
                    VALUES (%s, NULL, NULL, NULL, NULL, NULL)
                """, (driver_id,))
                connection.commit()
                cursor.execute(f"""
                    UPDATE trailer_info SET {column} = %s 
                    WHERE driver_id = %s
                """, (new_value, driver_id))
        
        connection.commit()
        await update.message.reply_text("✅ Information updated successfully!")
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    except mysql.connector.Error as e:
        await update.message.reply_text(f"❌ Database error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    
    # Очищаем поле редактирования
    context.user_data.pop('edit_field', None)
    
    # Возвращаемся к информации о водителе
    await all_driver_information(update, context, driver_id)
    return ConversationHandler.END

async def edit_cancel(update: Update, context: CallbackContext):
    await edit_select(update, context)
    return EDIT_SELECT

# Обработчик всех текстовых сообщений
async def handle_text(update: Update, context: CallbackContext) -> None:
    # Если находимся в режиме редактирования, передаем обработку save_edit
    if context.user_data.get('edit_field'):
        await save_edit(update, context)
        return
    
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_states:
        await start_information(update, context)
        return
    
    if text == "🔙 Back":
        current_state = user_states[user_id]["state"]
        if current_state == "driver_menu":
            await start_information(update, context)
        elif current_state == "search_menu":
            await driver_information(update, context)
        elif current_state == "search_by_name":
            await search_information(update, context)
        elif current_state == "search_by_location":
            await search_information(update, context)
        elif current_state == "search_by_trailer":
            await search_information(update, context)
        return
    
    if text == "ℹ️ Drivers information":
        await driver_information(update, context)
    elif text == "👀 View driver info":
        await search_information(update, context)
    elif text == "📟 By name":
        await search_by_name(update, context)
    elif text == "🗺️ By location":
        await search_by_location(update, context)
    elif text == "🔧 By trailer":
        await search_by_trailer(update, context)
    elif user_states[user_id]["state"] == "search_by_name":
        await by_name_information(update, context)
    elif user_states[user_id]["state"] == "search_by_location":
        await by_location_information(update, context)
    elif user_states[user_id]["state"] == "search_by_trailer":
        await by_trailer_information(update, context)
    else:
        await start_information(update, context)

# Обновленный обработчик кнопок
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "prev_page":
        search_results[user_id]["current_page"] -= 1
        await show_drivers_page(update, context, user_id)
    elif data == "next_page":
        search_results[user_id]["current_page"] += 1
        await show_drivers_page(update, context, user_id)
    elif data.startswith("driver_"):
        driver_id = int(data.split("_")[1])
        await all_driver_information(update, context, driver_id)
    elif data == "return_to_list":
        await show_drivers_page(update, context, user_id)
    elif data.startswith("confirm_delete_"):
        driver_id = int(data.split("_")[2])
        await confirm_delete_driver(update, context, driver_id)
    elif data.startswith("delete_no_"):
        driver_id = int(data.split("_")[2])
        await all_driver_information(update, context, driver_id)
    elif data.startswith("delete_yes_"):
        driver_id = int(data.split("_")[2])
        await delete_driver(update, context, driver_id)
    elif data == "edit_select":
        await edit_select(update, context)
    elif data == "edit_cancel":
        await edit_cancel(update, context)
    elif data.startswith("edit_"):
        await edit_field(update, context)

def main() -> None:
    print("Бот запущен")
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # ConversationHandler для добавления водителя
        add_driver_conv = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^🆕 Add driver$"), add_new_driver)
            ],
            states={
                ADD_DRIVER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_driver_name)],
                ADD_DRIVER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_driver_phone)],
                ADD_DRIVER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_driver_email)],
                ADD_DRIVER_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_driver_location)],
                ADD_DRIVER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_driver_day)],
                ADD_TRAILER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_type)],
                ADD_TRAILER_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_length)],
                ADD_TRAILER_BEE_NETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_bee_nets)],
                ADD_TRAILER_EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_equipment)],
                ADD_TRAILER_MC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_mc)],
            },
            fallbacks=[]  # Убрали ненужный обработчик
        )
        
        # Остальные обработчики
        application.add_handler(CommandHandler("start", start_information))
        application.add_handler(add_driver_conv)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\nБот остановлен")

if __name__ == "__main__":
    main()