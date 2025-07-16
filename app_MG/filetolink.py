import ftplib
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import asyncio
FTP_HOST = '185.235.196.18'
FTP_USER = 'incelspa'
FTP_PASS = 'p3tPE51mX+(hH0'
FTP_PORT = 21
FTP_DIR = 'public_html'


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

    # شناسایی انواع مختلف محتوا
    content_types = [
        update.message.document,
        update.message.video,
        update.message.audio,
        update.message.voice,
        update.message.video_note,
        update.message.photo
    ]

    file = None
    file_name = None
    file_size = 0
    file_id = None

    # بررسی انواع مختلف محتوا
    if update.message.document:
        file = update.message.document
        file_name = file.file_name
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.video:
        file = update.message.video
        file_name = f"video_{file.file_id}.mp4"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.audio:
        file = update.message.audio
        file_name = file.file_name or f"audio_{file.file_id}.mp3"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.voice:
        file = update.message.voice
        file_name = f"voice_{file.file_id}.ogg"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.video_note:
        file = update.message.video_note
        file_name = f"video_note_{file.file_id}.mp4"
        file_size = file.file_size
        file_id = file.file_id
    elif update.message.photo:
        # گرفتن بزرگترین اندازه عکس
        file = update.message.photo[-1]
        file_name = f"photo_{file.file_id}.jpg"
        file_size = file.file_size
        file_id = file.file_id



    if file:
        # ... بررسی حجم و محدودیت کاربر ...

        # ارسال پیام پیشرفت
        progress_message = await update.message.reply_text(
            "📤 در حال آپلود فایل به سرور...\n"
            "⏳ پیشرفت: 0%\n"
            "🚀 سرعت: 0 KB/s\n"
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

            current_time = time.time()
            elapsed_time = current_time - start_time
            speed = uploaded_bytes / elapsed_time / 1024  # KB/s

            if current_time - last_update_time > 0.5:
                try:
                    await context.bot.edit_message_text(
                        chat_id=progress_message.chat_id,
                        message_id=progress_message.message_id,
                        text=(
                            f"📤 در حال آپلود فایل به سرور...\n"
                            f"⏳ پیشرفت: {percent:.1f}%\n"
                            f"🚀 سرعت: {speed:.1f} KB/s\n"
                            f"⏱ زمان سپری شده: {int(elapsed_time)} ثانیه"
                        )
                    )
                    last_update_time = current_time
                except Exception:
                    pass

        file_path = f"./{file_name}"

        try:
            # دانلود فایل از تلگرام
            downloaded_file = await context.bot.get_file(file.file_id)
            await downloaded_file.download_to_drive(file_path)

            # آپلود با گزارش پیشرفت
            try:
                download_link = await upload_to_ftp(file_path, file_name, update_progress)

                await context.bot.edit_message_text(
                    chat_id=progress_message.chat_id,
                    message_id=progress_message.message_id,
                    text=f"✅ فایل با موفقیت آپلود شد!\nلینک دانلود: {download_link}"
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
    for attempt in range(max_retries):
        try:
            with ftplib.FTP() as ftp:
                # تنظیمات اتصال
                ftp.connect(FTP_HOST, FTP_PORT, timeout=60)
                ftp.login(FTP_USER, FTP_PASS)
                ftp.set_pasv(True)
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
                            chunk = f.read(10240)  # 10KB per chunk
                            if not chunk:
                                break

                            # استفاده از wrapper برای chunk
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