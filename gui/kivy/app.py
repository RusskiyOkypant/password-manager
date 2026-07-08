import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
from core.password_manager import PasswordManager
from gui.kivy.screens import CreateVaultScreen, UnlockScreen, MainScreen
from gui.kivy.widgets import NotificationPopup
from dotenv import load_dotenv

load_dotenv()


class KivyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TOKEN = os.getenv('YANDEX_TOKEN')
        self.manager = PasswordManager(self.TOKEN)
        self.screen_manager = ScreenManager()
        self.lock_timeout = 300  # 5 минут
        self._lock_check_event = None

        # Устанавливаем светлую тему
        Window.clearcolor = (1, 1, 1, 1)

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

        return self.screen_manager

    def show_notification(self, message, color='green', duration=2):
        """Показывает всплывающее уведомление"""
        popup = NotificationPopup(message=message, color=color, duration=duration)
        popup.open()

    def reset_lock_timer(self):
        """Сбрасывает таймер бездействия"""
        if self.manager:
            self.manager.update_activity()

    def start_lock_check(self):
        """Периодическая проверка автоблокировки (каждые 10 секунд)"""
        self.check_lock()
        self._lock_check_event = Clock.schedule_interval(self.check_lock, 10)

    def check_lock(self, dt=None):
        """Проверяет, не истекло ли время бездействия"""
        if self.manager.master_password and self.manager.is_locked(self.lock_timeout):
            self.screen_manager.current = 'unlock'
            self.show_notification("Хранилище заблокировано из-за бездействия", "orange", 3)

    def on_stop(self):
        """Обработчик закрытия приложения"""
        if self._lock_check_event:
            self._lock_check_event.cancel()
        try:
            if self.manager.modified and self.manager.has_internet:
                if hasattr(self.manager, 'token_valid') and self.manager.token_valid:
                    if not self.manager.upload_if_modified():
                        print("Предупреждение: Не удалось синхронизировать изменения")
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")