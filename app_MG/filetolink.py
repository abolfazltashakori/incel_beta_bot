import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# اطلاعات سرور Y
API_URL = 'https://c708480.parspack.net/upload'  # Endpoint URL سرور Y
ACCESS_KEY = 'kOA804bqN0kNZseP'  # Access Key سرور Y
SECRET_KEY = '0xN56PV49K5cR4cbyuK8AJmwp17LsiRD'  # Secret Key سرور Y

# وضعیت منتظر بودن برای فایل
WAITING_FOR_FILE = False


# منوی ارسال فایل
async def file_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ارسال فایل", callback_data='file_handler')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("لطفاً یک فایل ارسال کنید.", reply_markup=reply_markup)
    return WAITING_FOR_FILE  # ورود به مرحله دریافت فایل


# پردازش دکمه ارسال فایل
async def file_handler(update: Update, context: CallbackContext):
    global WAITING_FOR_FILE
    WAITING_FOR_FILE = True  # حالت منتظر بودن فایل را فعال می‌کنیم

    if update.message:
        await update.message.reply_text("لطفاً یک فایل ارسال کنید.")
    elif update.callback_query:
        await update.callback_query.answer("لطفاً یک فایل ارسال کنید.")


# دریافت و آپلود فایل
async def receive_file(update: Update, context: CallbackContext):
    global WAITING_FOR_FILE

    # اگر در حالت دریافت فایل هستیم
    if WAITING_FOR_FILE:
        if update.message and update.message.document:
            file = update.message.document
            file_id = file.file_id
            file_name = file.file_name

            # دریافت فایل از تلگرام
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(f'./{file_name}')

            # آپلود به سرور Y
            try:
                download_link = await upload_to_server_y(f'./{file_name}')
                await update.message.reply_text(
                    f"فایل شما با موفقیت آپلود شد. برای دانلود از لینک زیر استفاده کنید:\n{download_link}")
                WAITING_FOR_FILE = False  # بازنشانی وضعیت پس از دریافت فایل
            except Exception as e:
                await update.message.reply_text(f"خطا در آپلود فایل: {str(e)}")
                WAITING_FOR_FILE = False  # بازنشانی وضعیت پس از خطا
        else:
            await update.message.reply_text("لطفاً یک فایل ارسال کنید.")
    else:
        await update.message.reply_text("برای ارسال فایل، ابتدا دکمه ارسال فایل را فشار دهید.")


# آپلود فایل به سرور Y
async def upload_to_server_y(file_path):
    """
    این تابع به صورت غیرهمزمان فایل را به سرور Y آپلود می‌کند و لینک دانلود را برمی‌گرداند.
    """
    headers = {
        'Access-Key': ACCESS_KEY,
        'Secret-Key': SECRET_KEY
    }

    # ارسال درخواست غیرهمزمان با استفاده از aiohttp
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            async with session.post(API_URL, headers=headers, data=files) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("download_link")
                else:
                    raise Exception(f"خطا در آپلود فایل: {await response.text()}")
