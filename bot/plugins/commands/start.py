import base64
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import Config
from utils import prettify_table_to_markdown


@Client.on_message(filters.command(["start", "live"]) & filters.incoming)
@Client.on_callback_query(filters.regex("^live"))
async def start(bot: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0

    if not isinstance(message, Message):
        _, r_user_id = message.data.split("_")
        
        if r_user_id != str(user_id):
            return await message.answer("You are not allowed to do this!")

    func = message.reply if isinstance(message, Message) else message.edit_message_text
    async with aiohttp.ClientSession() as session:
        async with session.get(Config.WEBSITE_URL) as resp:
            data = await resp.text()
            source = data

    data = await prettify_table_to_markdown(source)

    if not data:
        return await func(
            "No live matches found!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Refresh", callback_data=f"live_{user_id}")]]
            ),
        )

    buttons = []
    for dat in data:
        text = dat["row_text"]
        kwargs = {"text": text}
        href = dat["href"]
        if not href:
            encoded_data = encode_base64(text)[:10]
            Config.DATA[encoded_data] = text
            kwargs["callback_data"] = f"view {encoded_data} {user_id}"
            buttons.append([InlineKeyboardButton(**kwargs)])

    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"live_{user_id}")])

    text = f"{bot.me.mention} statistics will provide an opportunity for people who are interested in sports to actively monitor a wide range of sports 🏀 ⚽ tournaments - including the results and statistics of each competition"

    await func(
        text=text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    if not isinstance(message, Message):
        await message.answer("🔄 Refreshed successfully!")


def encode_base64(string):
    string_bytes = string.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string
