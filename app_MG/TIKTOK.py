import yt_dlp
import os
from telegram import Update
from functools import partial
from database_MG import *


async def download_tiktok_video(update: Update, context):
    url = update.message.text
    chat_id = update.message.chat_id

    if not "https://www.tiktok.com/" in url:
        await update.message.reply_text("لینک وارد شده معتبر نیست. لطفاً یک لینک ویدیوی صحیح ارسال کنید.")
        return

    progress_with_context = partial(progress_hook, context=context)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
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

        video_title = ydl.prepare_filename(ydl.extract_info(url, download=False))
        save_download_to_db(update.effective_user.id, video_title, url)

        await update.message.reply_text("ویدیو با موفقیت دانلود شد!")

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {e}")
async def progress_hook(d, context):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        speed = d['speed']
        eta = d['eta']
        progress_message = f"در حال دانلود: {percent:.1f}%\n"
        progress_message += f"سرعت: {speed / 1024:.2f} KB/s\n"
        progress_message += f"زمان باقی‌مانده: {eta}s"

        chat_id = d.get('chat_id')
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=progress_message)

    elif d['status'] == 'finished':
        filename = d['filename']
        if os.path.exists(filename):
            os.remove(filename)
            print(f"فایل {filename} حذف شد.")