import os
import sqlite3
import datetime


class Data:
    def createdb(self):
        con = sqlite3.connect('data.db')
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
        con = sqlite3.connect(os.path.join('db','data.db'))
        cur = con.cursor()
        cur.execute('INSERT INTO punishments(user_id, save_until_timestamp, times_triggered) VALUES(?, ?, ?)',
                    (user_id, save_until_timestamp, times_triggered))
        con.commit()

    def was_already_triggered(self, user_id):
        con = sqlite3.connect(os.path.join('db','data.db'))
        cur = con.cursor()
        value = cur.execute('SELECT * FROM punishments ORDER BY save_until_timestamp  WHERE user_id=?', (user_id,)).fetchone()
        if value is not None and value[2] < int(datetime.datetime.now().timestamp()):
            return value[3]
        return 0

    def increment_times_triggered(self, user_id):


# db = Data()
# db.createdb()