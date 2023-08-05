import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAX_TOKENS = 1024
RENDER_DELAY = 5
WHITE_LIST = os.getenv("WHITE_LIST")
REMIND_TIME = 5
SETTINGS_FILE = "settings.json"

about_latoken = ("Компания Latoken проводит онлайн хакатоны, для найма сотрудников. Обычно они проходят по субботам. "
                 "В них есть следующие этапы: 12:00 - 13:00 обсуждаем задачи в Zoom, 13:00 - 19:00 делаем задачи, "
                 "19:00 - 20:00 демо проекта и призы.")
