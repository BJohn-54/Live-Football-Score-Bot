import aiohttp
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
    CallbackQuery,
)

from bot.config import Config
from utils import prettify_table_to_markdown


@Client.on_callback_query(filters.regex("^search"))
async def search_matches_cb(bot: Client, query: CallbackQuery):
    _, user_id = query.data.split("_")
    if user_id != str(query.from_user.id):
        return await query.answer("You are not allowed to do this!")
    await query.answer()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Back", callback_data="start")]]
    )
    await query.message.edit(
        "Send me a query to search for live matches.\nExample: /search Real Madrid",
        reply_markup=markup,
    )


@Client.on_message(filters.command("search") & filters.incoming)
async def search_matches(bot: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "No query found!\nUsage: /search <query>\nExample: /search Real Madrid"
        )

    q = message.text.split(None, 1)[1]
    out = await message.reply("Searching...")
    async with aiohttp.ClientSession() as session:
        async with session.get(Config.WEBSITE_URL) as resp:
            data = await resp.text()
            source = data
    data = await prettify_table_to_markdown(source)

    if not data:
        return await out.edit("No live matches found!")

    buttons = []

    for dat in data:
        text = dat["row_text"]
        if href := dat["href"]:
            kwargs = {"text": text}
            if q.lower() not in text.lower():
                continue

            if message.chat.type == enums.ChatType.PRIVATE:
                kwargs["web_app"] = WebAppInfo(url=href)
            else:
                kwargs["url"] = href
            buttons.append([InlineKeyboardButton(**kwargs)])

    if not buttons:
        return await out.edit("No query matches found!")

    text = f"**Search results for {q}**"
    await out.edit(
        text=text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
