import yt_dlp
import os
import random
import string
from telegram import Update
from functools import partial
from database_MG import *


# تابع برای ایجاد نام رندوم برای فایل
def generate_random_filename(extension="mp4", length=10):
    """تولید نام رندوم برای فایل‌ها"""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return f"{random_string}.{extension}"


# تابع نمایش درصد پیشرفت دانلود
async def progress_hook(d, context):
    if d['status'] == 'downloading':
        downloaded_bytes = d.get('downloaded_bytes', 0)
        total_bytes = d.get('total_bytes', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)

        if total_bytes and downloaded_bytes is not None:
            percent = (downloaded_bytes / total_bytes) * 100
            progress_message = f"در حال دانلود: {percent:.1f}%\n"
            if speed is not None:
                progress_message += f"سرعت: {speed / 1024:.2f} KB/s\n"
            if eta is not None:
                progress_message += f"زمان باقی‌مانده: {eta}s"

            chat_id = d.get('chat_id')
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=progress_message)

    elif d['status'] == 'finished':
        filename = d['filename']
        print(f"فایل {filename} دانلود شد و آماده ارسال است.")


async def download_tiktok_video(update: Update, context):
    url = update.message.text
    chat_id = update.message.chat_id

    if not "https://www.tiktok.com/" in url:
        await update.message.reply_text("لینک وارد شده معتبر نیست. لطفاً یک لینک ویدیوی صحیح ارسال کنید.")
        return

    progress_with_context = partial(progress_hook, context=context)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',  # فقط برای ذخیره نام اصلی به صورت موقت
        'progress_hooks': [progress_with_context],
        'cookiefile': 'tiktok_cooki.txt',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferredformat': 'mp4',
        }],
    }

    await update.message.reply_text("در حال دانلود ویدیو...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # نام رندوم برای فایل
        random_filename = generate_random_filename(extension="mp4")
        downloaded_filename = ydl.prepare_filename(ydl.extract_info(url, download=False))

        # تغییر نام فایل
        os.rename(downloaded_filename, random_filename)

        save_download_to_db(update.effective_user.id, random_filename, url)

        await update.message.reply_text("ویدیو با موفقیت دانلود شد!")

        # ارسال فایل به کاربر
        file_path = os.path.join(os.getcwd(), random_filename)
        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, 'rb'))  # ارسال ویدیو به کاربر


            print(f"فایل {file_path} پس از ارسال حذف شد.")

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {e}")
