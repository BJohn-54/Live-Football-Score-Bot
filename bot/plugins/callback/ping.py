from pyrogram import Client, filters
from pyrogram.types import CallbackQuery


@Client.on_callback_query(filters.regex("^ping_"))
async def ping(bot: Client, query: CallbackQuery):
    _, user_id = query.data.split("_")
    if user_id != str(query.from_user.id):
        return await query.answer("You are not allowed to do this!")
    await query.answer("I am alive!", show_alert=True)
