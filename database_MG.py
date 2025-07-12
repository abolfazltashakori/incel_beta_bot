import sqlite3

def create_connection():
    return sqlite3.connect('1mydatabase.db')

def create_table():
    conn = create_connection()
    try:
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

def save_user_to_db(telegram_id, first_name, last_name, username, balance, auther, number, ban):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute('''
            UPDATE users SET first_name = ?, last_name = ?, username = ?, balance = ?, auther = ?, number = ?, ban = ?
            WHERE telegram_id = ?
            ''', (first_name, last_name, username, balance, auther, number, ban, telegram_id))
        else:
            cursor.execute('''
            INSERT INTO users (telegram_id, first_name, last_name, username, balance, auther, number, ban)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, first_name, last_name, username, balance, auther, number, ban))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_download_history(user_id):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT title, link FROM downloads WHERE user_id=?', (user_id,))
        history = cursor.fetchall()
        return history
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def save_download_to_db(user_id, title, link):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO downloads (user_id, title, link)
        VALUES (?, ?, ?)
        ''', (user_id, title, link))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
