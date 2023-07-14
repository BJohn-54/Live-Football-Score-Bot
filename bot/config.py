import os
from dotenv import load_dotenv

load_dotenv()


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


class Config(object):
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "tg_bot")
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    OWNER_ID = int(os.environ.get("OWNER_ID"))

    ADMINS = list(map(int, os.environ.get("ADMINS").split())) if os.environ.get("ADMINS") else []
    ADMINS.append(OWNER_ID) if OWNER_ID not in ADMINS else []
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
    WEB_SERVER = is_enabled(os.environ.get("WEB_SERVER", "False"), False)


class Script(object):
    START_MESSAGE = os.environ.get("START_MESSAGE", "Start message")
