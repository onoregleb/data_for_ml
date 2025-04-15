import sqlite3
import pandas as pd

class SQLiteHandler:
    def __init__(self, db_path: str = "data.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vacancies (
                id TEXT PRIMARY KEY,
                name TEXT,
                salary_from REAL,
                salary_to REAL,
                salary_currency TEXT,
                employer_name TEXT,
                published_at TEXT,
                area_name TEXT,
                schedule TEXT,
                employment TEXT,
                experience TEXT,
                alternate_url TEXT
            )
        ''')
        self.conn.commit()

    def insert_data(self, df: pd.DataFrame, table: str):
        df.to_sql(table, self.conn, if_exists='append', index=False)

    def read_sql(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.conn)

    def close(self):
        self.conn.close()