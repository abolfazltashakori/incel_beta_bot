from database_MG import *
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler

async def show_download_history(update, context):
    user_id = update.effective_user.id
    history = get_download_history(user_id)

    if history:
        history_message = "سوابق دانلود شما:\n"
        for record in history:
            history_message += f"- {record['title']} (لینک: {record['link']})\n"
    else:
        history_message = "هیچ سوابق دانلودی یافت نشد."

    await update.message.reply_text(history_message)
