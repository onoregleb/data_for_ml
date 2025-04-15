import time
import pandas as pd
import requests


def fetch_vacancies(params, max_pages=20, per_page=100):
    """
    Собирает вакансии с HH.ru по заданным параметрам.
    """
    url = "https://api.hh.ru/vacancies"
    headers = {"User-Agent": "JobAnalysis/1.0 (example@gmail.com)"}
    all_vacancies = []

    print(f"Запуск сбора вакансий с параметрами: {params}")

    for page in range(max_pages):
        params.update({"page": page, "per_page": per_page})
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            page_data = response.json()

            if "items" in page_data and page_data["items"]:
                all_vacancies.extend(page_data["items"])

            # Логгирование каждых 10 страниц
            if (page + 1) % 10 == 0:
                print(f"Обработано {page + 1} страниц.")

            # Если на странице нет вакансий, завершаем сбор
            if not page_data["items"]:
                print(f"Страница {page} не содержит вакансий. Завершаем сбор.")
                break

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении данных с API на странице {page}: {e}")
            break

        # Пауза между запросами, чтобы избежать превышения лимитов API
        time.sleep(1)

    print(f"Всего вакансий собрано: {len(all_vacancies)}.")
    return all_vacancies

def hh_scrape(db_handler):
    params = {
        "text": "Data Scientist OR Machine Learning OR Аналитик данных OR Искусственный интеллект OR Data Engineer OR ML",
        "area": 113,  # Россия
        "specialization": 1,  # IT
    }

    raw_api_data = fetch_vacancies(params)

    columns = [
        "id", "name", "area_name", "salary_from", "salary_to", "salary_currency",
        "published_at", "employer_name", "alternate_url", "schedule", "employment", "experience"
    ]

    df = pd.DataFrame(columns=columns)
    for i, vacancy in enumerate(raw_api_data):
        salary = vacancy.get("salary", {}) or {}
        employer = vacancy.get("employer", {}) or {}
        snippet = vacancy.get("snippet", {}) or {}

        data = {
            "id": vacancy.get("id"),
            "name": vacancy.get("name"),
            "area_name": vacancy.get("area", {}).get("name"),
            "salary_from": salary.get("from"),
            "salary_to": salary.get("to"),
            "salary_currency": salary.get("currency"),
            "published_at": vacancy.get("published_at"),
            "employer_name": employer.get("name"),
            "alternate_url": vacancy.get("alternate_url"),
            "schedule": vacancy.get("schedule", {}).get("name"),
            "employment": vacancy.get("employment", {}).get("name"),
            "experience": vacancy.get("experience", {}).get("name"),
        }

        df.loc[i] = data

    db_handler.insert_data(df, "vacancies")