import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler,ApplicationBuilder
from telegram.error import BadRequest
from app_MG.SETTING import *
from app_MG.ADMIN import *
from app_MG.APARAT import *
from app_MG.YOUTUBE import *
from app_MG.VPN_STORE import *
from app_MG.TIKTOK import *
from database_MG import *
from datetime import datetime
from app_MG.filetolink import *
import threading
import time
from database_MG import reset_filetolink_limits
WAITING_FOR_LINK = range(1)
CHANNELS = [
    {'name': 'IncelGP', 'username': '@incel_gr'},
    # اضافه کردن دیگر کانال‌ها
]

# تابع برای بررسی عضویت کاربر در کانال
async def is_user_member(update: Update, context: CallbackContext, channel_username: str):
    user = update.effective_user
    user_id = user.id
    try:
        member = await context.bot.get_chat_member(channel_username, user_id)
        # بررسی عضویت یا ادمین بودن
        if member.status in ['member', 'administrator']:
            return True
        else:
            return False
    except BadRequest:
        return False

async def check_membership_and_show_menu(update: Update, context: CallbackContext):
    user = update.effective_user  # استفاده از effective_user
    telegram_id = user.id
    first_name = user.first_name
    last_name = user.last_name or ""
    username = user.username or ""

    # برای تست می‌توانیم مقدارهای ثابت برای balance، auther، number و ban بدهیم
    balance = 0
    auther = False  # به دلخواه تغییر دهید
    number = "user_number"  # به دلخواه تغییر دهید
    ban = False  # به دلخواه تغییر دهید

    # ذخیره اطلاعات کاربر در پایگاه داده
    save_user_to_db(telegram_id, first_name, last_name, username, balance, auther, number, ban)

    for channel in CHANNELS:
        is_member = await is_user_member(update, context, channel['username'])

        if not is_member:
            keyboard = [
                [InlineKeyboardButton(f"عضویت در {channel['name']}", url=f"https://t.me/{channel['username'][1:]}")],
                [InlineKeyboardButton("بازگشت", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(f"برای استفاده از ربات، لطفاً به کانال {channel['name']} عضو شوید.",
                                                             reply_markup=reply_markup)
            else:
                await update.message.reply_text(f"برای استفاده از ربات، لطفاً به کانال {channel['name']} عضو شوید.",
                                                reply_markup=reply_markup)
            return  # جلوگیری از ادامه فرآیند

    # اگر کاربر عضو همه کانال‌ها بود، منو اصلی را نمایش می‌دهیم
    return await main_menu(update, context)

# منوی اصلی ربات
async def main_menu(update: Update, context: CallbackContext):
    user = update.effective_user  # استفاده از effective_user برای پشتیبانی از هم callback و هم message
    admin_id = 5381391685  # تغییر به عددی (بدون کوتیشن)

    if user.id == admin_id:  # مقایسه عددی
        keyboard = [

            # [InlineKeyboardButton("اسپاتیفای", callback_data='spotify'),
            # InlineKeyboardButton("ساند کلاود", callback_data='soundcloud'),
            [InlineKeyboardButton("تیک تاک", callback_data='tiktok'),InlineKeyboardButton("آپارات", callback_data='aparat')],
            # [InlineKeyboardButton("یوتیوب", callback_data='youtube'),
            #[InlineKeyboardButton("آپارات", callback_data='aparat')],
            # InlineKeyboardButton("اینستاگرام", callback_data='instagram')],
            [InlineKeyboardButton("فروشگاه", callback_data='shop'),
             InlineKeyboardButton("فایل به لینک", callback_data='file_to_link')],
            [InlineKeyboardButton("تنظیمات | مدیریت حساب", callback_data='settings')],
            [InlineKeyboardButton("بخش ادمین", callback_data='admin_menu')]
        ]
    else:
        keyboard = [
            # [InlineKeyboardButton("اسپاتیفای", callback_data='spotify'),
            # InlineKeyboardButton("ساند کلاود", callback_data='soundcloud'),
            [InlineKeyboardButton("تیک تاک", callback_data='tiktok'),InlineKeyboardButton("آپارات", callback_data='aparat')],

            # [InlineKeyboardButton("یوتیوب", callback_data='youtube'),
            #[InlineKeyboardButton("آپارات", callback_data='aparat')],
            # InlineKeyboardButton("اینستاگرام", callback_data='instagram')],

            [InlineKeyboardButton("فروشگاه", callback_data='shop'),
             InlineKeyboardButton("فایل به لینک", callback_data='file_to_link')],
            [InlineKeyboardButton("تنظیمات | مدیریت حساب", callback_data='settings')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    greeting = f"سلام {user.first_name}"

    if update.callback_query:
        await update.callback_query.edit_message_text(greeting, reply_markup=reply_markup)
    else:
        await update.message.reply_text(greeting, reply_markup=reply_markup)

# منوی فروشگاه
async def store_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("شارژ حساب", callback_data="charge_account"),
         InlineKeyboardButton("خرید | تمدید VPN", callback_data="buy_extend_vpn")],
        [InlineKeyboardButton("اشتراک هوش مصنوعی", callback_data="ai_subscription")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("انتخاب کنید", reply_markup=reply_markup)

# پردازش کلیک‌های دکمه‌ها
async def handle_menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "shop":
        await store_menu(update, context)
    elif data == "buy_extend_vpn":
        await vpn_menu(update, context)
    elif data == "back_to_main":
        await main_menu(update, context)
    elif data == "normal1":
        await normal1_menu(query)
    elif data == "normal2":
        await normal2_menu(query)
    elif data == "normal3":
        await normal3_menu(query)
    elif data == "normal4":
        await normal4_menu(query)
    elif data == "aparat":
        await aparat_menu(update, context)
    elif data == "aparat_link":
        await aparat_link(update, context)
    elif data == "tiktok":
        await tiktok_menu(update, context)
    elif data == "tiktok_link":
        await tiktok_link(update, context)
    elif data == "youtube":
        await youtube_menu(update, context)
    elif data == "youtube_link":
        await youtube_link(update, context)
    elif data == "file_to_link":
        await file_menu(update, context)
    elif data == "file_handler":
        await file_handler(update, context)
    elif data == "admin_menu":
        await admin_menu(update, context)
    #elif data == "spotify":
     #   await spotify_menu(update, context)
    #elif data == "spotify_link":
        #await spotify_link(update, context)
    elif data == "everyone_message":
        await everyone_message(update, context)
    elif data == "users_managment":
        await users_managment(update, context)
    elif data == "bot_analyze":
        await bot_analyze(update, context)
    if data == "bot_analyze":
        await bot_analyze(update, context)
    elif data == "refresh_stats":  # اضافه کردن این حالت جدید
        await bot_analyze(update, context)
    elif data == "wallet":
        await wallet_menu(update, context)
    elif data == "view_balance":
        await view_balance(update, context)
    elif data == "back_to_wallet":
        await wallet_menu(update, context)
    elif data == "settings":
        await wallet_menu(update, context)
def daily_reset_task():
    """وظیفه زمان‌بندی شده برای ریست روزانه"""
    while True:
        now = datetime.now()
        # اجرا در دقیقه 0 ساعت 0 (نیمه شب)
        if now.hour == 0 and now.minute == 0:
            reset_filetolink_limits()
            print(f"Daily reset completed at {now}")
        time.sleep(60)  # بررسی هر دقیقه
def daily_stats_task():
    """وظیفه زمان‌بندی شده برای ثبت آمار روزانه"""
    while True:
        now = datetime.now()
        # اجرا در دقیقه 0 ساعت 0 (نیمه شب)
        if now.hour == 0 and now.minute == 0:
            update_daily_stats()
            print(f"Daily stats updated at {now}")
        time.sleep(60)  # بررسی هر دقیقه

def after_successful_operation():
    increment_operations_count()

def main():
    create_table()
    reset_thread = threading.Thread(target=daily_reset_task, daemon=True)
    reset_thread.start()


    application = ApplicationBuilder().token('7235750472:AAEbaq6LHqpLrc4Ohur8fEFYgPLD_f8FHek').build()
    stats_thread = threading.Thread(target=daily_stats_task, daemon=True)
    stats_thread.start()
    trans_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(pending_transactions, pattern='^pending_transactions$')],
        states={
            TRANSACTION_SELECTION: [
                CallbackQueryHandler(select_transaction, pattern='^trans_\d+$')
            ],
            TRANSACTION_ACTION: [
                CallbackQueryHandler(view_receipt, pattern='^view_receipt$'),
                CallbackQueryHandler(approve_transaction, pattern='^approve_trans$'),
                CallbackQueryHandler(reject_transaction, pattern='^reject_trans$'),
                CallbackQueryHandler(back_to_transactions, pattern='^back_to_transactions$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(back_to_transactions, pattern='^back_to_transactions$')
        ],
        per_message=False
    )

    wallet_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(wallet_cart, pattern='^wallet_cart$')],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            RECEIPT: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_receipt)]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_transaction, pattern='^cancel_transaction$')
        ],
        per_message=False
    )

    application.add_handler(wallet_conv_handler)

    application.add_handler(trans_conv_handler)
    # هندلرهای اصلی
    application.add_handler(CommandHandler('start', check_membership_and_show_menu))
    application.add_handler(CallbackQueryHandler(handle_menu_callback))



    file_filter = filters.ALL & ~filters.COMMAND

    application.add_handler(MessageHandler(
        file_filter,
        receive_file
    ), group=1)

    application.add_handler(MessageHandler(
        file_filter & ~filters.COMMAND,
        receive_file
    ), group=1)

    # هندلر متن
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ), group=2)

    application.run_polling()
# تابع جدید برای مدیریت پیام‌های متنی
async def handle_text_message(update: Update, context: CallbackContext):
    text = update.message.text
    if 'aparat.com' in text:
        await download_aparat_video(update, context)
    elif 'tiktok.com' in text:
        await download_tiktok_video(update, context)
    elif 'youtube.com' in text or 'youtu.be' in text:
        await download_youtube_video(update, context)
 #   if 'spotify.com' in text:
  #      await download_spotify_track(update, context)
    else:
        await update.message.reply_text("لطفاً یک لینک معتبر ارسال کنید.")


if __name__ == '__main__':
    main()