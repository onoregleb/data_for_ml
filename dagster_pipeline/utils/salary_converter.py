import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_exchange_rate(date, currency_code):
    """
    Получает курс валюты по дате в формате dd/mm/yyyy.
    Возвращает курс к рублю. Если валюта — RUR или курс не найден, возвращает 1.
    """
    if currency_code == "RUR" or pd.isna(currency_code):
        return 1

    try:
        url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            for valute in soup.find_all("Valute"):
                if valute.CharCode.text == currency_code:
                    return float(valute.Value.text.replace(",", ".")) / int(valute.Nominal.text)
    except Exception as e:
        print(f"[WARNING] Ошибка получения курса валюты для {currency_code} на {date}: {e}")
    return 1


def convert_salary_to_rur(row):
    """
    Конвертирует зарплату в рубли на основе курса ЦБ РФ.
    """
    if isinstance(row['published_at'], str):
        row['published_at'] = pd.to_datetime(row['published_at'], errors='coerce')

    date_str = row['published_at'].strftime("%d/%m/%Y") if pd.notnull(row['published_at']) else None
    currency = row['salary_currency']

    exchange_rate = get_exchange_rate(date_str, currency) if date_str else 1

    salary_from_rur = row['salary_from'] * exchange_rate if pd.notnull(row['salary_from']) else None
    salary_to_rur = row['salary_to'] * exchange_rate if pd.notnull(row['salary_to']) else None

    return pd.Series([salary_from_rur, salary_to_rur, "RUR"])
