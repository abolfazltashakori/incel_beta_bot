from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler

# تابع برای نمایش منوی اصلی VPN
async def vpn_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📦 بسته‌های عادی (1 ماهه)", callback_data='normal1')],
        [InlineKeyboardButton("🕒 بسته‌های لایف تایم", callback_data='normal2')],
        [InlineKeyboardButton("📅 بسته‌های بلند مدت", callback_data='normal3')],
        [InlineKeyboardButton("♾️ بسته‌های نامحدود", callback_data='normal4')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "🔒 <b>فروشگاه VPN</b>\n\n"
    message += "لطفاً نوع بسته مورد نظر خود را انتخاب کنید:\n"
    message += "────────────────────"
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
# تابع برای نمایش منوی "بسته های عادی"
async def normal1_menu(query):
    keyboard = [
        [InlineKeyboardButton("بسته 20 گیگ کاربر نامحدود 1 ماهه: 40t", callback_data='normal1_1')],
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود 1 ماهه: 90t", callback_data='normal1_2')],
        [InlineKeyboardButton("بسته 100 گیگ کاربر نامحدود 1 ماهه: 180t", callback_data='normal1_3')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_vpn')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("بسته مورد نظر را انتخاب کنید", reply_markup=reply_markup)

# تابع برای نمایش منوی "بسته های لایف تایم"
async def normal2_menu(query):
    keyboard = [
        [InlineKeyboardButton("بسته 10 گیگ کاربر نامحدود : 25t", callback_data='normal2_1')],
        [InlineKeyboardButton("بسته 20 گیگ کاربر نامحدود : 50t", callback_data='normal2_2')],
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود : 150t", callback_data='normal2_3')],
        [InlineKeyboardButton("بسته 100 گیگ کاربر نامحدود : 350t", callback_data='normal2_4')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_vpn')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("بسته مورد نظر را انتخاب کنید", reply_markup=reply_markup)

# تابع برای نمایش منوی "بسته های بلند مدت"
async def normal3_menu(query):
    keyboard = [
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود 2 ماهه: 125t", callback_data='normal3_1')],
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود 2 ماهه: 250t", callback_data='normal3_2')],
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود 2 ماهه: 375t", callback_data='normal3_3')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_vpn')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("بسته مورد نظر را انتخاب کنید", reply_markup=reply_markup)

# تابع برای نمایش منوی "بسته های نامحدود"
async def normal4_menu(query):
    keyboard = [
        [InlineKeyboardButton("بسته 10 گیگ کاربر نامحدود: 100t", callback_data='normal4_1')],
        [InlineKeyboardButton("بسته 50 گیگ کاربر نامحدود: 400t", callback_data='normal4_2')],
        [InlineKeyboardButton("بسته 100 گیگ کاربر نامحدود: 750t", callback_data='normal4_3')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_vpn')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("بسته نامحدود مورد نظر را انتخاب کنید", reply_markup=reply_markup)
