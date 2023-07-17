from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery

from bot.config import Config
from bot.plugins.callback.detailview import detail_view_matches
from utils import get_match_summary
from database import db


@Client.on_callback_query(filters.regex("^notify"))
async def notify_matches(bot: Client, query: CallbackQuery):
    _, match_id, edata, user_id = query.data.split()

    if user_id != str(query.from_user.id):
        return await query.answer("You are not allowed to do this!")

    for dat in Config.MATCHES:
        if dat["href"] and dat["href"].split("/")[-2] == match_id:
            data = dat

    match_data = await db.ticker.get_match(match_id)
    match_summary = await get_match_summary(data["href"])

    if not match_data:
        match_summary["users"] = [query.from_user.id]
        match_summary["url"] = data["href"]
        await db.ticker.add_match(match_summary)

    elif query.from_user.id not in match_data["users"]:
        await db.ticker.update_match(match_id, {"users": query.from_user.id}, "push")

    else:
        await db.ticker.update_match(match_id, {"users": query.from_user.id}, "pull")
        query.data = f"detail_view {match_id} {edata} {user_id}"
    await detail_view_matches(bot, query)
