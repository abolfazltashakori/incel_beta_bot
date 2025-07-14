import yt_dlp

def download_with_cookies(url):
    # تنظیمات دانلود برای استفاده از کوکی‌ها
    ydl_opts = {
        'format': 'bestaudio/best',  # دانلود بهترین کیفیت صوتی
        'postprocessors': [{
            'key': 'FFmpegPostProcessor',  # پست‌پردوسر صحیح برای تبدیل به صوت
            'preferredcodec': 'mp3',  # تبدیل به فرمت MP3
            'preferredquality': '192',  # کیفیت صوتی 192kbps
        }],
        'outtmpl': '%(title)s.%(ext)s',  # نام فایل بر اساس عنوان آهنگ
        'cookies': 'soundcloud_cooki.txt',  # مسیر فایل کوکی‌ها
    }

    # دانلود محتوا
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# مثال استفاده
download_with_cookies('https://soundcloud.com/alisorena/istgaheshahreyakh?si=24335f72cee043618d47f871a6b64a66&utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing')  # لینک آهنگ ساندکلاود
