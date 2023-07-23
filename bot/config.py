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
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Optional
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "footballtickerbot")
    WEB_SERVER = is_enabled(os.environ.get("WEB_SERVER", "False"), False)
    WEBSITE_URL = "https://sportscore.io"
    PORT = int(os.environ.get("PORT", 5000))
    DATA = {}
    MATCHES = []


class Messages(object):
    DETAIL_VIEW = """
**{home_team} ({home_score} - {away_score}) {away_team}**

Time (minutes): {time_status} 🕒

**Details:**

🏆 {home_team}

- Corner Kick ⚽: {home_corner_kick}
- Red Card 🟥: {home_red_card}
- Yellow Card 🟨: {home_yellow_card}

🏆 {away_team}

- Corner Kick ⚽: {away_corner_kick}
- Red Card 🟥: {away_red_card}
- Yellow Card 🟨: {away_yellow_card}
"""
