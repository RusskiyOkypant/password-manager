# Инструкция по установке

## Требования

- Python 3.7 или выше
- pip

## Шаги

1. Скачайте проект.
2. Перейдите в папку проекта.
3. Создайте виртуальное окружение (рекомендуется):

python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

4. Установите зависимости:

pip install -r requirements.txt

5. Получите токен Яндекс.Диска:
- Перейдите в https://oauth.yandex.ru/
- Создайте приложение и получите OAuth-токен.
6. Создайте папку `data/` и в ней файл `.env`:

YANDEX_TOKEN=ваш_токен


## Запуск

- Tkinter: `python run_tkinter.py`
- Kivy: `python run_kivy.py`