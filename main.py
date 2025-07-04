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
ADD_TRAILER_TOTAL, ADD_FLAT_48, ADD_FLAT_53, ADD_STEP_48, ADD_STEP_53, ADD_BEE_EQUIPMENT, ADD_NOTES, ADD_COMPANY, ADD_TRAILER_MC = range(9, 18)

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
        "💼Step 1/14: Enter driver's *full name*:",
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
        "💼Step 2/14: Enter driver's *phone number* (e.g., 123-456-7890):",
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
            "💼Step 1/14: Enter driver's *full name* (current: {}):".format(
                context.user_data['new_driver'].get('name', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_NAME
    
    context.user_data['new_driver']['phone'] = update.message.text
    await update.message.reply_text(
        "💼Step 3/14: Enter driver's *email* (or type 'skip' if none):",
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
            "💼Step 2/14: Enter driver's *phone number* (current: {}):".format(
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
        "💼Step 4/14: Enter driver's *current location* (state, e.g., TX):",
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
            "💼Step 3/14: Enter driver's *email* (current: {}):".format(
                context.user_data['new_driver'].get('email', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_EMAIL
    
    context.user_data['new_driver']['location'] = update.message.text
    await update.message.reply_text(
        "💼Step 5/14: Enter driver's *availability* (e.g., Mon-Fri):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_DRIVER_DAY

# Обработка дней работы
async def add_driver_day(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 4/14: Enter driver's *current location* (current: {}):".format(
                context.user_data['new_driver'].get('location', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_LOCATION
    
    context.user_data['new_driver']['day'] = update.message.text
    await update.message.reply_text(
        "💼Step 6/14: Enter *total amount of trailers*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_TOTAL

async def add_trailer_total(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 5/14: Enter driver's *availability* (current: {}):".format(
                context.user_data['new_driver'].get('day', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_DRIVER_DAY
    
    context.user_data['new_driver']['total_amount'] = update.message.text
    await update.message.reply_text(
        "💼Step 7/14: Enter *number of Flatbed 48' trailers*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_FLAT_48

async def add_flat_48(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 6/14: Enter *total amount of trailers* (current: {}):".format(
                context.user_data['new_driver'].get('total_amount', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_TRAILER_TOTAL
    
    context.user_data['new_driver']['flat_48'] = update.message.text
    await update.message.reply_text(
        "💼Step 8/14: Enter *number of Flatbed 53' trailers*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_FLAT_53

async def add_flat_53(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 7/14: Enter *number of Flatbed 48' trailers* (current: {}):".format(
                context.user_data['new_driver'].get('flat_48', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_FLAT_48
    
    context.user_data['new_driver']['flat_53'] = update.message.text
    await update.message.reply_text(
        "💼Step 9/14: Enter *number of Stepdeck 48' trailers*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_STEP_48

async def add_step_48(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 8/14: Enter *number of Flatbed 53' trailers* (current: {}):".format(
                context.user_data['new_driver'].get('flat_53', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_FLAT_53
    
    context.user_data['new_driver']['step_48'] = update.message.text
    await update.message.reply_text(
        "💼Step 10/14: Enter *number of Stepdeck 53' trailers*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_STEP_53

async def add_step_53(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 9/14: Enter *number of Stepdeck 48' trailers* (current: {}):".format(
                context.user_data['new_driver'].get('step_48', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_STEP_48
    
    context.user_data['new_driver']['step_53'] = update.message.text
    await update.message.reply_text(
        "💼Step 11/14: Enter *bee equipment*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_BEE_EQUIPMENT

async def add_bee_equipment(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 10/14: Enter *number of Stepdeck 53' trailers* (current: {}):".format(
                context.user_data['new_driver'].get('step_53', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_STEP_53
    
    context.user_data['new_driver']['bee_equipment'] = update.message.text
    await update.message.reply_text(
        "💼Step 12/14: Enter *notes*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_NOTES

async def add_notes(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 11/14: Enter *bee equipment* (current: {}):".format(
                context.user_data['new_driver'].get('bee_equipment', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_BEE_EQUIPMENT
    
    context.user_data['new_driver']['notes'] = update.message.text
    await update.message.reply_text(
        "💼Step 13/14: Enter *company name*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
    )
    return ADD_COMPANY

async def add_company(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 12/14: Enter *notes* (current: {}):".format(
                context.user_data['new_driver'].get('notes', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_NOTES
    
    context.user_data['new_driver']['company'] = update.message.text
    await update.message.reply_text(
        "💼Final step: Enter *MC number* (or 'skip' if none):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["Back"]], resize_keyboard=True)
    )
    return ADD_TRAILER_MC

async def add_trailer_mc(update: Update, context: CallbackContext) -> int:
    if update.message.text == "🔙 Back":
        await driver_information(update, context)
        return ConversationHandler.END
    elif update.message.text == "👣 1 step back":
        await update.message.reply_text(
            "💼Step 13/14: Enter *company name* (current: {}):".format(
                context.user_data['new_driver'].get('company', 'not set')
            ),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([["👣 1 step back"], ["🔙 Back"]], resize_keyboard=True)
        )
        return ADD_COMPANY
    
    mc = update.message.text
    if mc.lower() != 'skip':
        context.user_data['new_driver']['mc'] = mc
    
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
            (driver_id, total_amount, flat_48, flat_53, step_48, step_53, bee_equipment, notes, company, MC)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                driver_id,
                context.user_data['new_driver'].get('total_amount'),
                context.user_data['new_driver'].get('flat_48'),
                context.user_data['new_driver'].get('flat_53'),
                context.user_data['new_driver'].get('step_48'),
                context.user_data['new_driver'].get('step_53'),
                context.user_data['new_driver'].get('bee_equipment'),
                context.user_data['new_driver'].get('notes'),
                context.user_data['new_driver'].get('company'),
                context.user_data['new_driver'].get('mc')
            )
        )
        
        connection.commit()
        await update.message.reply_text(
            "✅ Driver added successfully!",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        await driver_information(update, context)
        
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
    trailer_text = update.message.text.strip()

    # Соответствие текста кнопки и поля в базе
    trailer_mapping = {
        "🚛 Flatbed 48": "flat_48",
        "🚛 Flatbed 53": "flat_53",
        "🚚 Stepdeck 48": "step_48",
        "🚚 Stepdeck 53": "step_53"
    }

    trailer_field = trailer_mapping.get(trailer_text)
    if not trailer_field:
        await update.message.reply_text(
            "Invalid trailer format. Please select from the options.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return

    # Подключение и поиск по регулярному выражению: поле содержит хотя бы одну цифру
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    query = f"""
        SELECT di.driver_id, di.name 
        FROM driver_info di
        JOIN trailer_info ti ON di.driver_id = ti.driver_id
        WHERE ti.{trailer_field} REGEXP '[0-9]'
        ORDER BY di.name
    """
    cursor.execute(query)
    drivers = cursor.fetchall()
    connection.close()

    if not drivers:
        await update.message.reply_text(
            f"There are no drivers with trailer [{trailer_text}]\nPlease try again",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)
        )
        return

    # Сохраняем результаты для пагинации
    search_results[user_id] = {
        "drivers": drivers,
        "current_page": 0,
        "search_text": trailer_text
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
    context.user_data['current_driver_id'] = driver_id
    
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT di.*, ti.total_amount, ti.flat_48, ti.flat_53, ti.step_48, ti.step_53, 
               ti.bee_equipment, ti.notes, ti.company, ti.MC 
        FROM driver_info di
        LEFT JOIN trailer_info ti ON di.driver_id = ti.driver_id
        WHERE di.driver_id = %s
    """, (driver_id,))
    
    driver = cursor.fetchone()
    connection.close()
    
    if not driver:
        await update.callback_query.answer("Driver not found!")
        return
    
    message = (
        f"----------------------------------------\n"
        f"👨🏻‍💼 *Driver Information*\n"
        f"🆔 *ID:* {driver['driver_id']}\n"
        f"----------------------------------------\n\n"
        f"📟 *Name :* {driver['name']}\n"
        f"📞 *Phone :* {driver['phone_number'] or 'Not specified'}\n"
        f"📧 *Email :* {driver['email'] or 'Not specified'}\n\n"
        f"🗺️ *Location :* {driver['current_location'] or 'Not specified'}\n"
        f"📅 *Available :* {driver['current_day_of_week'] or 'Not specified'}\n\n"
        f"----------------------------------------\n"
        f"🚘 *Trailer information*\n"
        f"----------------------------------------\n\n"
        f"📊 *Total trailers :* {driver.get('total_amount') or 'Not specified'}\n\n"
        f"🚛 *Flat 48 :* {driver.get('flat_48') or '0'}\n"
        f"🚛 *Flat 53 :* {driver.get('flat_53') or '0'}\n"
        f"🚚 *Step 48 :* {driver.get('step_48') or '0'}\n"
        f"🚚 *Step 53 :* {driver.get('step_53') or '0'}\n\n"
        f"🐝 *Bee Equipment:* {driver.get('bee_equipment') or 'Not specified'}\n"
        f"📝 *Notes :* {driver.get('notes') or 'None'}\n\n"
        f"🏢 *Company :* {driver.get('company') or 'Not specified'}\n"
        f"🔢 *MC Number :* {driver.get('MC') or 'Not specified'}"
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
        [InlineKeyboardButton("📟 Name", callback_data="edit_name")],
        [InlineKeyboardButton("📞 Phone number", callback_data="edit_phone")],
        [InlineKeyboardButton("📧 Email", callback_data="edit_email")],
        [InlineKeyboardButton("🗺️ Current location", callback_data="edit_location")],
        [InlineKeyboardButton("📅 Current day of week", callback_data="edit_day")],
        [InlineKeyboardButton("🔢 Total trailers", callback_data="edit_total_amount")],
        [InlineKeyboardButton("🚛 Flatbed 48'", callback_data="edit_flat_48")],
        [InlineKeyboardButton("🚛 Flatbed 53'", callback_data="edit_flat_53")],
        [InlineKeyboardButton("🚚 Stepdeck 48'", callback_data="edit_step_48")],
        [InlineKeyboardButton("🚚 Stepdeck 53'", callback_data="edit_step_53")],
        [InlineKeyboardButton("🐝 Bee equipment", callback_data="edit_bee_equipment")],
        [InlineKeyboardButton("📝 Notes", callback_data="edit_notes")],
        [InlineKeyboardButton("🏢 Company", callback_data="edit_company")],
        [InlineKeyboardButton("🔢 MC Number", callback_data="edit_mc")],
        [InlineKeyboardButton("↩️ Come back", callback_data="edit_come_back")]
    ]
    
    await update.callback_query.edit_message_text(
        text="Select what You wanna edit",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_SELECT

async def edit_field(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data
    
    if field == "edit_come_back":
        driver_id = context.user_data['current_driver_id']
        await all_driver_information(update, context, driver_id)
        return ConversationHandler.END
    
    context.user_data['edit_field'] = field
    
    field_names = {
        "edit_name": "📟 Name",
        "edit_phone": "📞 Phone number",
        "edit_email": "📧 Email",
        "edit_location": "🗺️ Current location",
        "edit_day": "📅 Current day of week",
        "edit_total_amount": "🔢 Total trailers",
        "edit_flat_48": "🚛 Flatbed 48'",
        "edit_flat_53": "🚛 Flatbed 53'",
        "edit_step_48": "🚚 Stepdeck 48'",
        "edit_step_53": "🚚 Stepdeck 53'",
        "edit_bee_equipment": "🐝 Bee equipment",
        "edit_notes": "📝 Notes",
        "edit_company": "🏢 Company",
        "edit_mc": "🔢 MC Number"
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
        "edit_total_amount": ("trailer_info", "total_amount"),
        "edit_flat_48": ("trailer_info", "flat_48"),
        "edit_flat_53": ("trailer_info", "flat_53"),
        "edit_step_48": ("trailer_info", "step_48"),
        "edit_step_53": ("trailer_info", "step_53"),
        "edit_bee_equipment": ("trailer_info", "bee_equipment"),
        "edit_notes": ("trailer_info", "notes"),
        "edit_company": ("trailer_info", "company"),
        "edit_mc": ("trailer_info", "MC")
    }
    
    table, column = field_mapping[field]
    
    try:
        connection = get_db()
        cursor = connection.cursor()
        
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
                    (driver_id, total_amount, flat_48, flat_53, step_48, step_53, 
                     bee_equipment, notes, company, MC)
                    VALUES (%s, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                """, (driver_id,))
                connection.commit()
                cursor.execute(f"""
                    UPDATE trailer_info SET {column} = %s 
                    WHERE driver_id = %s
                """, (new_value, driver_id))
        
        connection.commit()
        await update.message.reply_text("✅ Information updated successfully!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if connection.is_connected():
            connection.close()
    
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
                ADD_TRAILER_TOTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_total)],
                ADD_FLAT_48: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_flat_48)],
                ADD_FLAT_53: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_flat_53)],
                ADD_STEP_48: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_step_48)],
                ADD_STEP_53: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_step_53)],
                ADD_BEE_EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bee_equipment)],
                ADD_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_notes)],
                ADD_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company)],
                ADD_TRAILER_MC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trailer_mc)],
            },
            fallbacks=[]
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