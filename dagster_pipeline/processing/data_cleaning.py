import sys
sys.path.append("C:/Users/Gleb Onore/Desktop/data_for_ml/dagster_pipeline")

import pandas as pd
from dagster_pipeline.utils.salary_converter import convert_salary_to_rur


def merge_datasets(db_handler):
    merged_df = db_handler.read_sql("SELECT * FROM vacancies")

    merged_df['area_name'] = merged_df['area_name'].replace({
        "Полная удаленка": "Удалённая работа",
        "Можно удалённо из РФ": "Удалённая работа"
    })


    merged_df[['salary_from', 'salary_to', 'salary_currency']] = merged_df.apply(
        convert_salary_to_rur, axis=1
    )

    db_handler.insert_data(merged_df, "merged_vacancies")


def clean_data(db_handler):
    import numpy as np
    from sklearn.impute import KNNImputer
    from sklearn.model_selection import KFold

    df = db_handler.read_sql("SELECT * FROM 'merged_vacancies'")

    condition = (df['salary_from'].notna()) & (df['salary_to'].isna())
    df.loc[condition, 'salary_to'] = df.loc[condition, 'salary_from']

    exp_map = {
        'Нет опыта': 0,
        'От 1 года до 3 лет': 1,
        'От 3 до 6 лет': 2,
        'Более 6 лет': 3
    }
    df['experience_encoded'] = df['experience'].map(exp_map)

    impute_cols = ['salary_from', 'salary_to', 'experience_encoded']
    df_impute = df[impute_cols]
    imputer = KNNImputer(n_neighbors=10)
    df_imputed = imputer.fit_transform(df_impute)
    df[impute_cols] = df_imputed

    inv_exp_map = {v: k for k, v in exp_map.items()}
    df['experience'] = df['experience_encoded'].round().astype(int).map(inv_exp_map)

    # Очистка и salary_mean
    df['salary_from'] = pd.to_numeric(df['salary_from'], errors='coerce')
    df['salary_to'] = pd.to_numeric(df['salary_to'], errors='coerce')
    df.dropna(subset=['salary_from', 'salary_to'], inplace=True)
    df['salary_mean'] = (df['salary_from'] + df['salary_to']) / 2

    # One-hot и Label Encoding
    df = pd.get_dummies(df, columns=['salary_currency', 'schedule', 'employment'],
                        prefix=['curr', 'sched', 'employ'])

    experience_mapping = {'Нет опыта': 0, 'От 1 года до 3 лет': 1, 'От 3 до 6 лет': 2}
    df['experience_level'] = df['experience'].map(experience_mapping).fillna(-1)

    # Target Encoding
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

    # Smoothed Frequency Encoding
    def create_smoothed_encoding(series, target_series, weight=10):
        global_mean = target_series.mean()
        group_means = target_series.groupby(series).mean()
        group_counts = series.value_counts()
        smoothed = (group_counts * group_means + weight * global_mean) / (group_counts + weight)
        return series.map(smoothed).fillna(global_mean)

    df['employer_encoded'] = create_smoothed_encoding(df['employer_name'], df['salary_mean'])

    # Финальная очистка
    columns_to_drop = [
        'name', 'area_name', 'employer_name', 'experience',
        'alternate_url', 'published_at', 'salary_from', 'salary_to',
        'experience_encoded'
    ]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    db_handler.insert_data(df, "cleaned_vacancies")
