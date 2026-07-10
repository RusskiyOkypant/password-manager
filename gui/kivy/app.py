import os
import sys
from pathlib import Path
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
from core.password_manager import PasswordManager
from gui.kivy.screens import CreateVaultScreen, UnlockScreen, MainScreen
from gui.kivy.widgets import NotificationPopup
from dotenv import load_dotenv

# Определяем корневую папку (аналогично Tkinter)
def get_project_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / 'core').exists() or (parent / 'data').exists():
                return parent
        return current.parent

base_dir = get_project_root()
dotenv_path = base_dir / 'data' / '.env'
load_dotenv(dotenv_path)


class KivyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TOKEN = os.getenv('YANDEX_TOKEN')
        self.manager = PasswordManager(self.TOKEN)
        self.screen_manager = ScreenManager()
        self.lock_timeout = 300  # 5 минут
        self._lock_check_event = None
        self._dark_theme = True   # по умолчанию тёмная (можно загружать из конфига)

        # Устанавливаем тему по умолчанию (будет переопределена после загрузки конфига)
        self.apply_theme(self._dark_theme)

    def build(self):
        # Создаём экраны
        self.create_screen = CreateVaultScreen(name='create', app=self)
        self.unlock_screen = UnlockScreen(name='unlock', app=self)
        self.main_screen = MainScreen(name='main', app=self)

        self.screen_manager.add_widget(self.create_screen)
        self.screen_manager.add_widget(self.unlock_screen)
        self.screen_manager.add_widget(self.main_screen)

        # Определяем начальный экран
        if not self.manager.initialize():
            self.screen_manager.current = 'create'
        else:
            self.screen_manager.current = 'unlock'

        # Запускаем проверку автоблокировки
        self.start_lock_check()

        # Загружаем тему из конфига
        self.load_theme_from_config()

        return self.screen_manager

    def load_theme_from_config(self):
        """Загружает настройку темы из config.json и применяет"""
        try:
            from utils.config import load_config
            config = load_config()
            dark = config.get('dark_theme', True)
            self._dark_theme = dark
            self.apply_theme(dark)
        except:
            pass

    def apply_theme(self, dark):
        """Применяет тёмную или светлую тему к приложению"""
        self._dark_theme = dark
        if dark:
            # Тёмная тема
            Window.clearcolor = (0.18, 0.18, 0.18, 1)  # тёмно-серый
            # Можно также менять цвета виджетов через KV-стили, но здесь просто меняем фон
        else:
            Window.clearcolor = (1, 1, 1, 1)  # белый

        # Если главный экран уже создан, передаём ему тему
        if hasattr(self, 'main_screen'):
            self.main_screen.apply_theme(dark)

    def toggle_theme(self):
        """Переключает тему и сохраняет настройку"""
        from utils.config import load_config, save_config
        config = load_config()
        current = config.get('dark_theme', True)
        new_theme = not current
        config['dark_theme'] = new_theme
        save_config(config)
        self.apply_theme(new_theme)
        self.show_notification(f"Тема: {'Тёмная' if new_theme else 'Светлая'}", 'green', 2)

    def show_notification(self, message, color='green', duration=2):
        popup = NotificationPopup(message=message, color=color, duration=duration)
        popup.open()

    def reset_lock_timer(self):
        if self.manager:
            self.manager.update_activity()

    def start_lock_check(self):
        self.check_lock()
        self._lock_check_event = Clock.schedule_interval(self.check_lock, 10)

    def check_lock(self, dt=None):
        if self.manager.master_password and self.manager.is_locked(self.lock_timeout):
            self.screen_manager.current = 'unlock'
            self.show_notification("Хранилище заблокировано из-за бездействия", "orange", 3)

    def on_stop(self):
        if self._lock_check_event:
            self._lock_check_event.cancel()
        try:
            if self.manager.modified and self.manager.has_internet:
                if hasattr(self.manager, 'token_valid') and self.manager.token_valid:
                    if not self.manager.upload_if_modified():
                        print("Предупреждение: Не удалось синхронизировать изменения")
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")