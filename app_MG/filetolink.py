import ftplib
import os
import time
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, JobQueue
import asyncio

FTP_HOST = '185.235.196.18'
FTP_USER = 'incelspa'
FTP_PASS = 'p3tPE51mX+(hH0'
FTP_PORT = 21
FTP_DIR = 'public_html'


# تابع برای تولید نام فایل جدید
def generate_filename(telegram_id, original_name=None):
    """تولید نام فایل با فرمت: telegramid_randomextension.extension"""
    # تولید رشته تصادفی 8 کاراکتری
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    # استخراج پسوند فایل
    if original_name and '.' in original_name:
        ext = original_name.split('.')[-1].lower()
        # حذف پسوندهای طولانی (برای امنیت)
        ext = ext[:10]
    else:
        # پسوندهای پیش‌فرض بر اساس نوع محتوا
        ext = "bin"

    return f"{telegram_id}_{random_str}.{ext}"


# تابع حذف فایل از سرور FTP
def delete_ftp_file(file_name):
    try:
        with ftplib.FTP() as ftp:
            ftp.connect(FTP_HOST, FTP_PORT, timeout=60)
            ftp.login(FTP_USER, FTP_PASS)
            ftp.cwd(FTP_DIR)
            ftp.delete(file_name)
    except Exception as e:
        print(f"Error deleting expired file: {e}")


async def file_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📤 ارسال فایل", callback_data='file_handler')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "📁 لطفاً یک فایل را برای من ارسال کنید:",
        reply_markup=reply_markup
    )
    context.user_data['waiting_for_file'] = True


