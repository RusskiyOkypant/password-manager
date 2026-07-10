MIT License

Copyright (c) 2025 [Ваше имя]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

4.2. Обновлённый README.md

Вот хороший шаблон, который вы можете адаптировать:
markdown

# Менеджер паролей

🔒 Локальный менеджер паролей с шифрованием, синхронизацией через Яндекс.Диск, историей паролей, тёмной темой и резервным копированием.

## Возможности

- **Безопасное хранение**: пароли шифруются с помощью PBKDF2-HMAC-SHA256 (600 000 итераций) и Fernet (AES-128 + HMAC).
- **История паролей**: сохранение до 5 предыдущих версий пароля для каждого сервиса.
- **Отложенная замена**: генерация нового пароля без немедленной замены – только после успешной смены на сайте.
- **Синхронизация**: автоматическая синхронизация с Яндекс.Диском.
- **Двухфакторная аутентификация (TOTP)**: поддержка 2FA-кодов для сервисов.
- **Поиск и фильтрация**: быстрый поиск по названию, логину, URL или заметкам.
- **Резервное копирование**: автоматическое создание резервных копий при каждом изменении (хранятся последние 10).
- **Тёмная тема**: переключение между светлой и тёмной темой, настройка сохраняется.
- **Автоблокировка**: блокировка хранилища после 5 минут бездействия.
- **Экспорт/импорт**: экспорт данных в JSON/CSV и импорт из этих форматов.
- **Горячие клавиши**: Ctrl+F – поиск, Ctrl+N – новый сервис, Esc – закрыть окно/снять выделение.

## Установка и запуск

### Требования
- Python 3.8+
- Установите зависимости:

```bash
pip install -r requirements.txt
```
Настройка

    Создайте файл .env в корне проекта и добавьте ваш токен Яндекс.Диска:
    text

    YANDEX_TOKEN=ваш_токен

    Запустите приложение:

        Tkinter версия: python run_tkinter.py

        Kivy версия: python run_kivy.py

Первый запуск

При первом запуске будет предложено создать мастер-пароль. Он используется для шифрования всех данных. Не потеряйте его!
Структура проекта

    core/ – бизнес-логика (PasswordManager).

    gui/tkinter/ – десктопное приложение.

    gui/kivy/ – мобильное приложение.

    utils/ – утилиты (конфигурация).

    data/ – хранилище зашифрованных данных.

    backups/ – автоматические резервные копии.

Технологии

    Криптография: cryptography (PBKDF2, Fernet)

    GUI: Tkinter, Kivy

    Облачная синхронизация: Yandex.Disk API (yadisk)

    TOTP: pyotp

    Конфигурация: python-dotenv

Безопасность

    Мастер-пароль не хранится и не передаётся по сети.

    Данные шифруются локально перед синхронизацией.

    Все секреты хранятся в зашифрованном виде.

    Рекомендуется использовать сложный мастер-пароль (от 12 символов).

Планы по развитию

    Улучшение Kivy-версии до полноценного мобильного приложения.

    Поддержка дополнительных облачных сервисов (Google Drive, Dropbox).

    Импорт из других менеджеров паролей (Bitwarden, KeePass).

Автор

[Ваше имя или ник]
Лицензия

MIT

p.s.
нейросети рулят
