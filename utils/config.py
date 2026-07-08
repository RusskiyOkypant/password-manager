import json
import os

CONFIG_FILE = 'data/config.json'

DEFAULT_CONFIG = {
    'password_length': 20,
    'use_symbols': True,
    'use_digits': True,
    'use_uppercase': True,
    'use_lowercase': True,
    'dark_theme': True   # <-- изменили на True
}


def load_config():
    """Загружает конфигурацию из файла"""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Сохраняет конфигурацию в файл"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config_value(key, default=None):
    """Возвращает значение из конфигурации"""
    config = load_config()
    return config.get(key, default)