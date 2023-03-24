import json
import logging
import os

import openai
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from dotenv import load_dotenv
from loguru import logger

from src.config import PATH_TO_STORY, SAVE_HISTORY, BOT_TOKEN, SYSTEM_MESSAGE, MAX_CONTEXT, MAX_TOKENS, RENDER_DELAY
from src.lib import read_json, write_json

load_dotenv()

# Создать Telegram бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

logger.info("Starting Bot...")


# Декоратор для доступа пользователя к боту
def access(func):
    async def wrapper(message: types.Message):
        json_data = read_json("settings.json")
        if json_data["work"] is False:
            return
        user_id = message.from_user.id
        username = message.from_user.username
        name = message.from_user.full_name

        ids = json_data["users"]
        admin_users = json_data["admin_users"]

        if user_id not in ids:
            for admin_user in admin_users:
                await bot.send_message(chat_id=admin_user,
                                       text=f"Пользователь {user_id}|{username}|{name} пытается получить доступ к боту.")
        else:
            await func(message)

    return wrapper


# Функция для обработки сообщения от пользователя
@dp.message_handler(commands=['ai'])
@access
async def handle_message(message: types.Message):
    # Получить идентификатор пользователя и текст сообщения
    user_id = message.from_user.id
    user_message = message.text[4:].strip()
    if user_message == "":
        await bot.send_message(user_id, "Напишите сообщение!")
        return

    logger.info(f"User {user_id} send message: {user_message}")

    if SAVE_HISTORY:
        # Получить историю сообщений пользователя
        user_history = []
        try:
            with open(f"{PATH_TO_STORY}{user_id}.json", "r") as f:
                user_history = json.load(f)
        except FileNotFoundError:
            pass
        count_assistant_history = len([message for message in user_history if message['role'] == 'assistant']) + 1
        if count_assistant_history > MAX_CONTEXT:
            await bot.send_message(user_id,
                                   "История переполнена, начните новую тему! Чтобы очистить историю напишите /clear")
            return

        # Добавить новое сообщение в историю пользователя
        user_history.append({"role": "user", "content": user_message})

        # Сохранить историю сообщений пользователя
        with open(f"{PATH_TO_STORY}{user_id}.json", "w") as f:
            json.dump(user_history, f)
    else:
        user_history = [{"role": "user", "content": user_message}]

    # Отправить сообщение на обработку в OpenAI API
    user_history.append({"role": "system", "content": SYSTEM_MESSAGE})

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
            if count % RENDER_DELAY == 0:
                await bot_mess.edit_text(out_text)
            count += 1
        except KeyError:
            continue

    if SAVE_HISTORY:
        # Добавить новое сообщение от бота в историю пользователя
        user_history.append({"role": "assistant", "content": out_text})

        # Сохранить обновленную историю сообщений пользователя
        with open(f"{PATH_TO_STORY}{user_id}.json", "w") as f:
            json.dump(user_history, f)

        await bot_mess.edit_text(out_text + f"\n{count_assistant_history}/8")


# Добавить обработчик команды /start
@dp.message_handler(commands=['start'])
@access
async def start_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, "Привет! Я бот-консультант Ai Odyssey.")


# Добавить обработчик команды /history
@dp.message_handler(commands=['history'])
async def history_command(message: types.Message):
    user_id = message.from_user.id

    # Получить историю сообщений пользователя
    try:
        with open(f"{PATH_TO_STORY}{user_id}.json", "r") as f:
            user_history = json.load(f)
        # удаление из истории сообщений сообщения от system
        user_history = [message for message in user_history if message['role'] != 'system']

        history_message = "".join([f"{message['role']}: {message['content']} \n\n" for message in user_history])
        await bot.send_message(user_id, history_message)

    except FileNotFoundError:
        await bot.send_message(user_id, "История сообщений не найдена.")
        return


@dp.message_handler(commands=['clear'])
@access
async def clear_command(message: types.Message):
    user_id = message.from_user.id

    # Удалить историю сообщений пользователя
    try:
        os.remove(f"{PATH_TO_STORY}{user_id}.json")
        await bot.send_message(user_id, "История сообщений удалена.")
    except FileNotFoundError:
        await bot.send_message(user_id, "История сообщений не найдена.")
        return
    except Exception as e:
        await bot.send_message(user_id, f"Ошибка: {e}")
        return


@dp.message_handler(commands=['add_user'])
@access
async def add_user_command(message: types.Message):
    json_data = read_json("settings.json")
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, "У вас нет прав для выполнения этой команды.")
        return

    text = message.text
    add_user_id = int(text.split(" ")[1])
    if add_user_id in json_data["users"]:
        await bot.send_message(user_id, "Пользователь уже добавлен.")
        return
    ids = json_data["users"]
    ids.append(add_user_id)
    work = json_data["work"]
    write_json("settings.json", {"users": ids, "admin_users": admin_ids, "work": work})
    await bot.send_message(user_id, "Пользователь добавлен.")


@dp.message_handler(commands=['off_bot'])
@access
async def off_bot_command(message: types.Message):
    json_data = read_json("settings.json")
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, "У вас нет прав для выполнения этой команды.")
        return

    json_data["work"] = False
    write_json("settings.json", json_data)

    await bot.send_message(user_id, "Бот отключен.")


@dp.message_handler(commands=['on_bot'])
async def on_bot_command(message: types.Message):
    json_data = read_json("settings.json")
    user_id = message.from_user.id
    admin_ids = json_data["admin_users"]
    if user_id not in admin_ids:
        await bot.send_message(user_id, "У вас нет прав для выполнения этой команды.")
        return

    json_data["work"] = True
    write_json("settings.json", json_data)

    await bot.send_message(user_id, "Бот включен.")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, "Список доступных команд:\n\n"
                                    "/start - начать диалог\n"
                                    "/history - просмотреть историю сообщений\n"
                                    "/clear - очистить историю сообщений\n"
                                    "/id - получить id пользователя\n"
                                    "/help - получить список команд")


@dp.message_handler(commands=['id'])
async def id_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, f"Ваш id: {user_id}")


WEBHOOK_URL = os.getenv('WEBHOOK_URL')


async def on_startup(dp):
    # Установить вебхук
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    # Удалить вебхук
    await bot.delete_webhook()


WEBHOOK_PATH = ""
WEBAPP_HOST = os.getenv('WEBAPP_HOST')
WEBAPP_PORT = os.getenv('WEBAPP_PORT')

if os.getenv('WEBHOOK_START') == "True":
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH,
                           on_startup=on_startup, on_shutdown=on_shutdown,
                           skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)

else:
    executor.start_polling(dp, skip_updates=True)
