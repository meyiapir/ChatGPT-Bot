import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAX_TOKENS = 1024
RENDER_DELAY = 10
WHITE_LIST = os.getenv("WHITE_LIST")

