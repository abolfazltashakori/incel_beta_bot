import sqlite3
import datetime


def create_connection():
    """ایجاد اتصال به دیتابیس"""
    return sqlite3.connect('main_mydatabase.db')


def create_table():
    """ایجاد جداول مورد نیاز"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'filetolink_limit' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN filetolink_limit FLOAT DEFAULT 2147483648")

        if 'last_reset_date' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_reset_date TEXT")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            balance INTEGER,
            auther BOOLEAN,
            number TEXT,
            ban BOOLEAN,
            filetolink_limit FLOAT DEFAULT 2147483648, -- 2GB به بایت
            last_reset_date TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            link TEXT
        )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def reset_filetolink_limits():
    """ریست محدودیت روزانه همه کاربران"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
        UPDATE users 
        SET filetolink_limit = 2147483648, 
            last_reset_date = ?
        ''', (today,))
        conn.commit()
        print(f"Reset filetolink limits for all users on {today}")
    except sqlite3.Error as e:
        print(f"Database reset error: {e}")
    finally:
        conn.close()


def save_user_to_db(telegram_id, first_name, last_name, username, balance, auther, number, ban):
    """ذخیره یا به‌روزرسانی کاربر در دیتابیس"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        if existing_user:
            # Get column index safely
            reset_date_index = len(existing_user) - 1  # last_reset_date is last column
            last_reset_date = existing_user[reset_date_index] if reset_date_index >= 0 else None

            if last_reset_date != today:  # استفاده از متغیر محاسبه شده
                cursor.execute('''
                UPDATE users SET 
                    first_name = ?, 
                    last_name = ?, 
                    username = ?, 
                    balance = ?, 
                    auther = ?, 
                    number = ?, 
                    ban = ?,
                    filetolink_limit = 2147483648,
                    last_reset_date = ?
                WHERE telegram_id = ?
                ''', (first_name, last_name, username, balance, auther, number, ban, today, telegram_id))
            else:
                cursor.execute('''
                UPDATE users SET 
                    first_name = ?, 
                    last_name = ?, 
                    username = ?, 
                    balance = ?, 
                    auther = ?, 
                    number = ?, 
                    ban = ?
                WHERE telegram_id = ?
                ''', (first_name, last_name, username, balance, auther, number, ban, telegram_id))
        else:
            cursor.execute('''
            INSERT INTO users (
                telegram_id, first_name, last_name, username, 
                balance, auther, number, ban, last_reset_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, first_name, last_name, username, balance, auther, number, ban, today))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def reduce_filetolink_limit(telegram_id, file_size):
    """کاهش محدودیت کاربر پس از آپلود فایل"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET filetolink_limit = filetolink_limit - ?
        WHERE telegram_id = ? AND filetolink_limit >= ?
        ''', (file_size, telegram_id, file_size))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def get_user_limits(telegram_id):
    """دریافت محدودیت باقیمانده کاربر"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT filetolink_limit, last_reset_date 
        FROM users 
        WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()

        if result:
            limit, reset_date = result
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            if reset_date != today:
                return 2147483648  # ریست روزانه
            return limit
        return 2147483648  # کاربر جدید
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 2147483648
    finally:
        conn.close()