import pandas as pd
import numpy as np
from sklearn.model_selection import KFold


def engineer_features(db_handler):
    df = db_handler.read_sql("SELECT * FROM merged_vacancies")

    df['salary_from'] = pd.to_numeric(df['salary_from'], errors='coerce')
    df['salary_to'] = pd.to_numeric(df['salary_to'], errors='coerce')

    df['salary_to'] = df['salary_to'].fillna(df['salary_from'])
    df.dropna(subset=['salary_from', 'salary_to'], inplace=True)

    df['salary_mean'] = (df['salary_from'] + df['salary_to']) / 2

    df['schedule'] = df['schedule'].str.replace(' ', '_').str.strip()
    df['employment'] = df['employment'].str.replace(' ', '_').str.strip()
    df['salary_currency'] = df['salary_currency'].str.replace(' ', '_').str.strip()

    categorical_features = ['salary_currency', 'schedule', 'employment']
    df = pd.get_dummies(df,
                        columns=categorical_features,
                        prefix=['curr', 'sched', 'employ'])

    exp_map = {'Нет_опыта': 0, 'От_1_года_до_3_лет': 1, 'От_3_до_6_лет': 2}
    df['experience'] = df['experience'].str.replace(' ', '_').str.strip()
    df['experience_level'] = df['experience'].map(exp_map).fillna(-1).astype(int)

    def create_target_encoding(series, target_series):
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        encoded = pd.Series(np.zeros(len(series)), index=series.index)
        global_mean = target_series.mean()

        for train_idx, val_idx in kf.split(series):
            train_series = series.iloc[train_idx]
            train_target = target_series.iloc[train_idx]
            group_means = train_target.groupby(train_series).mean()
            encoded.iloc[val_idx] = series.iloc[val_idx].map(group_means).fillna(global_mean)

        return encoded.fillna(global_mean)

    df['job_title_encoded'] = create_target_encoding(df['name'], df['salary_mean'])
    df['region_encoded'] = create_target_encoding(df['area_name'], df['salary_mean'])

    def create_smoothed_encoding(series, target_series, weight=10):
        global_mean = target_series.mean()
        group_means = target_series.groupby(series).mean()
        group_counts = series.value_counts()
        smoothed = (group_counts * group_means + weight * global_mean) / (group_counts + weight)
        return series.map(smoothed).fillna(global_mean)

    df['employer_encoded'] = create_smoothed_encoding(df['employer_name'], df['salary_mean'])

    final_columns = [
        'id', 'salary_mean',
        'curr_RUR',
        'sched_Гибкий_график', 'sched_Полный_день',
        'sched_Сменный_график', 'sched_Удаленная_работа',
        'sched_Вахтовый_метод',
        'employ_Полная_занятость', 'employ_Проектная_работа',
        'employ_Стажировка', 'employ_Частичная_занятость',
        'experience_level', 'job_title_encoded',
        'region_encoded', 'employer_encoded'
    ]

    for col in final_columns:
        if col not in df.columns:
            df[col] = 0

    # Приведение типов
    final_cols_to_int = [col for col in final_columns if col.startswith('curr_') or col.startswith('sched_') or col.startswith('employ_')]
    df[final_cols_to_int] = df[final_cols_to_int].astype(int)

    # Сохранение
    db_handler.insert_data(df[final_columns], "features_for_model")