from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    WebAppInfo,
)

from bot.config import Config, Messages
from utils import get_match_summary
from database import db


@Client.on_callback_query(filters.regex("^detail_view"))
async def detail_view_matches(bot: Client, query: CallbackQuery):
    _, match_id, edata, user_id = query.data.split()

    if user_id != str(query.from_user.id):
        return await query.answer("You are not allowed to do this!")

    data = next(
        (
            dat
            for dat in Config.MATCHES
            if dat["href"] and dat["href"].split("/")[-2] == match_id
        ),
        "",
    )

    if not data:
        return await query.answer("Something went wrong!", show_alert=True)

    url = data["href"]

    match_summary = await get_match_summary(url)
    match_data = await db.ticker.get_match(match_id)


    if not match_summary:
        return await query.answer("Something went wrong!", show_alert=True)

    text = Messages.DETAIL_VIEW.format(**match_summary)

    kwargs = {
        "text": "Watch Live",
    }

    if query.message.chat.type == enums.ChatType.PRIVATE:
        kwargs["web_app"] = WebAppInfo(url=url)
    else:
        kwargs["url"] = url
    buttons = [
        [InlineKeyboardButton(**kwargs)],
        [
            InlineKeyboardButton(
                text="Unnotify 🔕"
                if match_data and query.from_user.id in match_data["users"]
                else "Notify 🔔",
                callback_data=f"notify {match_id} {edata} {user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Refresh 🔄",
                callback_data=f"detail_view {match_id} {edata} {user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Back 🔙",
                callback_data=f"view {edata} {user_id}",
            )
        ],
    ]

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
