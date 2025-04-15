import re
import time
import pandas as pd
from requests_html import HTMLSession
from datetime import datetime, timedelta
from natasha import Segmenter, NewsMorphTagger, NewsEmbedding, Doc, MorphVocab

session = HTMLSession()
emb = NewsEmbedding()
segmenter = Segmenter()
morph_tagger = NewsMorphTagger(emb)
morph_vocab = MorphVocab()

BASE_URL = "https://getmatch.ru"
MONTHS = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12
}


def normalize_month(month: str) -> str:
    doc = Doc(month)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)

    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        return token.lemma.lower()

    return month.lower()


def parse_published_at(published_at: str) -> str:
    if not published_at:
        return None

    try:
        published_at = published_at.lower()

        if published_at == "сегодня":
            return datetime.today().strftime('%Y-%m-%d')

        yesterday_pattern = re.compile(r'вчера')
        if yesterday_pattern.search(published_at):
            return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

        parts = published_at.split()
        if len(parts) >= 3:
            day = int(parts[0])
            month = normalize_month(parts[1])
            year = int(parts[2])

            month_num = MONTHS.get(month)
            if month_num:
                return datetime(year, month_num, day).strftime('%Y-%m-%d')

    except Exception as e:
        print(f"Ошибка при парсинге даты: {published_at} | {e}")

    return None


def parse_salary(salary_str: str):
    """Парсинг зарплаты"""
    if not salary_str:
        return None, None, None

    original_salary_str = salary_str

    salary_str = salary_str.replace('\u200d', '').replace('—', '-').replace('–', '-')
    salary_str = salary_str.replace(' ', '')  # Убираем пробелы

    salary_from, salary_to, currency = None, None, 'RUR'  # По умолчанию рублики

    try:
        # Определяем валюту на основе наличия символов
        if '₽' in original_salary_str:
            currency = 'RUR'
        elif '$' in original_salary_str:
            currency = 'USD'
        elif '€' in original_salary_str:
            currency = 'EUR'

        salary_str = salary_str.replace('₽', '').replace('$', '').replace('€', '')

        # Парсим диапазон зарплаты
        if 'от' in salary_str:
            salary_from = int(salary_str.split('от')[1].split('/')[0])
        elif 'до' in salary_str:
            salary_to = int(salary_str.split('до')[1].split('/')[0])
        elif '-' in salary_str:
            parts = salary_str.split('-')
            if len(parts) == 2:
                salary_from, salary_to = map(int, parts)

    except ValueError:
        pass

    return salary_from, salary_to, currency


def clean_responsibility(text: str) -> str:
    """Удаляет 'Что делать:' в начале текста, если оно есть"""
    if text and text.startswith("Что делать:"):
        return text[len("Что делать:"):].strip()
    return text.strip() if text else None

def clean_area_name(text: str) -> str:
    """Очищает название города, удаляя символ 📍 и всё, что в скобках"""
    if not text:
        return None

    text = text.replace("📍", "").strip()
    text = re.sub(r"\s*\(.*?\)", "", text)
    return text.strip()

def normalize_experience(experience: str) -> str:
    """Нормализует опыт работы в стандартные диапазоны"""
    if not experience:
        return "Нет опыта"

    experience = experience.lower()

    if "3+" in experience or "от 3" in experience:
        return "От 3 до 6 лет"
    elif "5+" in experience or "от 5" in experience:
        return "Более 6 лет"
    elif "1" in experience or "год" in experience:
        return "От 1 года до 3 лет"
    elif "нет" in experience or "не требуется" in experience:
        return "Нет опыта"
    else:
        return "Не указано"


