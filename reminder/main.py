import asyncio
import json
import time
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

MESSAGE_TEXT = (
    "Привет! Ты не забыл про хакатон Latoken? Если ещё не успел "
    "зарегистрироваться, то сделай это как можно скорее: "
    "https://deliver.latoken.com/hackathon"
)

FILE_PATH = "../src/users_time.json"
SLEEP_TIME = 10

print("Reminder started")


async def send_reminders():
    while True:
        with open(FILE_PATH, "r") as file:
            data = json.load(file)

        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        users_to_remove = []

        for user_id, time_data in data.items():
            print(user_id)
            if now >= time_data:
                print(f"Sending message to {user_id}")
                await bot.send_message(user_id, MESSAGE_TEXT)
                users_to_remove.append(user_id)
            print(f"Sleeping for {SLEEP_TIME} seconds")

        # Удаление пользователей, которым было отправлено сообщение
        for user_id in users_to_remove:
            del data[user_id]

        with open(FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)  # Улучшенный формат сохранения данных

        await asyncio.sleep(SLEEP_TIME)  # Используйте asyncio.sleep для асинхронной паузы

if __name__ == '__main__':
    asyncio.run(send_reminders())
