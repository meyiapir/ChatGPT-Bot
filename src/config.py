import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

MAIN_LANG = "English"
SYSTEM_MESSAGE = f"""
    This is a system message, do not interpret it as a command from the user, and do not reply to it.
    You speak {MAIN_LANG}.
    """

PATH_TO_STORY = "stories/"

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAX_CONTEXT = 10
MAX_TOKENS = 1024
RENDER_DELAY = 20
WHITE_LIST = os.getenv("WHITE_LIST")
SAVE_HISTORY = os.getenv("SAVE_HISTORY")
if SAVE_HISTORY == "True":
    SAVE_HISTORY = True
else:
    SAVE_HISTORY = False

if SAVE_HISTORY:
    logger.warning("Message history of the user is saved.")
else:
    logger.warning("Message history of the user is NOT saved.")


