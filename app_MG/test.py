import ftplib

def upload_file_to_ftp(file_path):
    ftp_host = "185.235.196.18"  # آدرس سرور FTP
    ftp_user = "incelspa"  # نام کاربری FTP
    ftp_pass = "p3tPE51mX+(hH0"  # پسورد FTP

    try:
        # اتصال به سرور FTP
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login(ftp_user, ftp_pass)  # وارد کردن نام کاربری و پسورد
            ftp.cwd("public_html")
            # آپلود فایل
            with open(file_path, 'rb') as f:
                ftp.storbinary(f'STOR {file_path}', f)  # ارسال فایل به سرور

            print(f'فایل {file_path} با موفقیت به سرور FTP آپلود شد.')

    except ftplib.all_errors as e:
        print(f"خطا در اتصال یا آپلود فایل: {e}")

# فراخوانی تابع با فایل مورد نظر
upload_file_to_ftp('cookies.txt')  # به جای 'test.txt' نام فایل خود را وارد کنید
