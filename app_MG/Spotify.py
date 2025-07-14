from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
import os


# تابع برای دانلود از ساندکلاود
def download_from_soundcloud(url):
    ydl_opts = {
        'format': 'bestaudio/best',  # دانلود بهترین کیفیت صوتی
        'postprocessors': [{
            'key': 'FFmpegAudioPostProcessor',  # تبدیل به فرمت MP3
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # محل ذخیره فایل
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # دانلود آهنگ از لینک داده شده
        info_dict = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        return file_path


# دستور شروع ربات
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("سلام! لطفاً لینک آهنگ از ساندکلاود را ارسال کنید.")


# دستور دریافت لینک و دانلود آهنگ
async def download(update: Update, context: CallbackContext):
    url = update.message.text  # گرفتن لینک از پیام
    try:
        # دانلود آهنگ
        file_path = download_from_soundcloud(url)
        # ارسال فایل دانلود شده به تلگرام
        await update.message.reply_text("آهنگ دانلود شد! در حال آپلود...")
        await update.message.reply_audio(open(file_path, 'rb'))
        # حذف فایل بعد از ارسال
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود آهنگ: {str(e)}")


# تنظیمات ربات
async def main():
    # توکن ربات خود را وارد کنید
    TOKEN = '7235750472:AAEbaq6LHqpLrc4Ohur8fEFYgPLD_f8FHek'

    application = Application.builder().token(TOKEN).build()

    # افزودن دستورات به ربات
    application.add_handler(CommandHandler('start', start))
    application.add_handler(
        MessageHandler(filters.TEXT, download))  # تغییر از filters.Text & ~filters.Command به filters.TEXT

    # شروع ربات
    await application.run_polling()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
