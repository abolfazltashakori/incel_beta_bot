import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import yt_dlp
import logging

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            downloaded_bytes = d.get('downloaded_bytes', 0) or 0
            total_bytes = d.get('total_bytes', 1) or 1

            # تبدیل به عدد در صورت نیاز
            downloaded_bytes = float(downloaded_bytes) if downloaded_bytes else 0
            total_bytes = float(total_bytes) if total_bytes else 1

            percent = (downloaded_bytes / total_bytes) * 100
            speed = (d.get('speed', 0) or 0) / 1024  # KB/s
            eta = d.get('eta', 0) or 0

            logger.info(f"پیشرفت: {percent:.1f}% | سرعت: {speed:.2f} KB/s | زمان باقی‌مانده: {eta}s")
        except Exception as e:
            logger.error(f"خطا در پردازش پیشرفت: {str(e)}")

    elif d['status'] == 'finished':
        logger.info(f"دانلود کامل شد: {d.get('filename', 'فایل ناشناخته')}")


async def youtube_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال لینک", callback_data="youtube_link")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🎬 منوی یوتیوب - لطفا عمل مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )


async def youtube_link(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🔗 لطفاً لینک ویدیوی یوتیوب را ارسال کنید\n\n"
        "⚠️ توجه: ویدیوهای طولانی‌تر از 30 دقیقه پشتیبانی نمی‌شوند"
    )
    return "WAITING_FOR_LINK"


async def download_youtube_video(update: Update, context: CallbackContext):
    url = update.message.text.strip()

    # اعتبارسنجی اولیه لینک
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ فرمت لینک نامعتبر است!")
        return "WAITING_FOR_LINK"

    # تنظیمات دانلود
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'cookiefile': os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt'),
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-threads', '4'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # دریافت اطلاعات ویدیو
            try:
                info_dict = ydl.extract_info(url, download=False)
                if not info_dict:
                    raise ValueError("اطلاعات ویدیو دریافت نشد")
            except Exception as e:
                logger.error(f"خطا در دریافت اطلاعات: {str(e)}")
                await update.message.reply_text(
                    "❌ خطا در دریافت اطلاعات ویدیو!\n"
                    "دلایل احتمالی:\n"
                    "- لینک نامعتبر\n"
                    "- ویدیو خصوصی/حذف شده\n"
                    "- محدودیت منطقه‌ای\n\n"
                    "لطفاً لینک را بررسی و مجدد ارسال کنید."
                )
                return "WAITING_FOR_LINK"

            # بررسی مدت زمان ویدیو
            MAX_DURATION = 1800  # 30 دقیقه
            duration = info_dict.get('duration', 0)
            if duration > MAX_DURATION:
                await update.message.reply_text(
                    f"⏳ مدت زمان ویدیو ({duration // 60} دقیقه) بیشتر از حد مجاز ({MAX_DURATION // 60} دقیقه) است!"
                )
                return "WAITING_FOR_LINK"

            video_title = info_dict.get('title', 'ویدیو یوتیوب')
            await update.message.reply_text(f"⏳ در حال دانلود: {video_title}...")

            # دانلود ویدیو
            try:
                ydl.download([url])
            except Exception as e:
                logger.error(f"خطا در دانلود: {str(e)}")
                await update.message.reply_text("❌ خطا در فرآیند دانلود!")
                return "WAITING_FOR_LINK"

            # یافتن فایل دانلود شده
            file_path = ydl.prepare_filename(info_dict)
            if not os.path.exists(file_path):
                base_path = os.path.splitext(file_path)[0]
                for ext in ['.mp4', '.mkv', '.webm']:
                    if os.path.exists(base_path + ext):
                        file_path = base_path + ext
                        break

            if not os.path.exists(file_path):
                raise FileNotFoundError("فایل دانلود شده یافت نشد")

            # ارسال ویدیو
            await update.message.reply_text("✅ دانلود با موفقیت انجام شد! در حال آپلود...")
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎥 {video_title}",
                    supports_streaming=True,
                    timeout=300,
                    width=info_dict.get('width'),
                    height=info_dict.get('height'),
                    duration=duration
                )

            # پاکسازی فایل موقت
            try:
                os.remove(file_path)
            except:
                logger.warning(f"خطا در حذف فایل موقت: {file_path}")

            # نمایش مجدد منو
            return await youtube_menu(update, context)

    except yt_dlp.DownloadError as e:
        error_msg = str(e).lower()
        if "sign in" in error_msg:
            msg = ("🔒 خطای احراز هویت!\n\n"
                   "برای دانلود این ویدیو نیاز به احراز هویت دارید:\n"
                   "1. از افزونه 'Get cookies.txt' در کروم استفاده کنید\n"
                   "2. در YouTube.com وارد حساب شوید\n"
                   "3. کوکی‌ها را استخراج کنید\n"
                   "4. فایل را با نام 'youtube_cookies.txt' در پوشه ربات قرار دهید")
        elif "unavailable" in error_msg:
            msg = "🚫 ویدیو در دسترس نیست یا محدودیت منطقه‌ای دارد"
        else:
            msg = f"❌ خطای دانلود: {str(e)}"

        await update.message.reply_text(msg)
        logger.error(f"خطای یوتیوب: {str(e)}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطای سیستمی: {str(e)}")
        logger.exception("خطای غیرمنتظره در دانلود یوتیوب")

    return "WAITING_FOR_LINK"