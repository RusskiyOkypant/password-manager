import tkinter as tk
from tkinter import ttk
import os
import sys
import time
from datetime import datetime
from core.password_manager import PasswordManager
from gui.tkinter.screens import CreateVaultScreen, UnlockScreen, MainScreen
from gui.tkinter.widgets import NotificationFrame
from gui.tkinter.utils import center_window
from dotenv import load_dotenv
from pathlib import Path

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

class TkinterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 1.0)
        self.root.title("Менеджер паролей")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Загрузка токена
        self.TOKEN = os.getenv('YANDEX_TOKEN')
        self.manager = PasswordManager(self.TOKEN)

        # Таймер автоблокировки
        self.lock_timeout = 300
        self._lock_check_id = None

        # ---- Уведомления ----
        self.notification = NotificationFrame(self.root)

        # ---- Основной контейнер для экранов ----
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # ---- Текущий экран ----
        self.current_screen = None

        # Центрируем окно
        center_window(self.root)

        # Применяем тему (до создания экранов)
        self.apply_theme(self.is_dark_theme())

        # Запускаем UI
        self.setup_ui()

        # Запускаем проверку автоблокировки
        self.start_lock_check()

        # ---- Горячие клавиши ----
        self.root.bind('<Control-f>', self.focus_search)
        self.root.bind('<Control-n>', self.new_service)
        self.root.bind('<Escape>', self.escape_pressed)

    def is_dark_theme(self):
        from utils.config import load_config
        config = load_config()
        return config.get('dark_theme', True)  # по умолчанию тёмная

    def apply_theme(self, dark):
        """Глобально применяет тему ко всем стилям и текущему экрану"""
        bg = '#2d2d2d' if dark else '#f0f0f0'
        fg = '#ffffff' if dark else '#000000'
        select_bg = '#3d3d3d' if dark else '#e0e0e0'

        self.root.configure(bg=bg)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TFrame', background=bg)
        style.configure('TButton', background=bg, foreground=fg)
        style.configure('TEntry', fieldbackground=bg, foreground=fg)
        style.map('TEntry', fieldbackground=[('readonly', bg)])
        style.configure('Treeview', background=bg, foreground=fg, fieldbackground=bg)
        style.map('Treeview', background=[('selected', select_bg)])
        style.configure('Treeview.Heading', background=bg, foreground=fg)
        style.configure('Title.TLabel', background=bg, foreground=fg)
        style.configure('Detail.TLabel', background=bg, foreground=fg)

        # Применить тему к текущему экрану (если он имеет свой apply_theme)
        if self.current_screen and hasattr(self.current_screen, 'apply_theme'):
            self.current_screen.apply_theme(dark)

    def toggle_theme(self):
        """Переключает тему и сохраняет настройку"""
        from utils.config import load_config, save_config
        config = load_config()
        current = config.get('dark_theme', False)
        new_theme = not current
        config['dark_theme'] = new_theme
        save_config(config)
        self.apply_theme(new_theme)
        self.reload_current_screen()
        self.show_notification(f"Тема: {'Тёмная' if new_theme else 'Светлая'}", "green")

    def reload_current_screen(self):
        """Перезагружает текущий экран, сохраняя состояние"""
        if not self.current_screen:
            return
        screen_name = None
        if isinstance(self.current_screen, CreateVaultScreen):
            screen_name = 'create_vault'
        elif isinstance(self.current_screen, UnlockScreen):
            screen_name = 'unlock'
        elif isinstance(self.current_screen, MainScreen):
            screen_name = 'main'
        if screen_name:
            service = None
            if screen_name == 'main' and hasattr(self.current_screen, 'current_service'):
                service = self.current_screen.current_service
            self.show_screen(screen_name)
            if screen_name == 'main' and service:
                self.current_screen.current_service = service
                self.current_screen.refresh_services_list()
                self.current_screen.show_service_details_panel(service)

    def setup_ui(self):
        if not self.manager.initialize():
            self.show_screen("create_vault")
        else:
            self.show_screen("unlock")

    def show_screen(self, screen_name):
        """Переключает экраны"""
        for widget in self.main_container.winfo_children():
            widget.destroy()

        if screen_name == "create_vault":
            screen = CreateVaultScreen(self.main_container, self)
        elif screen_name == "unlock":
            screen = UnlockScreen(self.main_container, self)
        elif screen_name == "main":
            screen = MainScreen(self.main_container, self)
        else:
            return

        screen.pack(fill=tk.BOTH, expand=True)
        self.current_screen = screen

        # Применяем тему к новому экрану
        self.apply_theme(self.is_dark_theme())

        self.notification.hide()

    # ---------- Уведомления ----------
    def show_notification(self, text, color='green', duration=3000):
        bg_colors = {
            'green': '#4CAF50',
            'red': '#F44336',
            'orange': '#FF9800',
            'yellow': '#FFEB3B',
            'blue': '#2196F3'
        }
        bg = bg_colors.get(color, '#4CAF50')
        fg = 'white' if color in ('green', 'red', 'blue') else 'black'
        self.notification.show(text, bg, fg, duration)

    # ---------- Автоблокировка ----------
    def start_lock_check(self):
        self.check_lock()
        self._lock_check_id = self.root.after(10000, self.start_lock_check)

    def check_lock(self):
        if self.manager.master_password and self.manager.is_locked(self.lock_timeout):
            self.show_screen("unlock")
            self.show_notification("Хранилище заблокировано из-за бездействия", "orange")

    def reset_lock_timer(self):
        self.manager.update_activity()

    # ---------- Горячие клавиши ----------
    def focus_search(self, event=None):
        if isinstance(self.current_screen, MainScreen):
            self.current_screen.search_entry.focus_set()
            return "break"

    def new_service(self, event=None):
        if isinstance(self.current_screen, MainScreen):
            self.current_screen.show_add_service_panel()
            return "break"

    def escape_pressed(self, event=None):
        # Закрываем все Toplevel окна (настройки, история и т.д.)
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists():
                child.destroy()
                return "break"
        # Если на главном экране, снимаем выделение с сервиса
        if isinstance(self.current_screen, MainScreen):
            if self.current_screen.current_service:
                self.current_screen.current_service = None
                self.current_screen.show_no_service_selected()
                self.current_screen.tree.selection_remove(self.current_screen.tree.selection())
                return "break"

    # ---------- Конфликт синхронизации ----------
    def check_conflict(self):
        """Проверяет конфликт синхронизации и показывает диалог при необходимости"""
        if hasattr(self.manager, '_conflict') and self.manager._conflict:
            self.manager._conflict = False
            self.show_conflict_dialog()

    def show_conflict_dialog(self):
        """Показывает диалог разрешения конфликта"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Конфликт синхронизации")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        dark = self.is_dark_theme()
        dialog.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Конфликт синхронизации",
                  style='Title.TLabel').pack(pady=10)
        ttk.Label(frame, text="Облачная версия данных новее, но у вас есть локальные изменения.\n"
                               "Выберите, какую версию оставить:",
                  justify='center').pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)

        def choose_local():
            if self.manager.resolve_conflict('local'):
                self.show_notification("Выбрана локальная версия", "green")
                self.reload_current_screen()
            else:
                self.show_notification("Ошибка сохранения локальной версии", "red")
            dialog.destroy()

        def choose_remote():
            if self.manager.resolve_conflict('remote'):
                self.show_notification("Выбрана облачная версия", "green")
                self.reload_current_screen()
            else:
                self.show_notification("Ошибка загрузки облачной версии", "red")
            dialog.destroy()

        ttk.Button(btn_frame, text="📁 Локальная", command=choose_local).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="☁️ Облачная", command=choose_remote).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    # ---------- Обработка закрытия ----------
    def on_closing(self):
        if self._lock_check_id:
            self.root.after_cancel(self._lock_check_id)
        try:
            if self.manager.modified and self.manager.has_internet:
                if hasattr(self.manager, 'token_valid') and self.manager.token_valid:
                    if not self.manager.upload_if_modified():
                        self.show_notification(
                            "Не удалось синхронизировать изменения с Яндекс.Диском",
                            "orange"
                        )
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
        self.root.destroy()

    def run(self):
        self.root.mainloop()