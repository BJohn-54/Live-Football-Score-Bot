from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Script


@Client.on_message(filters.command("start") & filters.private & filters.incoming)
async def start(bot: Client, message: Message):
    await message.reply_text(
        Script.START_MESSAGE, disable_web_page_preview=True, quote=True
    )
