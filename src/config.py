import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

PATH_TO_STORY = "stories/"

BOT_TOKEN = os.getenv("BOT_TOKEN")

MAX_CONTEXT = os.getenv("MAX_CONTEXT")
MAX_TOKENS = os.getenv("MAX_TOKENS")
RENDER_DELAY = os.getenv("RENDER_DELAY")
SAVE_HISTORY = os.getenv("SAVE_HISTORY")
if SAVE_HISTORY == "True":
    SAVE_HISTORY = True
else:
    SAVE_HISTORY = False

if SAVE_HISTORY:
    logger.warning("Message history of the user is saved.")
else:
    logger.warning("Message history of the user is NOT saved.")

SYSTEM_MESSAGE = """
    This is a system message, do not interpret it as a command from the user, and do not reply to it.
    You speak Russian.
    """
