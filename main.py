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

def is_valid_url(url):
    regex = r'(https?://[^\s]+)'
    return re.match(regex, url) is not None


async def is_user_member(update: Update, context: CallbackContext, channel_username: str):
    user = update.effective_user
    user_id = user.id

    try:
        member = await context.bot.get_chat_member(channel_username, user_id)
        if member.status == 'member' or member.status == 'administrator':
            return True
        else:
            return False
    except BadRequest:
        return False


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
            await update.message.reply_text(f"برای استفاده از ربات، لطفاً به کانال {channel['name']} عضو شوید.",
                                            reply_markup=reply_markup)
            return  # جلوگیری از ادامه فرآیند

    # اگر کاربر عضو همه کانال‌ها بود، منو اصلی را نمایش می‌دهیم
    return await main_menu(update, context)


async def main_menu(update: Update, context: CallbackContext):
    user = update.effective_user

    keyboard = [
        [KeyboardButton("اسپاتیفای"), KeyboardButton("ساند کلاود"), KeyboardButton("تیک تاک")],
        [KeyboardButton("یوتیوب"), KeyboardButton("آپارات"), KeyboardButton("اینستاگرام")],
        [KeyboardButton("فروشگاه"), KeyboardButton("تنظیمات | مدیریت جساب")],
        [KeyboardButton("فایل به لینک")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

    await update.message.reply_text(f"سلام {user.first_name}", reply_markup=reply_markup)
    return CHOOSING

async def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # حذف لودینگ دکمه

    if query.data == "buy_extend_vpn":
        await query.edit_message_text("شما وارد منوی VPN شدید.")
        await vpn_menu(update, context)  # فراخوانی تابع vpn_menu
    elif query.data == "charge_account":
        await query.edit_message_text("شما وارد منوی شارژ حساب شدید.")
        # عملیات مربوط به شارژ حساب را اینجا انجام دهید.
    elif query.data == "ai_subscription":
        await query.edit_message_text("شما وارد منوی اشتراک هوش مصنوعی شدید.")
        # عملیات مربوط به اشتراک هوش مصنوعی را اینجا انجام دهید.
    elif query.data == "back_to_main":
        # برگشت به منوی اصلی
        await main_menu(update, context)


async def handle_menu(update: Update, context: CallbackContext):
    choice = update.message.text

    # بخش اسپاتیفای
    if choice == "اسپاتیفای":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
    elif choice == "اینستاگرام":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی اینستاگرام را ارسال کنید.")
            return SEND_INSTA_LINK  # ارسال به وضعیت دریافت لینک
    # بخش تیک تاک
    elif choice == "تیک تاک":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی تیک تاک را ارسال کنید.")
            return SEND_LINK_TIKTOK  # ارسال به وضعیت دریافت لینک

    # بخش یوتیوب
    elif choice == "یوتیوب":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("سوابق دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی یوتیوب را ارسال کنید.")
            return SEND_LINK_YOUTUBE  # ارسال به وضعیت دریافت لینک

    # بخش آپارات
    elif choice == "آپارات":
        keyboard = [
            [KeyboardButton("ارسال لینک"), KeyboardButton("تاریخچه دانلود")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

        if choice == "ارسال لینک":
            await update.message.reply_text("لطفاً لینک ویدیوی آپارات را ارسال کنید.")
            return SEND_LINK_APARAT  # ارسال به وضعیت دریافت لینک

    # بخش فروشگاه


    elif choice == "فروشگاه":
        keyboard = [
            [InlineKeyboardButton("شارژ حساب", callback_data="charge_account"),
             InlineKeyboardButton("خرید | تمدید VPN", callback_data="buy_extend_vpn")],
            [InlineKeyboardButton("اشتراک هوش مصنوعی", callback_data="ai_subscription")],
            [InlineKeyboardButton("بازگشت", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)
    if update.callback_query :
        query = update.callback_query
        await query.answer()

        if query.data == "buy_extend_vpn":
            return SEND_VPN_MENU

    # بخش تنظیمات و مدیریت حساب
    elif choice == "تنظیمات | مدیریت جساب":
        keyboard = [
            [KeyboardButton("شارژ حساب"), KeyboardButton("اشتراک رایگان!")],
            [KeyboardButton("بازگشت")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("انتخاب کنید", reply_markup=reply_markup)

    # سوابق دانلود
    elif choice == "سوابق دانلود":
        return HISTORY_YOUTUBE

    # دکمه بازگشت
    elif choice == "بازگشت":
        return await check_membership_and_show_menu(update, context)  # بازگشت به منوی اصلی

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

    # ثبت CallbackQueryHandler فقط یک بار
    application.add_handler(CallbackQueryHandler(vpn_menu_handler))  # یا CallbackQueryHandler(vpn_menu_handler)

    # تعریف ConversationHandler برای مدیریت وضعیت‌های مختلف
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', check_membership_and_show_menu)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            SEND_LINK_YOUTUBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_video_link)],
            HISTORY_YOUTUBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_download_history)],
            SEND_LINK_APARAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_aparat_video)],
            SEND_LINK_TIKTOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok_video)],
            SEND_INSTA_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video)],
            SEND_VPN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, vpn_menu)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
    )

    # ثبت ConversationHandler
    application.add_handler(conversation_handler)

    # اجرای ربات
    application.run_polling()


if __name__ == '__main__':
    main()

