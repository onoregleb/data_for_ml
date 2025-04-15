# processing/feature_engineering.py
from database.sqlite_handler import SQLiteHandler

def engineer_features(db_handler):
    df = db_handler.read_sql("SELECT * FROM cleaned_vacancies")
    # Логика feature engineering как в оригинале
    ...
    db_handler.insert_data(df, "processed_vacancies")