import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, filters, Application
import yt_dlp

# تابعی برای چاپ لاگ‌های مربوط به دانلود و ارسال پیشرفت به تلگرام
def progress_hook(d, context: CallbackContext):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        speed = d['speed'] / 1024  # تبدیل سرعت به کیلوبایت در ثانیه
        eta = d['eta']

        # دریافت chat_id از context
        chat_id = context.chat_data.get('chat_id')
        if chat_id:
            progress_message = f"در حال دانلود: {percent:.2f}% | سرعت دانلود: {speed:.2f} KB/s | زمان باقی‌مانده: {eta}s"
            # ویرایش پیام پیشرفت با استفاده از message_id
            message_id = context.chat_data.get('message_id')
            if message_id:
                context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress_message)

    elif d['status'] == 'finished':
        print(f"دانلود تمام شد: {d['filename']}")

# منوی آپارات
async def aparat_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال لینک", callback_data="aparat_link")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)

# درخواست لینک از کاربر
async def aparat_link(update: Update, context: CallbackContext):
    # از کاربر خواسته می‌شود که لینک ویدیو را ارسال کند
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفاً لینک ویدیوی آپارات را ارسال کنید.")
    return "WAITING_FOR_LINK"  # وضعیت برای دریافت لینک

# دانلود ویدیو از آپارات
async def download_aparat_video(update: Update, context: CallbackContext):
    url = update.message.text  # دریافت لینک ویدیو از پیام
    try:
        # ذخیره chat_id و message_id در context برای استفاده در progress_hook
        chat_id = update.message.chat_id
        context.chat_data['chat_id'] = chat_id  # ذخیره chat_id برای استفاده در progress_hook

        # ارسال پیام ابتدایی برای نشان دادن پیشرفت
        progress_message = "در حال دانلود..."
        progress_message_sent = await update.message.reply_text(progress_message)
        context.chat_data['message_id'] = progress_message_sent.message_id  # ذخیره message_id برای ویرایش پیام

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # دانلود بهترین کیفیت ویدیو و صدا
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # محل ذخیره فایل
            'quiet': False,  # جلوگیری از چاپ اطلاعات اضافی
            'progress_hooks': [lambda d: progress_hook(d, context)],  # ارسال context به progress_hook
        }

        # دانلود ویدیو از آپارات
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

            # ارسال ویدیو به تلگرام
            await update.message.reply_text("ویدیو دانلود شد! در حال ارسال...")
            await update.message.reply_video(open(file_path, 'rb'))

            # حذف فایل پس از ارسال
            os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود ویدیو: {str(e)}")

    return "WAITING_FOR_LINK"  # برگشت به وضعیت بعد از دانلود
