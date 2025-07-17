import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import yt_dlp
import logging

# تنظیم لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# تابعی برای چاپ لاگ‌های مربوط به دانلود
def progress_hook(d):
    if d['status'] == 'downloading':
        # دریافت مقادیر با بررسی وجود داشتن
        downloaded_bytes = d.get('downloaded_bytes', 0) or 0
        total_bytes = d.get('total_bytes')

        # اگر total_bytes وجود نداشت یا صفر بود
        if not total_bytes:
            total_bytes = 1  # مقدار پیش‌فرض برای جلوگیری از خطا

        percent = downloaded_bytes / total_bytes * 100
        speed = d.get('speed', 0) or 0
        speed_kb = speed / 1024  # تبدیل به کیلوبایت

        eta = d.get('eta', 0) or 0
        logger.info(f"در حال دانلود: {percent:.2f}% | سرعت دانلود: {speed_kb:.2f} KB/s | ETA: {eta}s")

    elif d['status'] == 'finished':
        logger.info(f"دانلود تمام شد: {d['filename']}")


# منوی یوتیوب
async def youtube_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال لینک", callback_data="youtube_link")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)


# درخواست لینک از کاربر
async def youtube_link(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفاً لینک ویدیوی یوتیوب را ارسال کنید.")
    return "WAITING_FOR_LINK"  # وضعیت برای دریافت لینک


# دانلود ویدیو از یوتیوب
async def download_youtube_video(update: Update, context: CallbackContext):
    url = update.message.text  # دریافت لینک ویدیو از پیام

    # مسیر فایل کوکی‌ها - استفاده از مسیر مطلق
    cookie_path = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')

    # تنظیمات پیشرفته yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'progress_hooks': [progress_hook],
        'cookiefile': cookie_path,
        'ignoreerrors': True,
        'no_warnings': True,
        'restrictfilenames': True,
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-threads', '4'],  # استفاده از چند هسته برای پردازش
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # اعتبارسنجی کوکی‌ها
            if os.path.exists(cookie_path):
                logger.info("استفاده از کوکی‌ها برای احراز هویت")
            else:
                logger.warning("فایل کوکی یافت نشد! دانلود بدون احراز هویت انجام می‌شود.")

            # استخراج اطلاعات ویدیو
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'video')
            duration = info_dict.get('duration', 0)

            # محدودیت مدت زمان (اختیاری)
            MAX_DURATION = 1800  # 30 دقیقه
            if duration > MAX_DURATION:
                await update.message.reply_text(f"❌ مدت زمان ویدیو نباید بیشتر از {MAX_DURATION // 60} دقیقه باشد.")
                return

            await update.message.reply_text(f"⬇️ در حال دانلود: {video_title}...")

            # دانلود واقعی ویدیو
            ydl.download([url])

            # یافتن فایل دانلود شده
            file_path = ydl.prepare_filename(info_dict)

            # اگر فایل ترکیب شده وجود ندارد، سعی در یافتن فایل اصلی
            if not os.path.exists(file_path):
                base_path = os.path.splitext(file_path)[0]
                for ext in ['.mp4', '.mkv', '.webm']:
                    if os.path.exists(base_path + ext):
                        file_path = base_path + ext
                        break

            # ارسال فایل به تلگرام
            await update.message.reply_text("✅ ویدیو دانلود شد! در حال ارسال...")
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    supports_streaming=True,
                    timeout=300  # افزایش زمان انتظار برای آپلود
                )

            # حذف فایل موقت
            os.remove(file_path)

            # نمایش مجدد منو
            keyboard = [
                [InlineKeyboardButton("ارسال لینک", callback_data="youtube_link")],
                [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("عملیات مورد نظر را انتخاب کنید", reply_markup=reply_markup)

    except yt_dlp.DownloadError as e:
        if "Sign in to confirm you're not a bot" in str(e):
            logger.error("خطای احراز هویت: کوکی‌ها معتبر نیستند")
            await update.message.reply_text(
                "❌ خطا در احراز هویت! لطفاً فایل کوکی‌ها را به‌روزرسانی کنید.\n\n"
                "راهنمای به‌روزرسانی کوکی‌ها:\n"
                "1. از افزونه مرورگر 'Get cookies.txt' استفاده کنید\n"
                "2. در YouTube.com وارد حساب خود شوید\n"
                "3. کوکی‌ها را برای youtube.com استخراج کنید\n"
                "4. فایل را با نام 'youtube_cookies.txt' در پوشه ربات آپلود کنید"
            )
        elif "Video unavailable" in str(e):
            await update.message.reply_text("❌ ویدیو در دسترس نیست یا محدودیت منطقه‌ای دارد.")
        else:
            await update.message.reply_text(f"❌ خطا در دانلود ویدیو: {str(e)}")
            logger.exception("خطا در دانلود یوتیوب")

    except Exception as e:
        await update.message.reply_text(f"❌ خطای سیستمی: {str(e)}")
        logger.exception("خطای غیرمنتظره")

    return "WAITING_FOR_LINK"