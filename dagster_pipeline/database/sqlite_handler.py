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
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS merged_vacancies (
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS features_for_model (
                id TEXT PRIMARY KEY,
                salary_mean REAL,
                curr_RUR REAL,
                sched_Гибкий_график REAL,
                sched_Полный_день REAL,
                sched_Сменный_график REAL,
                sched_Удаленная_работа REAL,
                employ_Полная_занятость REAL,
                employ_Проектная_работа REAL,
                employ_Стажировка REAL,
                employ_Частичная_занятость REAL,
                experience_level INTEGER,
                job_title_encoded REAL,
                region_encoded REAL,
                employer_encoded REAL
            )
        ''')
        self.conn.commit()

    def insert_data(self, df: pd.DataFrame, table: str):
        if 'id' not in df.columns:
            raise ValueError("DataFrame must contain an 'id' column.")

        bool_cols = df.select_dtypes(include='bool').columns
        df[bool_cols] = df[bool_cols].astype(int)

        df = df.drop_duplicates(subset='id')

        # Получаем список колонок таблицы
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        table_columns = [row[1] for row in cursor.fetchall()]

        filtered_df = df[[col for col in df.columns if col in table_columns]]
        dropped_cols = set(df.columns) - set(filtered_df.columns)
        if dropped_cols:
            print(f"[insert_data] Пропущены лишние колонки: {dropped_cols}")

        if not filtered_df.empty:
            placeholders = ', '.join(['?'] * len(filtered_df.columns))
            columns = ', '.join(filtered_df.columns)
            insert_query = f'''
                INSERT OR IGNORE INTO {table} ({columns})
                VALUES ({placeholders})
            '''
            cursor.executemany(insert_query, filtered_df.values.tolist())
            self.conn.commit()
            print(f"[insert_data] Добавлено {cursor.rowcount} новых записей.")
        else:
            print(f"[insert_data] Нет новых данных для вставки.")

    def read_sql(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.conn)

    def close(self):
        self.conn.close()