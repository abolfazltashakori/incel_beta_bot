import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler

from app_MG.APARAT import download_aparat_video
from app_MG.TIKTOK import download_tiktok_video
from app_MG.YOUTUBE import download_video
from download_history import show_download_history
from database_MG import *
from app_MG import APARAT
from app_MG import TIKTOK
CHOOSING, SEND_LINK_YOUTUBE, HISTORY_YOUTUBE, SEND_LINK_APARAT,SEND_LINK_TIKTOK = range(5)

def is_valid_url(url):
    regex = r'(https?://[^\s]+)'
    return re.match(regex, url) is not None

async def main_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    default_first_name = user.first_name if user.first_name else 'نام پیش‌فرض'
    default_last_name = 'نام خانوادگی پیش‌فرض'
    default_username = user.username if user.username else 'نام کاربری پیش‌فرض'
    default_balance = 10000
    default_auther = True
    default_number = '+98913222222'
    default_ban = False

    save_user_to_db(user.id, default_first_name, default_last_name, default_username, default_balance,
                    default_auther, default_number, default_ban)

    keyboard = [
        [KeyboardButton("اسپاتیفای"), KeyboardButton("ساند کلاود"), KeyboardButton("تیک تاک")],
        [KeyboardButton("یوتیوب"), KeyboardButton("آپارات")],
        [KeyboardButton("فروشگاه"), KeyboardButton("تنظیمات | مدیریت جساب")],
        [KeyboardButton("فایل به لینک")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text(f"سلام {user.first_name}", reply_markup=reply_markup)
    return CHOOSING

async def handle_menu(update: Update, context: CallbackContext):
    choice = update.message.text

    if choice == "اسپاتیفای":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
    elif choice == "تیک تاک":
        keyboard = [
            [KeyboardButton("ارسال لینک") , KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی تیک تاک را ارسال کنید.")
            return SEND_LINK_TIKTOK
    elif choice == "یوتیوب":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی یوتیوب را ارسال کنید.")
            return SEND_LINK_YOUTUBE

    elif choice == "آپارات":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("تاریخچه دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی آپارات را ارسال کنید.")
            return SEND_LINK_APARAT

    elif choice == "فروشگاه":
        keyboard = [
            [KeyboardButton("شارژ حساب"), KeyboardButton("خرید | تمدید VPN")],
            [KeyboardButton("اشتراک هوش مصنوعی")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

    elif choice == "تنظیمات | مدیریت خساب":
        keyboard = [
            [KeyboardButton("شارژ حساب"), KeyboardButton("اشتراک رایگان!")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

    elif choice == "سوابق دانلود":
        return HISTORY_YOUTUBE

    elif choice == "بازگشت":
        return CHOOSING

    elif choice == "ارسال لینک":
        return SEND_LINK_YOUTUBE

    else:
        await update.message.reply_text("گزینه معتبر انتخاب کنید")
        return CHOOSING

async def receive_video_link(update: Update, context: CallbackContext):
    video_link = update.message.text

    if not is_valid_url(video_link):
        await update.message.reply_text("لینک وارد شده معتبر نیست. لطفاً یک لینک ویدیوی صحیح ارسال کنید.")
        return

    await download_video(update, context, video_link)
    return ConversationHandler.END

async def show_download_history(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    history = get_download_history(user_id)

    if history:
        history_message = "سوابق دانلود شما:\n"
        for record in history:
            history_message += f"- {record['title']} (لینک: {record['link']})\n"
    else:
        history_message = "هیچ سوابق دانلودی یافت نشد."

    await update.message.reply_text(history_message)
    return ConversationHandler.END

def main():
    create_table()

    application = Application.builder().token('7631908261:AAFOFL57VBPsNTVP6msncTuy6O21Qzjgc5I').build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', main_menu)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            SEND_LINK_YOUTUBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_video_link)],
            HISTORY_YOUTUBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_download_history)],
            SEND_LINK_APARAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_aparat_video)],
            SEND_LINK_TIKTOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok_video)]
        },
        fallbacks=[],
    )

    application.add_handler(conversation_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
