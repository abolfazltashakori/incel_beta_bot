import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import os




# تابع برای دانلود ویدیو از اینستاگرام
async def download_instagram_video(update: Update, context: CallbackContext):
    url = update.message.text
    if not "https://www.instagram.com/" in url:
        await update.message.reply_text("لینک وارد شده معتبر نیست. لطفاً یک لینک ویدیوی صحیح از اینستاگرام ارسال کنید.")
        return

    # گزینه‌های دانلود yt-dlp
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',  # نام فایل با عنوان ویدیو
        'noplaylist': True,  # جلوگیری از دانلود پلی‌لیست‌ها
    }

    # دانلود و ارسال ویدیو
    try:
        await update.message.reply_text("در حال دانلود ویدیو از اینستاگرام...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # ارسال فایل به کاربر
        await update.message.reply_video(video=open(filename, 'rb'))

        # حذف فایل پس از ارسال
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {e}")