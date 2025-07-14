import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler
from app_MG.APARAT import download_aparat_video
from app_MG.INSTAGRAM import download_instagram_video
from app_MG.TIKTOK import download_tiktok_video
from app_MG.VPN_STORE import *
from app_MG.YOUTUBE import download_video
from download_history import show_download_history
from database_MG import *
from app_MG import APARAT
from app_MG import TIKTOK
from app_MG import *
CHOOSING,SEND_VPN_MENU ,SEND_LINK_YOUTUBE, HISTORY_YOUTUBE, SEND_LINK_APARAT, SEND_LINK_TIKTOK,SEND_INSTA_LINK = range(7)

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

# تابع برای نمایش منوی اصلی VPN یا نمایش پیام عضویت
async def check_membership_and_show_menu(update: Update, context: CallbackContext):
    user = update.effective_user

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
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("اسپاتیفای", callback_data='spotify'),
         InlineKeyboardButton("ساند کلاود", callback_data='soundcloud'),
         InlineKeyboardButton("تیک تاک", callback_data='tiktok')],
        [InlineKeyboardButton("یوتیوب", callback_data='youtube'),
         InlineKeyboardButton("آپارات", callback_data='aparat'),
         InlineKeyboardButton("اینستاگرام", callback_data='instagram')],
        [InlineKeyboardButton("فروشگاه", callback_data='shop'),
         InlineKeyboardButton("فایل به لینک", callback_data='file_to_link')],
        [InlineKeyboardButton("تنظیمات | مدیریت جساب", callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(f"سلام {user.first_name}", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"سلام {user.first_name}", reply_markup=reply_markup)

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


def main():
    application = Application.builder().token('7235750472:AAEbaq6LHqpLrc4Ohur8fEFYgPLD_f8FHek').build()

    # ثبت CommandHandler و CallbackQueryHandler
    application.add_handler(CommandHandler('start', check_membership_and_show_menu))
    application.add_handler(CallbackQueryHandler(handle_menu_callback))  # ثبت CallbackQueryHandler برای پردازش کلیک‌ها

    application.run_polling()

if __name__ == '__main__':
    main()