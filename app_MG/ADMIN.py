from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database_MG import get_daily_stats, get_monthly_stats
import datetime


async def admin_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📊 آمار ربات", callback_data='bot_analyze')],
        [InlineKeyboardButton("📨 پیام همگانی", callback_data='everyone_message')],
        [InlineKeyboardButton("👥 بخش کاربران", callback_data='users_managment')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("منوی مدیریت:", reply_markup=reply_markup)


async def bot_analyze(update: Update, context: CallbackContext):
    try:
        # دریافت آمار با زمان فعلی برای جلوگیری از کش شدن
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        daily_stats = get_daily_stats()
        monthly_stats = get_monthly_stats() or {
            'month': datetime.datetime.now().strftime("%Y-%m"),
            'new_users': 0,
            'operations': 0
        }

        # اضافه کردن زمان به پیام برای منحصر به فرد شدن
        message = (
            f"📊 **آمار ربات** (آخرین به‌روزرسانی: {current_time})\n\n"
            f"📅 **آمار امروز**:\n"
            f"👤 کاربران کل: `{daily_stats.get('total_users', 0)}`\n"
            f"🆕 کاربران جدید: `{daily_stats.get('new_users', 0)}`\n"
            f"⚙️ عملیات انجام شده: `{daily_stats.get('operations', 0)}`\n\n"
            f"📈 **آمار ماه ({monthly_stats.get('month', '')})**:\n"
            f"🆕 کاربران جدید: `{monthly_stats.get('new_users', 0)}`\n"
            f"⚙️ عملیات انجام شده: `{monthly_stats.get('operations', 0)}`"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 به‌روزرسانی آمار", callback_data='refresh_stats')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # بررسی آیا محتوا تغییر کرده است
        if update.callback_query.message.text != message or str(update.callback_query.message.reply_markup) != str(reply_markup):
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.callback_query.answer("آمار قبلاً به‌روز است!")

    except Exception as e:
        print(f"خطا در نمایش آمار: {e}")
        await update.callback_query.answer("⚠️ خطا در به‌روزرسانی آمار")


# توابع دیگر (پیاده‌سازی اولیه)
async def everyone_message(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text("این بخش در حال توسعه است...")


async def users_managment(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🔍 جستجوی کاربر", callback_data='search_user')],
        [InlineKeyboardButton("🔐 تغییر وضعیت کاربر", callback_data='change_user_status')],
        [InlineKeyboardButton("📊 مشاهده کاربران", callback_data='view_users')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("مدیریت کاربران:", reply_markup=reply_markup)