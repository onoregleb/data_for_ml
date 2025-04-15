import sys
sys.path.append("C:/Users/Gleb Onore/Desktop/data_for_ml/dagster_pipeline")

import pandas as pd


def merge_datasets(db_handler):
    df_api = db_handler.read_sql("SELECT * FROM vacancies WHERE source='hh'")
    df_web = db_handler.read_sql("SELECT * FROM vacancies WHERE source='getmatch'")

    # Приведение published_at к datetime
    df_api['published_at'] = pd.to_datetime(df_api['published_at'], errors='coerce')
    df_web['published_at'] = pd.to_datetime(df_web['published_at'], errors='coerce')

    df_web = df_web.reindex(columns=df_api.columns)
    merged_df = pd.concat([df_api, df_web], ignore_index=True)

    # Нормализация area_name
    merged_df['area_name'] = merged_df['area_name'].replace({
        "Полная удаленка": "Удалённая работа",
        "Можно удалённо из РФ": "Удалённая работа"
    })

    # Конвертация валют
    from dagster_pipeline.utils.salary_converter import convert_salary_to_rur
    merged_df[['salary_from', 'salary_to', 'salary_currency']] = merged_df.apply(
        convert_salary_to_rur, axis=1
    )

    db_handler.insert_data(merged_df, "merged_vacancies")


def clean_data(db_handler):
    df = db_handler.read_sql("SELECT * FROM merged_vacancies")

    db_handler.insert_data(df, "cleaned_vacancies")