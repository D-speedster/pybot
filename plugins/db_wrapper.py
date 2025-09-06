import sqlite3
from config import db_config


class DB:
    def __init__(self):
        self.mydb = sqlite3.connect(db_config['database'])
        self.cursor = self.mydb.cursor()

    def setup(self) -> None:
        try:
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS posts (msg_id INTEGER NOT NULL PRIMARY KEY, chat TEXT NOT NULL, like_ids TEXT, unlike_ids TEXT, likes INTEGER DEFAULT 0, unlikes INTEGER DEFAULT 0)")
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS insta_acc (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL)")
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, last_download TEXT NOT NULL, last_like INTEGER DEFAULT 0)")
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to creating tables: {}".format(error))

    def register_post(self, msg_id: int, chat: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'INSERT INTO posts (msg_id, chat) VALUES (?, ?)'
            record = (msg_id, chat)
            self.cursor.execute(query, record)
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to Insert user: {}".format(error))

    def get_likes(self, msg_id: int, chat: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT likes, unlikes FROM posts WHERE msg_id = ? AND chat = ?;'
            self.cursor.execute(query, (msg_id, chat))
            records = self.cursor.fetchone()
            print(records)
            self.cursor.close()
            return records
        except sqlite3.Error as error:
            print("Failed to get all users id: {}".format(error))

    def add_like(self, msg_id: int, user_id: int,  chat: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT like_ids, unlike_ids, likes, unlikes  FROM posts WHERE msg_id = ? AND chat = ?'
            self.cursor.execute(query, (msg_id, chat))
            records = self.cursor.fetchone()
            like_ids = records[0]
            if like_ids == None:
                like_ids = ""
            unlike_ids = records[1]
            if unlike_ids == None:
                unlike_ids = ""
            likes = records[2]
            unlikes = records[3]
            user_id = str(user_id)

            if user_id in like_ids:
                like_ids = like_ids.replace(f"{user_id}|", "")
                likes = likes - 1
            else:
                if user_id in unlike_ids:
                    unlike_ids = unlike_ids.replace(f"{user_id}|", "")
                    unlikes = unlikes - 1
                    query = 'UPDATE posts SET unlike_ids = ?, unlikes = ? WHERE msg_id = ? AND chat = ?'
                    record = (unlike_ids, unlikes, msg_id, chat)
                    self.cursor.execute(query, record)
                like_ids = f"{user_id}|{like_ids}"
                likes = likes + 1

            query = 'UPDATE posts SET like_ids = ?, likes = ? WHERE msg_id = ? AND chat = ?'
            record = (like_ids, likes, msg_id, chat)
            self.cursor.execute(query, record)

            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to Insert user: {}".format(error))

    def add_unlike(self, msg_id: int, user_id: int,  chat: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT like_ids, unlike_ids, likes, unlikes  FROM posts WHERE msg_id = ? AND chat = ?'
            self.cursor.execute(query, (msg_id, chat))
            records = self.cursor.fetchone()
            like_ids = records[0]
            if like_ids == None:
                like_ids = ""
            unlike_ids = records[1]
            if unlike_ids == None:
                unlike_ids = ""
            likes = records[2]
            unlikes = records[3]
            user_id = str(user_id)

            if user_id in unlike_ids:
                unlike_ids = unlike_ids.replace(f"{user_id}|", "")
                unlikes = unlikes - 1
            else:
                if user_id in like_ids:
                    like_ids = like_ids.replace(f"{user_id}|", "")
                    likes = likes - 1
                    query = 'UPDATE posts SET like_ids = ?, likes = ? WHERE msg_id = ? AND chat = ?'
                    record = (like_ids, likes, msg_id, chat)
                    self.cursor.execute(query, record)
                unlike_ids = f"{user_id}|{unlike_ids}"
                unlikes = unlikes + 1

            query = 'UPDATE posts SET unlike_ids = ?, unlikes = ? WHERE msg_id = ? AND chat = ?'
            record = (unlike_ids, unlikes, msg_id, chat)
            self.cursor.execute(query, record)

            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to Insert user: {}".format(error))

    def register_user(self, user_id: int, last_download: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'INSERT INTO users (user_id, last_download) VALUES (?, ?)'
            record = (user_id, last_download)
            self.cursor.execute(query, record)
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to Insert user: {}".format(error))

    def check_user_register(self, user_id: int) -> bool:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT user_id FROM users WHERE user_id = ?'
            self.cursor.execute(query, (user_id,))
            records = self.cursor.fetchall()
            self.cursor.close()
            if (int(user_id),) in records:
                return True
            else:
                return False
        except sqlite3.Error as error:
            print("Failed to check user: {}".format(error))

    def get_users_id(self) -> any:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT user_id FROM users;'
            self.cursor.execute(query)
            records = self.cursor.fetchall()
            self.cursor.close()
            return records
        except sqlite3.Error as error:
            print("Failed to get all users id: {}".format(error))

    def get_insta_acc(self) -> any:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT username, password FROM insta_acc;'
            self.cursor.execute(query)
            records = self.cursor.fetchall()
            self.cursor.close()
            return records
        except sqlite3.Error as error:
            print("Failed to get instagram account: {}".format(error))

    def save_insta_acc(self, username: str, password: str) -> any:
        try:
            self.cursor = self.mydb.cursor()
            query = 'INSERT INTO insta_acc (username, password) VALUES (?, ?)'
            record = (username, password)
            self.cursor.execute(query, record)
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to Insert instagram account: {}".format(error))

    def get_last_download(self, user_id: int) -> str:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT last_download FROM users WHERE user_id = ?'
            self.cursor.execute(query, (user_id,))
            record = self.cursor.fetchall()
            self.cursor.close()
            return record[0][0]
        except sqlite3.Error as error:
            print("Failed to get last download of user: {}".format(error))

    def update_last_download(self, user_id: int, last_download: str) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'UPDATE users SET last_download = ? WHERE user_id = ?'
            record = (last_download, user_id)
            self.cursor.execute(query, record)
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to update last download of user: {}".format(error))

    def get_last_like(self, user_id: int) -> str:
        try:
            self.cursor = self.mydb.cursor()
            query = 'SELECT last_like FROM users WHERE user_id = ?'
            self.cursor.execute(query, (user_id,))
            record = self.cursor.fetchall()
            self.cursor.close()
            return record[0][0]
        except sqlite3.Error as error:
            print("Failed to get last download of user: {}".format(error))

    def update_last_like(self, user_id: int, last_like: int) -> None:
        try:
            self.cursor = self.mydb.cursor()
            query = 'UPDATE users SET last_like = ? WHERE user_id = ?'
            record = (last_like, user_id)
            self.cursor.execute(query, record)
            self.mydb.commit()
            self.cursor.close()
        except sqlite3.Error as error:
            print("Failed to update last download of user: {}".format(error))

    def add_user(self, user_id: int, username: str = "") -> None:
        """اضافه کردن کاربر جدید یا به‌روزرسانی اطلاعات موجود"""
        try:
            if not self.check_user_register(user_id):
                from datetime import datetime
                current_time = str(datetime.now())
                self.register_user(user_id, current_time)
        except Exception as error:
            print(f"Failed to add user: {error}")
