import sys
sys.path.append("C:/Users/Gleb Onore/Desktop/data_for_ml/dagster_pipeline")

from dagster_pipeline.database.sqlite_handler import SQLiteHandler
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

def engineer_features(db_handler):
    df = db_handler.read_sql("SELECT * FROM merged_vacancies")

    # Заполнение salary_to при наличии только salary_from
    condition = (df['salary_from'].notna()) & (df['salary_to'].isna())
    df.loc[condition, 'salary_to'] = df.loc[condition, 'salary_from']

    # Классификация качества зарплатных данных
    df['salary_data_quality'] = np.where(
        df['salary_from'].notna() & df['salary_to'].notna(), 'full',
        np.where(df['salary_from'].notna(), 'only_from', 'estimated')
    )

    # Кодировка опыта
    exp_map = {
        'Нет опыта': 0,
        'От 1 года до 3 лет': 1,
        'От 3 до 6 лет': 2,
        'Более 6 лет': 3
    }
    df['experience_encoded'] = df['experience'].map(exp_map)

    # One-hot для графика работы
    schedule_dummies = pd.get_dummies(df['schedule'], prefix='schedule')
    df = pd.concat([df, schedule_dummies], axis=1)

    # Импутация KNN
    columns_for_imputation = ['salary_from', 'salary_to', 'experience_encoded']
    imputer = KNNImputer(n_neighbors=10)
    df[columns_for_imputation] = imputer.fit_transform(df[columns_for_imputation])

    # Обратное преобразование опыта
    inv_exp_map = {v: k for k, v in exp_map.items()}
    df['experience'] = df['experience_encoded'].round().astype(int).map(inv_exp_map)

    # Удаление вспомогательных столбцов
    columns_to_drop = [
        'salary_data_quality',
        'experience_encoded',
        'schedule_Гибкий график',
        'schedule_Полный день',
        'schedule_Сменный график',
        'schedule_Удаленная работа'
    ]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    db_handler.insert_data(df, "cleaned_vacancies")