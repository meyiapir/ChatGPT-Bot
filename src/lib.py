import json
import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def read_json(path: str) -> dict:
    with open(path, "r") as file:
        return json.load(file)


def write_json(path: str, data: dict):
    with open(path, "w") as file:
        json.dump(data, file)
