import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, filters, Application
import yt_dlp

# تابعی برای چاپ لاگ‌های مربوط به دانلود
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100  # جلوگیری از خطای تقسیم بر صفر
        speed = d.get('speed', 0) / 1024  # تبدیل سرعت به کیلوبایت در ثانیه
        eta = d.get('eta', 0)
        print(f"در حال دانلود: {percent:.2f}% | سرعت دانلود: {speed:.2f} KB/s | ETA: {eta}s")
    elif d['status'] == 'finished':
        print(f"دانلود تمام شد: {d['filename']}")

# منوی تیک تاک
async def tiktok_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال لینک", callback_data="tiktok_link")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)

# درخواست لینک از کاربر
async def tiktok_link(update: Update, context: CallbackContext):
    # از کاربر خواسته می‌شود که لینک ویدیو را ارسال کند
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفاً لینک ویدیوی تیک تاک را ارسال کنید.")
    return "WAITING_FOR_LINK"  # وضعیت برای دریافت لینک

# دانلود ویدیو از تیک تاک
async def download_tiktok_video(update: Update, context: CallbackContext):
    url = update.message.text  # دریافت لینک ویدیو از پیام
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # دانلود بهترین کیفیت ویدیو و صدا
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # محل ذخیره فایل
            'quiet': True,  # جلوگیری از چاپ اطلاعات اضافی
            'progress_hooks': [progress_hook],  # استفاده از hook برای چاپ لاگ‌ها
        }

        # دانلود ویدیو از تیک تاک
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

            # ارسال فایل به تلگرام
            await update.message.reply_text("ویدیو دانلود شد! در حال ارسال...")
            await update.message.reply_video(open(file_path, 'rb'))

            # حذف فایل پس از ارسال
            os.remove(file_path)

            # پس از ارسال ویدیو، منو دوباره نمایش داده می‌شود
            keyboard = [
                [InlineKeyboardButton("ارسال لینک", callback_data="tiktok_link")],
                [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {str(e)}")

    return "WAITING_FOR_LINK"  # برگشت به وضعیت بعد از دانلود
