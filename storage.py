import sqlite3
from typing import Optional

from appconfig import AppConfig, DatabaseConfig
from mahjong import MahjongQuestion


class Storage:
    setting: DatabaseConfig

    def __init__(self, appconfig: AppConfig):
        self.setting = appconfig.database
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.setting.name)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mahjong_question (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          question TEXT, hand TEXT, answer TEXT, 
          explanation TEXT, difficulty INTEGER)
          ''')
        conn.commit()
        conn.close()

    def insert_question(self, question: MahjongQuestion):
        conn = sqlite3.connect(self.setting.name)
        c = conn.cursor()
        c.execute(
            "INSERT INTO mahjong_question (question, hand, answer, explanation, difficulty) "
            "VALUES (?, ?, ?, ?, ?)",
            question.serialize())
        conn.commit()
        _id = c.lastrowid
        conn.close()

        return _id

    def find_question(self, question_id) -> Optional[MahjongQuestion]:
        conn = sqlite3.connect(self.setting.name)
        c = conn.cursor()
        c.execute(
            "SELECT id, question, hand, answer, explanation, difficulty "
            "FROM mahjong_question WHERE id=?",
            (question_id,))
        question = c.fetchone()
        conn.close()

        if question is None:
            return None

        return MahjongQuestion.deserialize(
            (question[0], question[1], question[2],
             question[3], question[4], question[5]))
