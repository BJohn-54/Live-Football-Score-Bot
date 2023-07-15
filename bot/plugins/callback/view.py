import aiohttp
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    WebAppInfo,
)

from bot.config import Config
from utils import prettify_table_to_markdown
from utils.helpers import get_source


@Client.on_callback_query(filters.regex("^view"))
async def view_matches(bot: Client, query: CallbackQuery):
    _, encoded_data, user_id = query.data.split()

    if user_id != str(query.from_user.id):
        return await query.answer("You are not allowed to do this!")

    reply_text = Config.DATA.get(encoded_data)

    if not reply_text:
        return await query.answer("Something went wrong!", show_alert=True)

    source = await get_source(Config.WEBSITE_URL)
    data = await prettify_table_to_markdown(source)

    if not data:
        return await query.answer("No live matches found!", show_alert=True)

    buttons = []

    is_href = False

    for dat in data:
        text = dat["row_text"]
        href = dat["href"]

        if not href:
            if is_href:
                break

            if text == reply_text:
                is_href = True

        if is_href and href:
            kwargs = {"text": text}
            if query.message.chat.type == enums.ChatType.PRIVATE:
                kwargs["web_app"] = WebAppInfo(url=href)
            else:
                kwargs["url"] = href
            buttons.append([InlineKeyboardButton(**kwargs)])

    buttons.extend(
        (
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data=f"view {encoded_data} {query.from_user.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back", callback_data=f"live_{query.from_user.id}"
                )
            ],
        )
    )

    await query.message.edit_text(
        text=reply_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
