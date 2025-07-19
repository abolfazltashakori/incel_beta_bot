from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler
import database_MG as db  # ایمپورت ماژول دیتابیس

# حالت‌های مکالمه
AMOUNT, RECEIPT = range(2)


async def wallet_menu(update: Update, context: CallbackContext):
    """منوی کیف پول با گزینه مشاهده موجودی"""
    user_id = update.callback_query.from_user.id
    balance = db.get_user_balance(user_id)

    keyboard = [
        [InlineKeyboardButton("افزایش موجودی (کارت به کارت)", callback_data="wallet_cart")],
        [InlineKeyboardButton("مشاهده موجودی", callback_data="view_balance")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"💰 موجودی فعلی شما: {balance} تومان\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=reply_markup
    )


async def view_balance(update: Update, context: CallbackContext):
    """نمایش موجودی کاربر"""
    user_id = update.callback_query.from_user.id
    balance = db.get_user_balance(user_id)

    keyboard = [
        [InlineKeyboardButton("افزایش موجودی", callback_data="wallet_cart")],
        [InlineKeyboardButton("بازگشت", callback_data="back_to_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"💳 موجودی حساب شما: {balance} تومان",
        reply_markup=reply_markup
    )


async def wallet_cart(update: Update, context: CallbackContext):
    """شروع فرآیند واریز کارت به کارت"""
    keyboard = [
        [InlineKeyboardButton("لغو", callback_data="cancel_transaction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "💳 لطفاً مبلغ واریزی را به تومان وارد کنید:\n"
        "• حداقل مبلغ: 25,000 تومان\n"
        "• حداکثر مبلغ: 500,000 تومان",
        reply_markup=reply_markup
    )
    return AMOUNT


async def get_amount(update: Update, context: CallbackContext):
    """دریافت مبلغ از کاربر"""
    try:
        amount = int(update.message.text)
        if amount < 25000 or amount > 500000:
            await update.message.reply_text("❌ مبلغ باید بین 25,000 تا 500,000 تومان باشد. لطفاً مجدداً وارد کنید:")
            return AMOUNT

        context.user_data['amount'] = amount

        # اطلاعات کارت ادمین
        admin_card = """
        💳 اطلاعات کارت برای واریز:

        بانک: ملت
        شماره کارت: 5460-0441-8618-6219
        به نام: ابوالفضل تشکری

        ✅ پس از واریز، تصویر رسید را ارسال کنید.
        """

        await update.message.reply_text(admin_card)
        await update.message.reply_text("📎 لطفاً تصویر رسید واریزی را ارسال کنید:")
        return RECEIPT

    except ValueError:
        await update.message.reply_text("❌ لطفاً فقط عدد وارد کنید (مثال: 50000):")
        return AMOUNT


async def get_receipt(update: Update, context: CallbackContext):
    """دریافت تصویر رسید واریزی"""
    # دریافت فایل رسید
    receipt_file = None
    if update.message.photo:
        receipt_file = update.message.photo[-1].file_id
    elif update.message.document:
        receipt_file = update.message.document.file_id

    if not receipt_file:
        await update.message.reply_text("❌ لطفاً یک تصویر معتبر ارسال کنید.")
        return RECEIPT

    # ذخیره تراکنش در دیتابیس
    user_id = update.message.from_user.id
    db_user_id = db.get_user_id_by_telegram(user_id)
    amount = context.user_data['amount']

    if db_user_id:
        transaction_id = db.add_transaction(db_user_id, amount, receipt_file)
        if transaction_id:
            # اطلاع به ادمین (در اینجا باید کد اطلاع‌رسانی به ادمین اضافه شود)
            await update.message.reply_text(
                "✅ رسید شما با موفقیت ثبت شد و در انتظار تایید ادمین است.\n"
                "پس از تایید، موجودی حساب شما افزایش خواهد یافت."
            )
        else:
            await update.message.reply_text("❌ خطا در ثبت تراکنش. لطفاً مجدداً تلاش کنید.")
    else:
        await update.message.reply_text("❌ کاربر یافت نشد!")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_transaction(update: Update, context: CallbackContext):
    """لغو تراکنش"""
    context.user_data.clear()
    await update.callback_query.edit_message_text("❌ تراکنش لغو شد.")
    return ConversationHandler.END


