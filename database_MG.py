import sqlite3

def create_connection():
    conn = sqlite3.connect('1mydatabase.db')  # نام فایل دیتابیس
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
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
        ban BOOLEAN
    )
    ''')
    conn.commit()
    conn.close()


def save_user_to_db(telegram_id, first_name, last_name, username, balance, auther, number, ban):
    conn = create_connection()
    cursor = conn.cursor()

    # بررسی وجود داده قبل از INSERT
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # اگر کاربر قبلاً وجود داشته باشد، عملیات UPDATE انجام می‌دهیم
        cursor.execute('''
        UPDATE users SET first_name = ?, last_name = ?, username = ?, balance = ?, auther = ?, number = ?, ban = ?
        WHERE telegram_id = ?
        ''', (first_name, last_name, username, balance, auther, number, ban, telegram_id))
    else:
        # اگر کاربر وجود نداشته باشد، عملیات INSERT انجام می‌دهیم
        cursor.execute('''
        INSERT INTO users (telegram_id, first_name, last_name, username, balance, auther, number, ban)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (telegram_id, first_name, last_name, username, balance, auther, number, ban))

    conn.commit()
    conn.close()


def get_download_history(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT title, link FROM downloads WHERE user_id = ?
    ''', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return [{"title": row[0], "link": row[1]} for row in history]

def create_download_history_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        link TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_download_to_db(user_id, title, link):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO downloads (user_id, title, link)
    VALUES (?, ?, ?)
    ''', (user_id, title, link))
    conn.commit()
    conn.close()
