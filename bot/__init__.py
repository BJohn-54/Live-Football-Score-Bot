import logging
import logging.config
from pyrogram import Client
from bot.config import Config
from bot.utils import start_webserver


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
        self.owner = await self.get_users(int(Config.OWNER_ID))
        self.username = f"@{me.username}"

        logging.info("Bot started")
        logging.info(f"Owner: {self.owner.mention}")

        if Config.WEB_SERVER:
            await start_webserver()

    async def stop(self, *args):
        await super().stop()
