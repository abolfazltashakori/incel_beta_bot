import yt_dlp
import os
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, CallbackContext, MessageHandler, filters
from functools import partial
import re

CHOOSING, SEND_LINK_YOUTUBE, HISTORY_YOUTUBE, RETURN_HOME = range(4)

def progress_hook(d, context: CallbackContext):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        speed = d['speed']
        eta = d['eta']
        progress_message = f"در حال دانلود: {percent:.1f}%\n"
        progress_message += f"سرعت: {speed / 1024:.2f} KB/s\n"
        progress_message += f"زمان باقی‌مانده: {eta}s"

        chat_id = d.get('chat_id')
        if chat_id:
            context.bot.send_message(chat_id=chat_id, text=progress_message)

    elif d['status'] == 'finished':
        filename = d['filename']
        if os.path.exists(filename):
            os.remove(filename)
            print(f"فایل {filename} حذف شد.")

def is_valid_url(url):
    regex = r'(https?://[^\s]+)'
    return re.match(regex, url) is not None

async def download_video(update: Update, context: CallbackContext, video_link: str):
    chat_id = update.message.chat_id

    progress_with_context = partial(progress_hook, context=context)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_with_context],  # ارسال context به progress_hook
        'cookiefile': 'cookies.txt',  # برای احراز هویت
    }

    await update.message.reply_text("در حال دانلود ویدیو...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_link])

        await update.message.reply_text("ویدیو با موفقیت دانلود شد!")

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {e}")

async def handle_menu(update: Update, context: CallbackContext):
    choice = update.message.text

    if choice == "ارسال لینک":
        return SEND_LINK_YOUTUBE

    await update.message.reply_text("گزینه معتبر انتخاب کنید")
    return CHOOSING

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

def get_download_history(user_id):
    return [
        {"title": "ویدیو 1", "link": "https://youtu.be/xxxxxx"},
        {"title": "ویدیو 2", "link": "https://youtu.be/yyyyyy"},
    ]
