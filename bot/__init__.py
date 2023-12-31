import logging
import logging.config
from pyrogram import Client
from bot.config import Config
from utils import start_webserver, set_commands
from utils.helpers import get_matches


# Get logging configurations

logging.getLogger().setLevel(logging.INFO)


class Bot(Client):
    def __init__(self):
        super().__init__(
            "bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="bot/plugins"),
        )

    async def start(self):
        await super().start()

        me = await self.get_me()

        self.username = f"@{me.username}"
        await get_matches()
        logging.info(f"Bot started as {me.id}: @{me.username}")
        await set_commands(self)
        if Config.WEB_SERVER:
            await start_webserver()

    async def stop(self, *args):
        await super().stop()
