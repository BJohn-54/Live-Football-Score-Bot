from contextlib import suppress
import datetime


import aiohttp
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from bot.config import Config
from utils import prettify_table_to_markdown


@Client.on_message(filters.command(["start", "live"]) & filters.incoming)
@Client.on_callback_query(filters.regex("live"))
async def start(bot: Client, message: Message):
    func = message.reply if isinstance(message, Message) else message.edit_message_text
    chat_type = (
        message.chat.type if isinstance(message, Message) else message.message.chat.type
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(Config.WEBSITE_URL) as resp:
            data = await resp.text()
            source = data

    data = await prettify_table_to_markdown(source)

    if not data:
        return await func("No live matches found!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Refresh", callback_data="live")]]))
    
    buttons = []
    for dat in data:
        text = dat["row_text"]
        kwargs = {"text": text}

        if href := dat["href"]:
            if chat_type == enums.ChatType.PRIVATE:
                kwargs["web_app"] = WebAppInfo(url=href)
            else:
                kwargs["url"] = href
        else:
            kwargs["callback_data"] = "ident"

        buttons.append([InlineKeyboardButton(**kwargs)])


    buttons.append([InlineKeyboardButton("Refresh", callback_data="live")])

    text = f"**Last updated at {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} UTC**"

    with suppress(Exception):
        await func(
            text=text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    if not isinstance(message, Message):
        await message.answer("Refreshed successfully!")
