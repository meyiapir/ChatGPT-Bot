import json
import os

import openai
from aiogram import types
from dotenv import load_dotenv
from src.config import WHITE_LIST

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def read_json(path: str) -> dict:
    with open(path, "r") as file:
        return json.load(file)


def write_json(path: str, data: dict):
    with open(path, "w") as file:
        json.dump(data, file)


def access(func):
    async def wrapper(message: types.Message):
        if WHITE_LIST == "False":
            await func(message)
            return

        json_data = read_json("settings.json")
        if json_data["work"] is False:
            return
        user_id = message.from_user.id

        allow_ids = json_data["users"]

        if user_id in allow_ids:
            await func(message)

    return wrapper
