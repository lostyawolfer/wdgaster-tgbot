import os
import sqlite3
import datetime


class Punishments:
    def createdb(self):
        con = sqlite3.connect('punishments.db')
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS punishments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            save_until_timestamp INTEGER,
            times_triggered INTEGER
            )
        ''')
        con.commit()

    def add_data(self, user_id, save_until_timestamp, times_triggered):
        con = sqlite3.connect(os.path.join('db','punishments.db'))
        cur = con.cursor()
        cur.execute('INSERT INTO punishments(user_id, save_until_timestamp, times_triggered) VALUES(?, ?, ?)',
                    (user_id, save_until_timestamp, times_triggered))
        con.commit()

    def was_already_triggered(self, user_id):
        con = sqlite3.connect(os.path.join('db','punishments.db'))
        cur = con.cursor()
        value = cur.execute('SELECT * FROM punishments ORDER BY save_until_timestamp  WHERE user_id=?', (user_id,)).fetchone()
        if value is not None and value[2] < int(datetime.datetime.now().timestamp()):
            return value[3]
        return 0

    def increment_times_triggered(self, user_id):
        ...

class Pronouns:
    def createdb(self):
        con = sqlite3.connect(os.path.join('db','pronouns.db'))
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pronouns(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            pronouns TEXT
            )
        ''')
        con.commit()

    def find_if_user_exists(self, user_id) -> bool:
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()
        query = cur.execute('SELECT * FROM pronouns WHERE user_id=?', (user_id,)).fetchone()
        if query:
            return True
        return False

    def add_pronouns(self, user_id, username, pronouns):
        con = sqlite3.connect(os.path.join('db','pronouns.db'))
        cur = con.cursor()
        user_exists = self.find_if_user_exists(user_id)

        pronouns = pronouns.replace("\n", " ").replace('\r', ' ')

        if not user_exists:
            cur.execute('INSERT INTO pronouns(user_id, username, pronouns) VALUES(?, ?, ?)',
                        (user_id, username, pronouns))
        else:
            cur.execute('UPDATE pronouns SET pronouns=? WHERE user_id=?', (pronouns, user_id))

        con.commit()

    def get_pronouns(self, user_id) -> str | None:
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()

        pronouns = cur.execute('SELECT pronouns FROM pronouns WHERE user_id=?', (user_id,)).fetchone()
        return pronouns[0] if pronouns is not None else None

    def get_pronouns_by_username(self, username) -> str | None:
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()

        pronouns = cur.execute('SELECT pronouns FROM pronouns WHERE username=?', (username,)).fetchone()
        return pronouns[0] if pronouns is not None else None

    def get_user_id_by_username(self, username) -> int | None:
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()

        user_id = cur.execute('SELECT user_id FROM pronouns WHERE username=?', (username,)).fetchone()
        return user_id[0] if user_id is not None else None

    def rm_pronouns(self, user_id):
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()
        cur.execute('DELETE FROM pronouns WHERE user_id=?', (user_id,))
        con.commit()

    def get_all_data(self):
        con = sqlite3.connect(os.path.join('db', 'pronouns.db'))
        cur = con.cursor()
        data = cur.execute('SELECT user_id, username, pronouns FROM pronouns').fetchall()
        return data