async def file_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    context.user_data['waiting_for_file'] = True
    keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data='cancel_upload')]]
    await query.edit_message_text(
        "✅ حالت دریافت فایل فعال شد!\n\n"
        "لطفاً فایل خود را ارسال کنید. (هر نوع فایلی پذیرفته می‌شود)\n"
        "⚠️ توجه: لینک دانلود به مدت 4 ساعت معتبر خواهد بود.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def receive_file(update: Update, context: CallbackContext):
    if not context.user_data.get('waiting_for_file'):
        return

    if not context.job_queue:
        await update.message.reply_text("⚠️ خطای سیستم! لطفاً دوباره امتحان کنید.")
        return

    # شناسایی انواع مختلف محتوا
    file = None
    original_name = None
    file_size = 0
    file_id = None

    # بررسی انواع مختلف محتوا
    if update.message.document:
        file = update.message.document
        original_name = file.file_name
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.video:
        file = update.message.video
        original_name = f"video_{file.file_id}.mp4"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.audio:
        file = update.message.audio
        original_name = file.file_name or f"audio_{file.file_id}.mp3"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.voice:
        file = update.message.voice
        original_name = f"voice_{file.file_id}.ogg"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.video_note:
        file = update.message.video_note
        original_name = f"video_note_{file.file_id}.mp4"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.photo:
        # گرفتن بزرگترین اندازه عکس
        file = update.message.photo[-1]
        original_name = f"photo_{file.file_id}.jpg"
        file_size = file.file_size
        file_id = file.file_id

    if file:
        # تولید نام جدید برای فایل
        user_id = update.message.from_user.id
        new_file_name = generate_filename(user_id, original_name)

        # ارسال پیام پیشرفت با طراحی زیباتر
        progress_message = await update.message.reply_text(
            "⏳ در حال پردازش فایل شما...\n"
            "▰▱▱▱▱▱▱▱▱ 0%\n"
            "⏱ زمان سپری شده: 0 ثانیه"
        )

        # متغیرهای پیگیری پیشرفت
        last_update_time = time.time()
        start_time = time.time()
        uploaded_bytes = 0

        async def update_progress(chunk):
            nonlocal uploaded_bytes, last_update_time
            uploaded_bytes += len(chunk)
            percent = (uploaded_bytes / file_size) * 100

            # ایجاد نوار پیشرفت
            progress_bar = "▰" * int(percent / 10) + "▱" * (10 - int(percent / 10))

            current_time = time.time()
            elapsed_time = current_time - start_time
            speed = uploaded_bytes / elapsed_time / 1024  # KB/s

            if current_time - last_update_time > 0.5:
                try:
                    await context.bot.edit_message_text(
                        chat_id=progress_message.chat_id,
                        message_id=progress_message.message_id,
                        text=(
                            f"🚀 در حال آپلود فایل...\n"
                            f"{progress_bar} {percent:.1f}%\n"
                            f"📦 حجم: {uploaded_bytes / 1024 / 1024:.1f}MB / {file_size / 1024 / 1024:.1f}MB\n"
                            f"⚡ سرعت: {speed:.1f} KB/s\n"
                            f"⏱ زمان سپری شده: {int(elapsed_time)} ثانیه"
                        )
                    )
                    last_update_time = current_time
                except Exception:
                    pass

        file_path = f"./{new_file_name}"

        try:
            # دانلود فایل از تلگرام
            downloaded_file = await context.bot.get_file(file.file_id)
            await downloaded_file.download_to_drive(file_path)

            # آپلود با گزارش پیشرفت
            try:
                download_link = await upload_to_ftp(file_path, new_file_name, update_progress)

                # محاسبه زمان انقضا
                expire_time = datetime.now() + timedelta(hours=4)
                expire_time_str = expire_time.strftime("%Y-%m-%d %H:%M:%S")

                # زمان‌بندی حذف فایل بعد از 4 ساعت
                context.job_queue.run_once(
                    lambda ctx: delete_ftp_file(new_file_name),
                    4 * 60 * 60  # 4 ساعت به ثانیه
                )

                # ایجاد دکمه برای لینک دانلود
                keyboard = [
                    [InlineKeyboardButton("📥 دانلود فایل", url=download_link)],
                    [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.edit_message_text(
                    chat_id=progress_message.chat_id,
                    message_id=progress_message.message_id,
                    text=(
                        "✅ فایل شما با موفقیت آپلود شد!\n\n"
                        f"🔗 لینک دانلود:\n{download_link}\n\n"
                        f"⏳ این لینک تا {expire_time_str} معتبر است\n"
                        "برای دانلود فایل روی دکمه زیر کلیک کنید:"
                    ),
                    reply_markup=reply_markup
                )
            except Exception as e:
                await context.bot.edit_message_text(
                    chat_id=progress_message.chat_id,
                    message_id=progress_message.message_id,
                    text=f"❌ خطا در آپلود به سرور: {str(e)}"
                )
                raise
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


async def upload_to_ftp(file_path, file_name, progress_callback=None, max_retries=3):
    CHUNK_SIZE = 7194304  # 7MB

    for attempt in range(max_retries):
        try:
            with ftplib.FTP() as ftp:
                # تنظیمات بهینه شده
                ftp.connect(FTP_HOST, FTP_PORT, timeout=60)
                ftp.login(FTP_USER, FTP_PASS)
                ftp.set_pasv(True)  # حالت فعال برای عملکرد بهتر
                ftp.voidcmd('TYPE I')  # حالت باینری
                ftp.set_debuglevel(0)  # غیرفعال کردن لاگ
                ftp.cwd(FTP_DIR)

                # ایجاد یک wrapper برای chunk
                class ChunkWrapper:
                    def __init__(self, chunk):
                        self.chunk = chunk
                        self.position = 0

                    def read(self, size=-1):
                        if self.position >= len(self.chunk):
                            return b''
                        start = self.position
                        if size < 0:
                            end = len(self.chunk)
                        else:
                            end = min(self.position + size, len(self.chunk))
                        self.position = end
                        return self.chunk[start:end]

                # آپلود فایل
                with open(file_path, 'rb') as f:
                    if progress_callback:
                        while True:
                            chunk = f.read(CHUNK_SIZE)
                            if not chunk:
                                break

                            wrapper = ChunkWrapper(chunk)
                            ftp.storbinary(f"STOR {file_name}", wrapper)
                            await progress_callback(chunk)
                    else:
                        ftp.storbinary(f'STOR {file_name}', f)

                return f"https://incel.space/{file_name}"

        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"خطای FTP بعد از {max_retries} تلاش: {str(e)}")
            await asyncio.sleep(2)