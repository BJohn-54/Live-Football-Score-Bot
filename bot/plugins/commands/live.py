import base64
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from bot.config import Config


@Client.on_message(filters.command(["live"]) & filters.incoming)
@Client.on_callback_query(filters.regex("^live"))
async def live(bot: Client, message: Message or CallbackQuery):
    user_id = message.from_user.id if message.from_user else 0
    offset = 0
    limit = 8
    if not isinstance(message, Message):
        if len(message.data.split("_")) == 2:
            _, r_user_id = message.data.split("_")
        elif len(message.data.split("_")) == 3:
            _, r_user_id, offset = message.data.split("_")
            offset = int(offset)
        if r_user_id != str(user_id):
            return await message.answer("You are not allowed to do this!")

    func = message.reply if isinstance(message, Message) else message.edit_message_text

    data = org_data = [x for x in Config.MATCHES if not x["href"]]

    if not data:
        return await func(
            "No live matches found!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Refresh", callback_data=f"live_{user_id}")]]
            ),
        )
    i = 0
    data = data[offset:]
    buttons = []
    for dat in data:
        text = dat["row_text"]
        kwargs = {"text": text}
        href = dat["href"]
        if not href:
            encoded_data = encode_base64(text[::-1])[:25]
            Config.DATA[encoded_data] = text
            kwargs["callback_data"] = f"view {encoded_data} {user_id}"
            buttons.append([InlineKeyboardButton(**kwargs)])
            i += 1
            if i == limit:
                break
            continue

    pagination = []
    # Add pagination buttons
    if len(org_data) > offset + limit:
        pagination.append(
            InlineKeyboardButton(
                "Next ▶️", callback_data=f"live_{user_id}_{offset + limit}"
            )
        )
    if offset >= limit:
        pagination.insert(
            0,
            InlineKeyboardButton(
                "◀️ Previous", callback_data=f"live_{user_id}_{offset - limit}"
            ),
        )
    # total_pages = int(len(org_data) / limit) + 1
    pagination.insert(
        1,
        InlineKeyboardButton(f"Page. {offset // limit + 1}", callback_data="ignore"),
    )
    if pagination:
        buttons.append(pagination)
    buttons.extend(([InlineKeyboardButton("🔙 Back", callback_data="start")],))
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
    return base64_bytes.decode("utf-8")
