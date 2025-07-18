import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, filters, Application
import yt_dlp
from yt_dlp.utils import DownloadError


# تابعی برای نمایش پیشرفت دانلود به کاربر
async def progress_hook(d, context: CallbackContext, chat_id, message_id, total_bytes=None):
    try:
        if d['status'] == 'downloading':
            # دریافت اطلاعات پیشرفت
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = total_bytes or d.get('total_bytes', 1)
            percent = min(100, downloaded_bytes / total_bytes * 100)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            # تبدیل به واحدهای خوانا
            downloaded_mb = downloaded_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed else 0

            # ایجاد پیام وضعیت
            progress_bar = "⬜" * 20
            filled = int(percent / 5)
            if filled > 0:
                progress_bar = "🟩" * filled + "⬜" * (20 - filled)

            message = (
                f"📥 **در حال دانلود ویدیو از آپارات**\n\n"
                f"{progress_bar} {percent:.1f}%\n\n"
                f"📦 **حجم:** {downloaded_mb:.2f}/{total_mb:.2f} MB\n"
                f"🚀 **سرعت:** {speed_mb:.2f} MB/s\n"
                f"⏳ **زمان باقی‌مانده:** {eta} ثانیه"
            )

            # به‌روزرسانی پیام وضعیت
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message
            )

        elif d['status'] == 'finished':
            # اتمام دانلود
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="✅ **دانلود با موفقیت انجام شد!**\n\nدر حال پردازش و ارسال ویدیو..."
            )

    except Exception as e:
        print(f"خطا در به‌روزرسانی وضعیت: {e}")


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
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفاً لینک ویدیوی آپارات را ارسال کنید.")
    return "WAITING_FOR_LINK"


# دانلود ویدیو از آپارات با نمایش پیشرفت
async def download_aparat_video(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat_id
    user_data = context.user_data

    try:
        # اعتبارسنجی اولیه لینک
        if 'aparat.com' not in url:
            await update.message.reply_text("❌ لینک ارسال شده معتبر نیست! لطفاً فقط لینک آپارات ارسال کنید.")
            return "WAITING_FOR_LINK"

        # ایجاد پوشه دانلود
        os.makedirs('downloads', exist_ok=True)

        # ارسال پیام وضعیت اولیه
        status_message = await update.message.reply_text("🔍 در حال بررسی لینک...")
        user_data['status_message_id'] = status_message.message_id

        # دریافت اطلاعات اولیه ویدیو
        ydl_info = yt_dlp.YoutubeDL({'quiet': True})
        info_dict = ydl_info.extract_info(url, download=False)
        total_bytes = info_dict.get('filesize_approx') or info_dict.get('filesize') or 0

        # دریافت حلقه رویداد فعلی
        loop = asyncio.get_running_loop()

        # تنظیمات دانلود با بالاترین کیفیت
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'progress_hooks': [lambda d: asyncio.run_coroutine_threadsafe(
                progress_hook(d, context, chat_id, user_data['status_message_id'], total_bytes),
                loop
            )],
        }

        # به‌روزرسانی وضعیت به شروع دانلود
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['status_message_id'],
            text="⏬ دانلود ویدیو شروع شد..."
        )

        # دانلود ویدیو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

            # ارسال ویدیو
            await update.message.reply_video(
                video=open(file_path, 'rb'),
                caption="✅ ویدیو با موفقیت دانلود شد!",
                supports_streaming=True
            )

            # حذف فایل موقت
            os.remove(file_path)

        # حذف پیام وضعیت
        await context.bot.delete_message(chat_id=chat_id, message_id=user_data['status_message_id'])

    except DownloadError as e:
        error_message = f"❌ خطا در دانلود ویدیو: {str(e)}"
        print(error_message)
        await handle_download_error(update, context, error_message)

    except Exception as e:
        error_message = f"❌ خطای ناشناخته: {str(e)}"
        print(error_message)
        await handle_download_error(update, context, error_message)

    finally:
        # نمایش منوی مجدد
        return await show_aparat_menu(update, context)


# مدیریت خطاهای دانلود
async def handle_download_error(update: Update, context: CallbackContext, error_message: str):
    chat_id = update.message.chat_id
    user_data = context.user_data

    if 'status_message_id' in user_data:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=user_data['status_message_id'],
                text=error_message
            )
        except:
            await update.message.reply_text(error_message)
    else:
        await update.message.reply_text(error_message)


# نمایش منوی آپارات
async def show_aparat_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال لینک", callback_data="aparat_link")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)
    return "WAITING_FOR_LINK"