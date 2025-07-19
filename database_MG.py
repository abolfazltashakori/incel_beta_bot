import sqlite3
import datetime


def create_connection():
    """ایجاد اتصال به دیتابیس"""
    return sqlite3.connect('main_beta_1_0_1_mydatabase.db', isolation_level=None)


def create_table():
    """ایجاد جداول مورد نیاز"""
    conn = create_connection()
    try:
        cursor = conn.cursor()

        # ایجاد جدول users (کامنت خارج از رشته SQL)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            balance INTEGER DEFAULT 0,
            auther BOOLEAN DEFAULT 0,
            number TEXT,
            ban BOOLEAN DEFAULT 0,
            filetolink_limit FLOAT DEFAULT 2147483648,
            last_reset_date TEXT,
            join_date TEXT DEFAULT CURRENT_DATE
        )
        ''')

        # ایجاد جدول downloads
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            link TEXT,
            download_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # ایجاد جدول daily_stats
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            total_users INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0,
            operations INTEGER DEFAULT 0
        )
        ''')

        # ایجاد جدول transactions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            receipt TEXT,
            status TEXT DEFAULT 'pending',
            transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        conn.commit()
        print("تمامی جداول با موفقیت ایجاد یا بررسی شدند")
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده در ایجاد جداول: {e}")
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
        print(f"محدودیت‌های آپلود برای همه کاربران در تاریخ {today} ریست شد")
    except sqlite3.Error as e:
        print(f"خطای ریست پایگاه داده: {e}")
    finally:
        conn.close()


def save_user_to_db(telegram_id, first_name, last_name, username, balance, auther, number, ban):
    """ذخیره یا به‌روزرسانی کاربر در دیتابیس"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT last_reset_date, join_date FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            last_reset_date = existing_user[0]
            join_date = existing_user[1]

            if last_reset_date != today:
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
            # کاربر جدید - ثبت تاریخ عضویت
            cursor.execute('''
            INSERT INTO users (
                telegram_id, first_name, last_name, username, 
                balance, auther, number, ban, last_reset_date, join_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, first_name, last_name, username, balance, auther, number, ban, today, today))

            # افزایش تعداد کاربران جدید در آمار روزانه
            increment_new_users_count()

        conn.commit()
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
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
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()


def get_user_limits(telegram_id):
    """دریافت محدودیت باقیمانده کاربر"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
        SELECT filetolink_limit, last_reset_date 
        FROM users 
        WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()

        if result:
            limit, reset_date = result
            if reset_date != today:
                return 2147483648  # ریست روزانه
            return limit
        return 2147483648  # کاربر جدید
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return 2147483648
    finally:
        conn.close()


def get_total_users_count():
    """دریافت تعداد کل کاربران"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return 0
    finally:
        conn.close()


def get_today_new_users_count():
    """دریافت تعداد کاربران جدید امروز"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", (today,))
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return 0
    finally:
        conn.close()


def update_daily_stats():
    """به‌روزرسانی آمار روزانه"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        total_users = get_total_users_count()
        new_users = get_today_new_users_count()

        # دریافت تعداد عملیات امروز (اگر وجود دارد)
        cursor.execute("SELECT operations FROM daily_stats WHERE date = ?", (today,))
        result = cursor.fetchone()
        operations = result[0] if result else 0

        # درج یا به‌روزرسانی آمار
        cursor.execute('''
        INSERT OR REPLACE INTO daily_stats (date, total_users, new_users, operations)
        VALUES (?, ?, ?, ?)
        ''', (today, total_users, new_users, operations))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()


def increment_operations_count():
    """افزایش شمارشگر عملیات روزانه"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # افزایش تعداد عملیات
        cursor.execute('''
        UPDATE daily_stats 
        SET operations = operations + 1 
        WHERE date = ?
        ''', (today,))

        # اگر رکوردی برای امروز وجود نداشت، ایجاد کنیم
        if cursor.rowcount == 0:
            update_daily_stats()
            cursor.execute('''
            UPDATE daily_stats 
            SET operations = operations + 1 
            WHERE date = ?
            ''', (today,))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()


