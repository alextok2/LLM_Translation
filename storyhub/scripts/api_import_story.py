import requests
from urllib.parse import urljoin


BASE = "http://127.0.0.1:8000"  # поправь, если нужен другой хост/порт
LOGIN_URL = f"{BASE}/accounts/login/"
IMPORT_URL = f"{BASE}/api/stories/import/"
CREATE_URL = f"{BASE}/api/stories/"  # на случай пошагового пути
PARSE_URL_TPL = f"{BASE}/api/stories/{{id}}/parse/"

def login(session: requests.Session, username: str, password: str):
    # 1) получаем csrftoken
    r = session.get(LOGIN_URL)
    r.raise_for_status()
    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        raise RuntimeError("Не получен csrftoken; проверь CSRF middleware и LOGIN_URL")

    # 2) логинимся (POST + csrfmiddlewaretoken)
    payload = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrftoken,
        "next": "/",  # можно поменять
    }
    headers = {"Referer": LOGIN_URL}
    r = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=False)
    # ожидаем редирект 302 при успешном логине
    if r.status_code not in (302, 301):
        raise RuntimeError(f"Логин не удался: HTTP {r.status_code}")
    if "sessionid" not in session.cookies:
        raise RuntimeError("Нет sessionid после логина — проверь учётные данные/настройки")
    return True

def post_json(session, path, data):
    csrftoken = session.cookies.get("csrftoken", "")
    headers = {"Content-Type": "application/json", "X-CSRFToken": csrftoken, "Referer": BASE}
    
    # --- FIX IS HERE ---
    full_url = urljoin(BASE, path) 
    
    r = session.post(full_url, json=data, headers=headers)
    if r.status_code >= 400:
        print("HTTP", r.status_code, "→", full_url)
        # покажем первые 2000 символов HTML-страницы с трейсбеком
        print(r.text[:2000])
        r.raise_for_status()
    return r.json()


def create_and_parse_one_chapter(username: str, password: str):
    s = requests.Session()
    login(s, username, password)

    # “Импорт в одном запросе”: создание + парсинг одной главы (с машинным переводом)
    data = {
        "title": "История одним махом",
        "description": "Демонстрация импорта одной главой",
        "original_language": 1,  # ID языка из БД (создай в /admin)
        "target_language": 2,
        "tags": [],

        "original_text": "Оригинал абзац 1\n\nОригинал абзац 2",
        "machine_text": "MT абзац 1\n\nMT абзац 2"  # убери/оставь пустым для “без перевода”
    }
    resp = post_json(s, IMPORT_URL, data)
    print("Создано+распарсено:", resp)

def create_and_parse_chapters(username: str, password: str):
    s = requests.Session()
    login(s, username, password)

    # Импорт с главами; у второй главы machine_text отсутствует (это “без перевода”)
    data = {
        "title": "Роман с главами",
        "description": "Демо история с 2 главами",
        "original_language": 1,
        "target_language": 2,
        "tags": [],

        "chapters": [
            {
                "title": "Глава 1. Начало",
                "original_text": "Ориг-1а\n\nОриг-1б",
                "machine_text": "MT-1a\n\nMT-1b"
            },
            {
                "title": "Глава 2. Продолжение",
                "original_text": "Ориг-2а\n\nОриг-2б"
                # machine_text опущен — без перевода
            }
        ]
    }
    resp = post_json(s, IMPORT_URL, data)
    print("Создано+распарсено (главы):", resp)

def create_then_parse_step_by_step(username: str, password: str):
    s = requests.Session()
    login(s, username, password)

    # Шаг 1. Создаём историю (метаданные)
    csrftoken = s.cookies.get("csrftoken")
    headers = {"X-CSRFToken": csrftoken or "", "Referer": BASE}
    story_data = {
        "title": "Пошаговая история",
        "description": "Сначала создать, потом парсить",
        "original_language": 1,
        "target_language": 2,
        "tags": []
    }
    r = s.post(CREATE_URL, json=story_data, headers=headers)
    r.raise_for_status()
    story = r.json()
    story_id = story["id"]

    # Шаг 2. Парсим (без перевода)
    parse_data = {
        "original_text": "Ориг 1\n\nОриг 2"
        # machine_text не передаём — без перевода
    }
    r = s.post(PARSE_URL_TPL.format(id=story_id), json=parse_data, headers=headers)
    r.raise_for_status()
    print("Пошаговый импорт:", r.json())

if __name__ == "__main__":
    # Подставь логин/пароль админа
    USER = "newStories"
    PASS = "avWwmzC5qzEPHZamwc"

    create_and_parse_one_chapter(USER, PASS)
    create_and_parse_chapters(USER, PASS)
    create_then_parse_step_by_step(USER, PASS)