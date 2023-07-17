from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)


@Client.on_message(filters.command(["start"]) & filters.incoming)
@Client.on_callback_query(filters.regex("^start"))
async def start(bot: Client, message: Message or CallbackQuery):
    user_id = message.from_user.id if message.from_user else 0
    func = message.reply if isinstance(message, Message) else message.edit_message_text
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Football Live Matches", callback_data=f"live_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton("Search", callback_data=f"search_{user_id}"),
            ],
            [
                InlineKeyboardButton(
                    "Join SportScore Chatroom", url="https://t.me/+a_3DI3_yNmJlZjQx"
                ),
            ],
            [
                InlineKeyboardButton("SportScore.io", url="https://SportScore.io"),
            ],
            [
                InlineKeyboardButton(
                    "Check if bot is up", callback_data=f"ping_{user_id}"
                ),
            ],
        ]
    )
    await func(
        f"Hello {message.from_user.mention(style='md')},\n\nI am {bot.me.mention} statistics bot. I can provide an opportunity for people who are interested in sports to actively monitor a wide range of sports 🏀 ⚽ tournaments - including the results and statistics of each competition",
        reply_markup=markup,
    )
