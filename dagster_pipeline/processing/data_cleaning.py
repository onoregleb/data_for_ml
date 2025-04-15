# processing/data_cleaning.py
import pandas as pd
from database.sqlite_handler import SQLiteHandler


def merge_datasets(db_handler):
    df_api = db_handler.read_sql("SELECT * FROM vacancies WHERE source='hh'")
    df_web = db_handler.read_sql("SELECT * FROM vacancies WHERE source='getmatch'")

    merged_df = pd.concat([df_api, df_web], ignore_index=True)
    # Логика объединения как в оригинале
    ...

    db_handler.insert_data(merged_df, "merged_vacancies")


def clean_data(db_handler):
    df = db_handler.read_sql("SELECT * FROM merged_vacancies")
    # Логика очистки данных как в оригинале
    ...
    db_handler.insert_data(df, "cleaned_vacancies")