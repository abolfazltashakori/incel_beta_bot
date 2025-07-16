import ftplib
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# تنظیمات FTP
FTP_HOST = '185.235.196.18'  # آدرس سرور FTP
FTP_USER = 'incelspa'  # نام کاربری FTP
FTP_PASS = 'p3tPE51mX+(hH0'  # رمز عبور FTP
FTP_DIR = 'public_html'  # پوشه مقصد در سرور


async def file_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال فایل", callback_data='file_handler')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("لطفاً یک فایل ارسال کنید.", reply_markup=reply_markup)
    context.user_data['waiting_for_file'] = True


async def file_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    context.user_data['waiting_for_file'] = True
    keyboard = [[InlineKeyboardButton("انصراف", callback_data='cancel_upload')]]
    await query.edit_message_text(
        "✅ حالت دریافت فایل فعال شد!\nلطفاً فایل خود را ارسال کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def receive_file(update: Update, context: CallbackContext):
    if not context.user_data.get('waiting_for_file'):
        await update.message.reply_text("لطفاً ابتدا دکمه 'ارسال فایل' را انتخاب کنید.")
        return

    # شناسایی انواع مختلف فایل‌ها
    file = None
    file_name = None

    if update.message.document:
        file = update.message.document
        file_name = file.file_name
    elif update.message.video:
        file = update.message.video
        file_name = file.file_name if file.file_name else f"video_{file.file_id}.mp4"
    elif update.message.audio:
        file = update.message.audio
        file_name = file.file_name if file.file_name else f"audio_{file.file_id}.mp3"
    elif update.message.photo:
        # برای عکس‌ها، بزرگترین سایز را انتخاب می‌کنیم
        file = update.message.photo[-1]
        file_name = f"photo_{file.file_id}.jpg"
    elif update.message.voice:
        file = update.message.voice
        file_name = f"voice_{file.file_id}.ogg"
    elif update.message.video_note:
        file = update.message.video_note
        file_name = f"video_note_{file.file_id}.mp4"

    if file:
        file_path = f"./{file_name}"

        try:
            # دانلود فایل از تلگرام
            downloaded_file = await context.bot.get_file(file.file_id)
            await downloaded_file.download_to_drive(file_path)

            # آپلود به سرور FTP
            download_link = await upload_to_ftp(file_path, file_name)
            await update.message.reply_text(f"✅ فایل آپلود شد!\nلینک دانلود: {download_link}")

        except Exception as e:
            await update.message.reply_text(f"❌ خطا در آپلود: {str(e)}")
            print(f"Upload error: {str(e)}")  # خطایابی
        finally:
            # پاکسازی فایل موقت و بازنشانی حالت
            if os.path.exists(file_path):
                os.remove(file_path)
            context.user_data['waiting_for_file'] = False
    else:
        await update.message.reply_text("""
لطفاً یک فایل معتبر ارسال کنید. انواع فایل‌های قابل قبول:
- فایل مستند (Document)
- ویدیو
- عکس
- صدا
- ویدیو یادداشت
""")

async def upload_to_ftp(file_path, file_name):
    try:
        # اتصال به سرور FTP
        with ftplib.FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)

            # تغییر به پوشه مقصد
            ftp.cwd(FTP_DIR)

            # آپلود فایل
            with open(file_path, 'rb') as f:
                ftp.storbinary(f'STOR {file_name}', f)

            # ساخت لینک دانلود (فرض بر این است که دامنه شما example.com است)
            return f"http://incel.space/{file_name}"

    except ftplib.all_errors as e:
        raise Exception(f"خطا در اتصال FTP: {str(e)}")