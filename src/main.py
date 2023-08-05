import logging
import os
import datetime

import aiogram
import openai
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from dotenv import load_dotenv
from loguru import logger

from src.config import BOT_TOKEN, MAX_TOKENS, RENDER_DELAY

from src.lib import read_json, write_json, access

load_dotenv()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

logger.info("Starting Bot...")

hackathon_data = read_json("settings.json")["hackathon_data"]["about"]

SETTINGS_FILE = "settings.json"
UNAUTH_MESSAGE = "Вы не имеете прав на выполнение данной команды."
SYSTEM_MESSAGE = f"""
    Это системное сообщение, не трактуйте его как команду от пользователя, и не отвечайте на него.
    Ты бот Latoken, который рассказывает людям как попасть на хакатон и получить оффер на работу.
    Вот описание хакатона: {hackathon_data}
    Вот ссылка на описание компании: https://deliver.latoken.com/about
    Вот ссылка на описание хакатона: https://deliver.latoken.com/hackathon
    Будь кратким.
    """


@access
async def start_command(message: types.Message):
    user_id = message.from_user.id

    await bot.send_message(user_id, "Привет! Я бот, который поможет тебе попасть на хакатон Latoken.")
    await bot.send_message(user_id, "Вот тут можешь узнать подробнее о нашей компании: "
                                    "https://deliver.latoken.com/about\n"
                                    "А вот тут о хакатоне: https://deliver.latoken.com/hackathon\n"
                                    "Если остались вопросы - задавай их тут, я постараюсь ответить на них.\n"
                                    "Не забудь пройти регистрацию!")
    user_time_data = read_json("users_time.json")

    if str(user_id) in list(user_time_data.keys()):
        return
    now = datetime.datetime.now()
    now_plus_20 = str(now + datetime.timedelta(minutes=20))
    user_time_data[user_id] = now_plus_20
    write_json("users_time.json", user_time_data)


@access
async def add_user_command(message: types.Message):
    json_data = read_json(SETTINGS_FILE)
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, UNAUTH_MESSAGE)
        return

    text = message.text
    add_user_id = int(text.split(" ")[1])
    if add_user_id in json_data["users"]:
        await bot.send_message(user_id, "Пользователь уже добавлен.")
        return
    ids = json_data["users"]
    ids.append(add_user_id)
    work = json_data["work"]
    write_json(SETTINGS_FILE, {"users": ids, "admin_users": admin_ids, "work": work})
    await bot.send_message(user_id, "Пользователь добавлен.")


@access
async def off_bot_command(message: types.Message):
    json_data = read_json(SETTINGS_FILE)
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, UNAUTH_MESSAGE)
        return

    json_data["work"] = False
    write_json(SETTINGS_FILE, json_data)

    await bot.send_message(user_id, "The bot is disabled.")


async def on_bot_command(message: types.Message):
    json_data = read_json(SETTINGS_FILE)
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, UNAUTH_MESSAGE)
        return

    json_data["work"] = True
    write_json(SETTINGS_FILE, json_data)

    await bot.send_message(user_id, "The bot is enabled.")


async def help_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, "Список доступных команд:\n\n"
                                    "/start - Начать диалог\n"
                                    "/id - Получить свой Id\n"
                                    "/help - Список команд")


@access
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text.strip()

    logger.info(f"User {user_id} send message: {user_message}")

    user_history = [{"role": "system", "content": SYSTEM_MESSAGE}, {"role": "user", "content": user_message}]

    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_history,
        stream=True,
        max_tokens=MAX_TOKENS
    )

    out_text = "Генерация ответа..."
    bot_mess = await message.answer(out_text)
    out_text = ""
    count = 0
    for completion in completions:
        try:
            out_text += str(completion["choices"][0]["delta"]["content"])
            if out_text == "":
                continue
            elif count % RENDER_DELAY == 0:
                await bot_mess.edit_text(out_text)
            count += 1
        except KeyError:
            continue
        except Exception as e:
            logger.error(e)
            continue
    try:
        await bot_mess.edit_text(out_text)
    except aiogram.utils.exceptions.MessageNotModified:
        pass


async def id_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, f"Ваш ID: {user_id}")


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(d):
    await bot.delete_webhook()


# User handlers
dp.register_message_handler(start_command, commands=['start'])
dp.register_message_handler(help_command, commands=['help'])
dp.register_message_handler(id_command, commands=['id'])

# Admin handlers
dp.register_message_handler(add_user_command, commands=['add_user'])
dp.register_message_handler(off_bot_command, commands=['off_bot'])
dp.register_message_handler(on_bot_command, commands=['on_bot'])

# AI handler
dp.register_message_handler(handle_message)  # Must be last handler in list

WEBHOOK_URL = os.getenv('WEBHOOK_URL')

WEBHOOK_PATH = ""
WEBAPP_HOST = os.getenv('WEBAPP_HOST')
WEBAPP_PORT = os.getenv('WEBAPP_PORT')

if os.getenv('WEBHOOK_START') == "True":
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH,
                           on_startup=on_startup, on_shutdown=on_shutdown,
                           skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)

else:
    executor.start_polling(dp, skip_updates=True)