def parse_experience(vacancy_url: str) -> str:
    """Парсинг опыта работы на странице вакансии"""
    try:
        response = session.get(vacancy_url)
        if response.status_code != 200:
            print(f"Ошибка {response.status_code}: не удалось загрузить страницу {vacancy_url}")
            return None

        # Ищем элемент с опытом работы
        experience_element = response.html.find(
            'body > app-root > app-container > div > app-vacancy > div > section.container.b-vacancy-v2 > div > div.col-md-8.col-sm-12 > div.section.b-specs > div:nth-child(3)',
            first=True
        )
        if experience_element:
            experience_text = experience_element.text.strip()
            # Оставляем только часть после \n
            if '\n' in experience_text:
                experience_text = experience_text.split('\n')[-1].strip()
            return normalize_experience(experience_text)
        else:
            return None
    except Exception as e:
        print(f"Ошибка при парсинге опыта работы: {e}")
        return None


def parse_vacancy_card(vacancy, vacancy_id):
    """Парсинг карточки вакансии"""
    try:
        title_element = vacancy.find('div.b-vacancy-card-title h3 a', first=True)
        salary_element = vacancy.find('div.b-vacancy-card-subtitle__salary span', first=True)
        company_element = vacancy.find('div.b-vacancy-card-title h4 a', first=True)
        published_at_element = vacancy.find('.b-vacancy-card-header__publish-date p', first=True)
        if published_at_element and published_at_element.text.strip():
            published_at = published_at_element.text.strip()
        else:
            published_at = None
        responsibility_element = vacancy.find('div.b-vacancy-card-description > p:nth-child(1)', first=True)
        area_element = vacancy.find('div.b-vacancy-card-subtitle app-vacancy-locations > div > span', first=True)

        salary_from, salary_to, salary_currency = parse_salary(salary_element.text if salary_element else None)

        if salary_from is None and salary_to is None:
            return None

        area_name = clean_area_name(area_element.text.strip()) if area_element else None

        if area_name and "можно удалённо из рф" in area_name.lower():
            schedule = "Удаленная работа"
        else:
            schedule = "Полный день"

        alternate_url = title_element.attrs.get('href') if title_element else None
        if alternate_url and alternate_url.startswith('/'):
            alternate_url = BASE_URL + alternate_url

        # Парсим опыт работы
        experience = parse_experience(alternate_url)

        return {
            'id': vacancy_id,
            'name': title_element.text if title_element else None,
            'alternate_url': alternate_url,
            'salary_from': salary_from,
            'salary_to': salary_to,
            'salary_currency': salary_currency,
            'employer_name': company_element.text if company_element else None,
            'published_at': parse_published_at(published_at_element.text.strip() if published_at_element else None),
            'snippet_responsibility': clean_responsibility(responsibility_element.text.strip()) if responsibility_element else None,
            'area_name': area_name,
            'employment': "Полная занятость",
            'schedule': schedule,
            'experience': experience
        }
    except Exception as e:
        print(f"Ошибка при парсинге карточки вакансии: {e}")
        return None


def scrape_page(url, start_id):
    """Сбор данных со страницы"""
    response = session.get(url)

    if response.status_code != 200:
        print(f"Ошибка {response.status_code}: не удалось загрузить страницу {url}")
        return [], start_id

    vacancies = response.html.find('app-vacancy-card')
    parsed_vacancies = []
    for vacancy in vacancies:
        parsed_vacancy = parse_vacancy_card(vacancy, start_id)
        if parsed_vacancy:
            parsed_vacancies.append(parsed_vacancy)
            start_id += 1  # Увеличиваем ID для следующей вакансии

    return parsed_vacancies, start_id


def getmatch_scrape(db_handler):
    base_url = "https://getmatch.ru/vacancies/data-science?p={page}&sa=150000&pa=all"
    all_data = []
    max_pages = 30
    start_id = 1

    for page in range(1, max_pages + 1):
        if (page + 1) % 10 == 0:
            print(f"Обработано {page + 1} страниц.")

        data, start_id = scrape_page(base_url.format(page=page), start_id)
        if not data:
            print("Нет больше данных. Завершение парсинга.")
            break

        all_data.extend(data)
        time.sleep(2)

    if all_data:
        df = pd.DataFrame(all_data)
        db_handler.insert_data(df, "vacancies")
        print("Данные сохранены в БД")
    else:
        print("Нет данных для сохранения.")