def increment_new_users_count():
    """افزایش شمارشگر کاربران جدید"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
        UPDATE daily_stats 
        SET new_users = new_users + 1 
        WHERE date = ?
        ''', (today,))

        if cursor.rowcount == 0:
            update_daily_stats()

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()


def get_daily_stats(date=None):
    """دریافت آمار روزانه با کش نکردن نتایج"""
    conn = create_connection()
    try:
        target_date = date or datetime.datetime.now().strftime("%Y-%m-%d")
        cursor = conn.cursor()

        # محاسبه آمار واقعی هر بار
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE date(join_date) = date('now')")
        new_users = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(operations) FROM daily_stats WHERE date = ?", (target_date,))
        operations = cursor.fetchone()[0] or 0

        return {
            'date': target_date,
            'total_users': total_users,
            'new_users': new_users,
            'operations': operations
        }
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return {
            'date': target_date,
            'total_users': 0,
            'new_users': 0,
            'operations': 0
        }
    finally:
        conn.close()

def get_user_id_by_telegram(telegram_id):
    """دریافت شناسه کاربر بر اساس تلگرام آیدی"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return None
    finally:
        conn.close()

def add_transaction(user_id, amount, receipt=None):
    """ثبت تراکنش جدید"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO transactions (user_id, amount, receipt)
        VALUES (?, ?, ?)
        ''', (user_id, amount, receipt))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()

def update_balance(user_id, amount):
    """افزایش موجودی کاربر"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance + ?
        WHERE id = ?
        ''', (amount, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()

def get_user_balance(telegram_id):
    """دریافت موجودی کاربر"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return 0
    finally:
        conn.close()

def get_monthly_stats():
    """دریافت آمار ماهانه"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        current_month = datetime.datetime.now().strftime("%Y-%m")

        cursor.execute('''
        SELECT 
            SUM(new_users) AS monthly_new_users,
            SUM(operations) AS monthly_operations
        FROM daily_stats 
        WHERE strftime('%Y-%m', date) = ?
        ''', (current_month,))
        result = cursor.fetchone()

        return {
            'month': current_month,
            'new_users': result[0] if result and result[0] else 0,
            'operations': result[1] if result and result[1] else 0
        }
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return None
    finally:
        conn.close()


def get_last_30_days_stats():
    """دریافت آمار 30 روز گذشته"""
    conn = create_connection()
    try:
        cursor = conn.cursor()

        # تاریخ شروع (30 روز پیش)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        cursor.execute('''
        SELECT 
            date,
            total_users,
            new_users,
            operations
        FROM daily_stats 
        WHERE date >= ?
        ORDER BY date DESC
        ''', (start_date,))

        stats = []
        for row in cursor.fetchall():
            stats.append({
                'date': row[0],
                'total_users': row[1],
                'new_users': row[2],
                'operations': row[3]
            })

        return stats
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return []
    finally:
        conn.close()

def get_pending_transactions():
    """دریافت تراکنش‌های در انتظار تایید"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT transactions.id, user_id, amount, receipt, transaction_date, users.telegram_id as user_telegram_id
        FROM transactions 
        JOIN users ON transactions.user_id = users.id
        WHERE status = 'pending'
        ''')
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return []
    finally:
        conn.close()

def get_transaction_details(transaction_id):
    """دریافت جزئیات کامل یک تراکنش"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT 
            transactions.id,
            transactions.amount,
            transactions.transaction_date as date,
            users.telegram_id as user_telegram_id,
            users.first_name || ' ' || users.last_name as user_name
        FROM transactions
        JOIN users ON transactions.user_id = users.id
        WHERE transactions.id = ?
        ''', (transaction_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return None
    finally:
        conn.close()

def update_transaction_status(transaction_id, status):
    """به‌روزرسانی وضعیت تراکنش"""
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE transactions 
        SET status = ?
        WHERE id = ?
        ''', (status, transaction_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"خطای پایگاه داده: {e}")
        return False
    finally:
        conn.close()