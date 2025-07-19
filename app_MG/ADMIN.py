from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from database_MG import *


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
        [InlineKeyboardButton("💳 تراکنش‌های در انتظار", callback_data='pending_transactions')],  # اضافه شده
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("مدیریت کاربران:", reply_markup=reply_markup)


TRANSACTION_SELECTION, TRANSACTION_ACTION = range(2)


async def pending_transactions(update: Update, context: CallbackContext):
    """نمایش تراکنش‌های در انتظار تایید"""
    transactions = get_pending_transactions()

    if not transactions:
        await update.callback_query.edit_message_text("هیچ تراکنش در انتظاری وجود ندارد.")
        return ConversationHandler.END

    context.user_data['pending_transactions'] = transactions

    keyboard = []
    for idx, trans in enumerate(transactions):
        keyboard.append([InlineKeyboardButton(
            f"تراکنش #{idx + 1} - {trans['amount']} تومان",
            callback_data=f"trans_{idx}"
        )])

    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='users_managment')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "تراکنش‌های در انتظار تایید:",
        reply_markup=reply_markup
    )
    return TRANSACTION_SELECTION


async def select_transaction(update: Update, context: CallbackContext):
    """انتخاب تراکنش برای بررسی"""
    query = update.callback_query
    await query.answer()

    trans_idx = int(query.data.split('_')[1])
    transactions = context.user_data['pending_transactions']
    selected_trans = transactions[trans_idx]

    context.user_data['selected_trans'] = selected_trans

    # دریافت اطلاعات کامل تراکنش
    trans_details = get_transaction_details(selected_trans['id'])

    message = (
        f"🔍 تراکنش #{trans_idx + 1}\n\n"
        f"👤 کاربر: {trans_details['user_name']}\n"
        f"💳 مبلغ: {trans_details['amount']} تومان\n"
        f"📅 تاریخ: {trans_details['date']}\n"
        f"🆔 شناسه تراکنش: {trans_details['id']}"
    )

    keyboard = [
        [InlineKeyboardButton("مشاهده رسید", callback_data="view_receipt")],
        [InlineKeyboardButton("تایید تراکنش", callback_data="approve_trans")],
        [InlineKeyboardButton("رد تراکنش", callback_data="reject_trans")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_transactions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, reply_markup=reply_markup)
    return TRANSACTION_ACTION


async def view_receipt(update: Update, context: CallbackContext):
    """ارسال تصویر رسید به ادمین"""
    query = update.callback_query
    await query.answer()

    trans = context.user_data['selected_trans']

    # ارسال تصویر رسید
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=trans['receipt'],
        caption=f"📎 رسید تراکنش #{trans['id']}"
    )

    # باقی ماندن در همین حالت برای انجام اقدامات بعدی
    return TRANSACTION_ACTION


async def approve_transaction(update: Update, context: CallbackContext):
    """تایید تراکنش و افزایش موجودی کاربر"""
    query = update.callback_query
    await query.answer()

    trans = context.user_data['selected_trans']

    # افزایش موجودی کاربر
    success = update_balance(trans['user_id'], trans['amount'])

    if success:
        # به‌روزرسانی وضعیت تراکنش
        update_transaction_status(trans['id'], 'approved')
        await query.edit_message_text(f"✅ تراکنش #{trans['id']} با موفقیت تایید شد!")

        # ارسال پیام به کاربر
        await context.bot.send_message(
            chat_id=trans['user_telegram_id'],
            text=f"✅ تراکنش شما به مبلغ {trans['amount']} تومان تایید شد!"
        )
    else:
        await query.edit_message_text("❌ خطا در تایید تراکنش!")

    return ConversationHandler.END


async def reject_transaction(update: Update, context: CallbackContext):
    """رد تراکنش"""
    query = update.callback_query
    await query.answer()

    trans = context.user_data['selected_trans']

    # به‌روزرسانی وضعیت تراکنش
    update_transaction_status(trans['id'], 'rejected')
    await query.edit_message_text(f"❌ تراکنش #{trans['id']} رد شد!")

    # ارسال پیام به کاربر
    await context.bot.send_message(
        chat_id=trans['user_telegram_id'],
        text=f"❌ تراکنش شما به مبلغ {trans['amount']} تومان رد شد. لطفاً با پشتیبانی تماس بگیرید."
    )

    return ConversationHandler.END


async def back_to_transactions(update: Update, context: CallbackContext):
    """بازگشت به لیست تراکنش‌ها"""
    return await pending_transactions(update, context)