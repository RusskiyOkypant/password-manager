import tkinter as tk
import os
from tkinter import ttk
from datetime import datetime
import webbrowser
from core.password_manager import PasswordManager
from gui.tkinter.widgets import GreenButton, BlueButton, RedButton, GrayButton
from gui.tkinter.utils import get_treeview_selected


class CreateVaultScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        ttk.Label(self, text="Создание нового хранилища", style='Title.TLabel').pack(pady=20)

        ttk.Label(self, text="Придумайте мастер-пароль:").pack(pady=5)
        self.master_password_entry = ttk.Entry(self, show="*", width=30)
        self.master_password_entry.pack(pady=5)

        ttk.Label(self, text="Подтвердите мастер-пароль:").pack(pady=5)
        self.confirm_password_entry = ttk.Entry(self, show="*", width=30)
        self.confirm_password_entry.pack(pady=5)

        ttk.Button(self, text="Создать хранилище", command=self.create_vault).pack(pady=30)

    def create_vault(self):
        password = self.master_password_entry.get()
        confirm = self.confirm_password_entry.get()
        if not password or not confirm:
            self.app.show_notification("Пароли не могут быть пустыми", "red")
            return
        if password != confirm:
            self.app.show_notification("Пароли не совпадают", "red")
            return
        if self.app.manager.create_vault(password, confirm):
            self.app.show_notification("Хранилище успешно создано!", "green")
            self.app.show_screen("main")
        else:
            self.app.show_notification("Не удалось создать хранилище", "red")

    def apply_theme(self, dark):
        bg = '#2d2d2d' if dark else '#f0f0f0'
        self.configure(bg=bg)


class UnlockScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        ttk.Label(self, text="Разблокировка хранилища", style='Title.TLabel').pack(pady=20)

        ttk.Label(self, text="Введите мастер-пароль:").pack(pady=5)
        self.password_entry = ttk.Entry(self, show="*", width=30)
        self.password_entry.pack(pady=5)

        ttk.Button(self, text="Разблокировать", command=self.unlock_vault).pack(pady=30)

    def unlock_vault(self):
        password = self.password_entry.get()
        if not password:
            self.app.show_notification("Введите пароль", "red")
            return
        if self.app.manager.unlock_vault(password):
            self.app.check_conflict()   # Проверка конфликта синхронизации
            self.app.show_screen("main")
        else:
            self.app.show_notification("Неверный пароль", "red")

    def apply_theme(self, dark):
        bg = '#2d2d2d' if dark else '#f0f0f0'
        self.configure(bg=bg)


class MainScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_service = None
        self.manager = app.manager

        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_paned)

        top_left_frame = ttk.Frame(left_frame)
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        top_left_frame.pack(fill=tk.X, pady=(0, 10))
        add_button = ttk.Button(
            top_left_frame,
            text="+ Добавить новый сервис",
            command=self.show_add_service_panel,
            style='Add.TButton'
        )
        add_button.pack(side=tk.RIGHT, padx=5)

        self.tree = ttk.Treeview(left_frame, columns=('service', 'created'),
                                 show='headings', height=25)
        self.tree.heading('service', text='Сервис')
        self.tree.heading('created', text='Дата создания')
        self.tree.column('service', width=150, minwidth=100, anchor=tk.W, stretch=True)
        self.tree.column('created', width=100, minwidth=80, anchor=tk.W, stretch=False)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_service_select)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Контекстное меню (правый клик)

        self.right_frame = ttk.Frame(main_paned, relief=tk.RIDGE, borderwidth=2)
        self.right_content = ttk.Frame(self.right_frame)
        self.right_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        main_paned.add(left_frame, weight=6)
        main_paned.add(self.right_frame, weight=2)

        self.show_no_service_selected()
        self.refresh_services_list()

        self.bind_all("<Button-1>", lambda e: self.app.reset_lock_timer())

    def on_search(self, event=None):
        query = self.search_entry.get().strip()
        self.refresh_services_list(query)

    def clear_right_panel(self):
        for widget in self.right_content.winfo_children():
            widget.destroy()

    def show_no_service_selected(self):
        self.clear_right_panel()
        info_frame = ttk.Frame(self.right_content)
        info_frame.pack(expand=True)

        ttk.Label(info_frame, text="Менеджер паролей",
                  style='Title.TLabel').pack(pady=(20, 10))
        ttk.Label(info_frame, text="Выберите сервис для просмотра пароля",
                  font=('Arial', 11)).pack(pady=5)
        ttk.Label(info_frame, text="или нажмите кнопку \"+ Добавить новый сервис\"",
                  font=('Arial', 11)).pack(pady=5)

        sync_frame = ttk.Frame(info_frame)
        sync_frame.pack(pady=(30, 0))
        if self.manager.has_internet:
            if hasattr(self.manager, 'token_valid') and self.manager.token_valid:
                sync_text = "✓ Синхронизация с Яндекс.Диском активна"
                sync_color = "green"
            else:
                sync_text = "⚠ Синхронизация недоступна (неверный токен)"
                sync_color = "orange"
        else:
            sync_text = "⚠ Синхронизация временно недоступна (нет интернета)"
            sync_color = "orange"
        ttk.Label(sync_frame, text=sync_text,
                  font=('Arial', 9), foreground=sync_color).pack()

    def refresh_services_list(self, query=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if query:
            services = self.manager.search_services(query)
        else:
            services = self.manager.list_services()

        for service in services:
            service_data = self.manager.get_service(service)
            created_at = datetime.fromisoformat(service_data['created_at'])
            formatted_date = created_at.strftime("%d.%m.%Y")
            status_text, status_color = self.manager.get_password_age_status(service_data['created_at'])
            item = self.tree.insert('', tk.END, values=(service, formatted_date))
            self.tree.item(item, tags=(status_color,))

        # Убраны явные tag_configure – они устанавливаются в apply_theme
        self.auto_adjust_columns()

        if self.current_service:
            if self.current_service in services:
                self.show_service_details_panel(self.current_service)
            else:
                self.current_service = None
                self.show_no_service_selected()

    def auto_adjust_columns(self):
        items = self.tree.get_children()
        if not items:
            return
        max_service_width = 0
        max_date_width = 0
        for item in items:
            service_name = self.tree.item(item, 'values')[0]
            date_str = self.tree.item(item, 'values')[1]
            service_width = len(service_name) * 1
            date_width = len(date_str) * 9
            if service_width > max_service_width:
                max_service_width = service_width
            if date_width > max_date_width:
                max_date_width = date_width
        max_service_width = max(100, min(max_service_width + 20, 200))
        max_date_width = max(80, min(max_date_width + 15, 120))
        self.tree.column('service', width=max_service_width)
        self.tree.column('created', width=max_date_width)

    def on_service_select(self, event):
        service_name = get_treeview_selected(self.tree)
        if service_name:
            self.current_service = service_name
            self.show_service_details_panel(service_name)

    def on_tree_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        service_name = get_treeview_selected(self.tree)
        if not service_name:
            return
        service_data = self.manager.get_service(service_name)
        if service_data and service_data.get('url', ''):
            webbrowser.open(service_data['url'])
            self.manager.update_last_accessed(service_name)
            self.refresh_services_list()

    # ---------- Контекстное меню (правый клик) ----------
    def show_context_menu(self, event):
        """Показывает контекстное меню для выбранного сервиса (правый клик)"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        service_name = self.tree.item(item, 'values')[0]
        if not service_name:
            return
        service_data = self.manager.get_service(service_name)
        if not service_data:
            return

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="📋 Копировать пароль", command=lambda: self.copy_password_to_clipboard(service_name))
        if service_data.get('url', ''):
            menu.add_command(label="🌐 Открыть ссылку", command=lambda: webbrowser.open(service_data['url']))
        menu.add_separator()
        menu.add_command(label="✏️ Изменить ссылку", command=lambda: self.show_edit_url_panel(service_name))
        menu.add_command(label="✏️ Изменить логин", command=lambda: self.show_edit_username_panel(service_name))
        menu.add_command(label="✏️ Изменить заметки", command=lambda: self.show_edit_notes_panel(service_name))
        menu.add_separator()
        menu.add_command(label="🗑️ Удалить сервис", command=lambda: self.show_delete_service_panel(service_name))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ---------- Отображение деталей ----------
    def show_service_details_panel(self, service_name):
        self.current_service = service_name
        self.manager.update_last_accessed(service_name)
        service_data = self.manager.get_service(service_name)
        if not service_data:
            self.show_no_service_selected()
            return

        self.clear_right_panel()

        title_frame = ttk.Frame(self.right_content)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(title_frame, text=service_name,
                  style='Title.TLabel', font=('Arial', 13)).pack(anchor=tk.W)

        info_frame = ttk.Frame(self.right_content)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        created_at = datetime.fromisoformat(service_data['created_at'])
        formatted_date = created_at.strftime("%d.%m.%Y")
        ttk.Label(info_frame, text=f"Дата создания: {formatted_date}").pack(anchor=tk.W, pady=2)

        status_text, status_color = self.manager.get_password_age_status(service_data['created_at'])
        status_label = ttk.Label(info_frame, text=f"Статус: {status_text}", font=('Arial', 10))
        if "Требуется" in status_text:
            status_label.config(foreground='red', font=('Arial', 10, 'bold'))
        elif "Рекомендуется" in status_text:
            status_label.config(foreground='orange', font=('Arial', 10, 'bold'))
        else:
            status_label.config(foreground='green', font=('Arial', 10, 'bold'))
        status_label.pack(anchor=tk.W, pady=2)

        username = service_data.get('username', '')
        if username:
            ttk.Label(info_frame, text=f"Логин: {username}").pack(anchor=tk.W, pady=2)

        url = service_data.get('url', '')
        if url:
            url_frame = ttk.Frame(self.right_content)
            url_frame.pack(fill=tk.X, pady=(0, 15))
            ttk.Label(url_frame, text="Ссылка:", style='Detail.TLabel').pack(anchor=tk.W)
            link_button = ttk.Button(
                url_frame,
                text="Перейти на сайт",
                style='Link.TButton',
                command=lambda u=url: webbrowser.open(u)
            )
            link_button.pack(anchor=tk.W, pady=(5, 0))

        notes = service_data.get('notes', '')
        if notes:
            notes_frame = ttk.Frame(self.right_content)
            notes_frame.pack(fill=tk.X, pady=(0, 15))
            ttk.Label(notes_frame, text="Заметки:", style='Detail.TLabel').pack(anchor=tk.W)
            ttk.Label(notes_frame, text=notes, wraplength=200).pack(anchor=tk.W, pady=2)

        password_frame = ttk.Frame(self.right_content)
        password_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(password_frame, text="Пароль:", style='Detail.TLabel').pack(anchor=tk.W)

        pending = service_data.get('pending_password')
        if pending:
            password_display = ttk.Entry(
                password_frame,
                textvariable=tk.StringVar(value=pending),
                state='readonly',
                font=('Arial', 10)
            )
            password_display.pack(fill=tk.X, pady=(5, 5))
            action_frame = ttk.Frame(password_frame)
            action_frame.pack(fill=tk.X, pady=5)
            ttk.Button(action_frame, text="✅ Подтвердить смену",
                       command=lambda: self.confirm_password_change(service_name)).pack(side=tk.LEFT, padx=2)
            ttk.Button(action_frame, text="❌ Отменить",
                       command=lambda: self.cancel_password_change(service_name)).pack(side=tk.LEFT, padx=2)
        else:
            password_inner_frame = ttk.Frame(password_frame)
            password_inner_frame.pack(fill=tk.X, pady=(5, 0))
            self.password_entry_var = tk.StringVar(value=service_data['current_password'])
            password_display = ttk.Entry(
                password_inner_frame,
                textvariable=self.password_entry_var,
                show="*",
                width=20,
                state='readonly'
            )
            password_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            self.show_password_var = tk.BooleanVar(value=False)
            show_button = ttk.Checkbutton(
                password_inner_frame,
                text="👁",
                variable=self.show_password_var,
                command=lambda: self.toggle_password_visibility(password_display),
                style='Toggle.TCheckbutton'
            )
            show_button.pack(side=tk.LEFT, padx=(0, 5))

            copy_button = ttk.Button(
                password_inner_frame,
                text="📋",
                command=lambda: self.copy_password_to_clipboard(service_name),
                width=3
            )
            copy_button.pack(side=tk.LEFT)

            action_frame = ttk.Frame(password_frame)
            action_frame.pack(fill=tk.X, pady=10)
            ttk.Button(action_frame, text="🔄 Сгенерировать новый",
                       command=lambda: self.generate_pending_password(service_name)).pack(fill=tk.X, pady=2)

            manual_frame = ttk.Frame(action_frame)
            manual_frame.pack(fill=tk.X, pady=2)
            self.manual_password_entry = ttk.Entry(manual_frame, show="*")
            self.manual_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            ttk.Button(manual_frame, text="Установить свой пароль",
                       command=lambda: self.set_manual_password(service_name)).pack(side=tk.LEFT)

            ttk.Button(action_frame, text="📜 История паролей",
                       command=lambda: self.show_password_history(service_name)).pack(fill=tk.X, pady=2)

        action_frame2 = ttk.Frame(self.right_content)
        action_frame2.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(action_frame2, text="Изменить ссылку",
                   command=lambda: self.show_edit_url_panel(service_name)).pack(fill=tk.X, pady=3)
        ttk.Button(action_frame2, text="Изменить логин",
                   command=lambda: self.show_edit_username_panel(service_name)).pack(fill=tk.X, pady=3)
        ttk.Button(action_frame2, text="Изменить заметки",
                   command=lambda: self.show_edit_notes_panel(service_name)).pack(fill=tk.X, pady=3)
        ttk.Button(action_frame2, text="Удалить сервис",
                   command=lambda: self.show_delete_service_panel(service_name)).pack(fill=tk.X, pady=3)
        ttk.Button(action_frame2, text="⚙️ Настройки",
                   command=self.show_settings_window).pack(fill=tk.X, pady=3)

    # ---------- Вспомогательные методы ----------
    def toggle_theme(self, parent_window):
        self.app.toggle_theme()
        parent_window.destroy()

    def apply_theme(self, dark=False):
        """Применяет тему ко всем виджетам, включая статусы в списке"""
        if dark:
            bg = '#2d2d2d'
            fg = '#ffffff'
            select_bg = '#3d3d3d'
            red_bg = '#5c1a1a'
            orange_bg = '#5c3a1a'
            green_bg = '#1a4a1a'
            status_fg = '#ffffff'
        else:
            bg = '#f0f0f0'
            fg = '#000000'
            select_bg = '#e0e0e0'
            red_bg = '#ffb8b8'
            orange_bg = '#ffc7a2'
            green_bg = '#b4ffb4'
            status_fg = '#000000'

        self.app.root.configure(bg=bg)

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

        self.tree.tag_configure('red', background=red_bg, foreground=status_fg)
        self.tree.tag_configure('orange', background=orange_bg, foreground=status_fg)
        self.tree.tag_configure('green', background=green_bg, foreground=status_fg)

    def toggle_password_visibility(self, password_widget):
        if self.show_password_var.get():
            password_widget.config(show="")
        else:
            password_widget.config(show="*")

    def show_backup_manager(self):
        """Окно управления резервными копиями"""
        backups = self.manager.list_backups()
        if not backups:
            self.app.show_notification("Резервные копии не найдены", "orange")
            return

        dialog = tk.Toplevel(self.app.root)
        dialog.title("Управление резервными копиями")
        dialog.geometry("500x400")
        dialog.transient(self.app.root)
        dialog.grab_set()
        dark = self.app.is_dark_theme()
        dialog.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Резервные копии", style='Title.TLabel').pack(pady=10)

        # Список с прокруткой
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10),
                             bg='#3d3d3d' if dark else 'white',
                             fg='white' if dark else 'black')
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Заполняем список (отображаем дату и имя)
        for idx, b in enumerate(backups):
            listbox.insert(tk.END, f"{b['date']}  {b['name']}")

        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        def restore_selected():
            selection = listbox.curselection()
            if not selection:
                self.app.show_notification("Выберите копию для восстановления", "orange")
                return
            idx = selection[0]
            backup_name = backups[idx]['name']
            if tk.messagebox.askyesno("Восстановление",
                                      f"Восстановить данные из копии {backup_name}?\nТекущие данные будут заменены."):
                if self.manager.restore_backup(backup_name):
                    self.app.show_notification("Данные восстановлены", "green")
                    self.refresh_services_list()
                    if self.current_service:
                        self.show_service_details_panel(self.current_service)
                    dialog.destroy()
                else:
                    self.app.show_notification("Ошибка восстановления", "red")

        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                self.app.show_notification("Выберите копию для удаления", "orange")
                return
            idx = selection[0]
            backup_name = backups[idx]['name']
            if tk.messagebox.askyesno("Удаление", f"Удалить копию {backup_name}?"):
                try:
                    os.remove(backups[idx]['path'])
                    self.app.show_notification("Копия удалена", "green")
                    dialog.destroy()
                    self.show_backup_manager()  # обновляем список
                except Exception as e:
                    self.app.show_notification(f"Ошибка удаления: {e}", "red")

        ttk.Button(btn_frame, text="🔄 Восстановить", command=restore_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Удалить", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)


    def show_password_settings(self, parent_window):
        from utils.config import load_config, save_config
        config = load_config()

        dialog = tk.Toplevel(parent_window)
        dialog.title("Настройки генерации пароля")
        dialog.geometry("350x280")
        dialog.transient(parent_window)
        dialog.grab_set()
        dark = self.app.is_dark_theme()
        dialog.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Параметры генерации пароля", style='Title.TLabel').pack(pady=10)

        length_frame = ttk.Frame(frame)
        length_frame.pack(fill=tk.X, pady=5)
        ttk.Label(length_frame, text="Длина:").pack(side=tk.LEFT, padx=5)
        length_var = tk.IntVar(value=config.get('password_length', 20))
        length_spin = ttk.Spinbox(length_frame, from_=4, to=50, textvariable=length_var, width=10)
        length_spin.pack(side=tk.LEFT, padx=5)

        use_symbols_var = tk.BooleanVar(value=config.get('use_symbols', True))
        use_digits_var = tk.BooleanVar(value=config.get('use_digits', True))
        use_uppercase_var = tk.BooleanVar(value=config.get('use_uppercase', True))
        use_lowercase_var = tk.BooleanVar(value=config.get('use_lowercase', True))

        ttk.Checkbutton(frame, text="Использовать спецсимволы (*&$#?@)",
                        variable=use_symbols_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Использовать цифры",
                        variable=use_digits_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Использовать заглавные буквы",
                        variable=use_uppercase_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Использовать строчные буквы",
                        variable=use_lowercase_var).pack(anchor=tk.W, pady=2)

        def save_settings():
            new_config = {
                'password_length': length_var.get(),
                'use_symbols': use_symbols_var.get(),
                'use_digits': use_digits_var.get(),
                'use_uppercase': use_uppercase_var.get(),
                'use_lowercase': use_lowercase_var.get()
            }
            current_config = load_config()
            current_config.update(new_config)
            save_config(current_config)
            self.app.show_notification("Настройки сохранены", "green")
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Сохранить", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_settings_window(self):
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("Настройки")
        settings_window.geometry("400x400")
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        dark = self.app.is_dark_theme()
        settings_window.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        main_frame = ttk.Frame(settings_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Настройки менеджера паролей", style='Title.TLabel').pack(pady=10)

        ttk.Button(main_frame, text="🔑 Сменить мастер-пароль",
                   command=lambda: self.show_change_master_password(settings_window)).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="📤 Экспорт данных (JSON)",
                   command=lambda: self.export_data('json')).pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="📤 Экспорт данных (CSV)",
                   command=lambda: self.export_data('csv')).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="📥 Импорт данных (JSON/CSV)",
                   command=self.import_data).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="⚙️ Параметры генерации пароля",
                   command=lambda: self.show_password_settings(settings_window)).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="🌓 Переключить тему (светлая/тёмная)",
                   command=lambda: self.toggle_theme(settings_window)).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="💾 Управление резервными копиями",
                   command=self.show_backup_manager).pack(fill=tk.X, pady=5)

        ttk.Button(main_frame, text="Закрыть", command=settings_window.destroy).pack(pady=15)

    def copy_password_to_clipboard(self, service_name):
        service_data = self.manager.get_service(service_name)
        if not service_data:
            self.app.show_notification("Сервис не найден", "red")
            return
        password = service_data['current_password']
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(password)
        self.manager.update_last_accessed(service_name)
        self.refresh_services_list()
        self.app.show_notification("Пароль скопирован в буфер обмена", "green")

    # ---------- Методы для работы с паролем ----------
    def generate_pending_password(self, service_name):
        new_pw = self.manager.generate_pending_password(service_name)
        if new_pw:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(new_pw)
            self.show_service_details_panel(service_name)
            self.app.show_notification(
                "Пароль скопирован в буфер обмена. Вставьте его на сайте, затем нажмите 'Подтвердить смену'.",
                "blue", duration=5000
            )
        else:
            self.app.show_notification("Не удалось сгенерировать пароль", "red")

    def confirm_password_change(self, service_name):
        if self.manager.confirm_password_change(service_name):
            self.refresh_services_list()
            self.show_service_details_panel(service_name)
            self.app.show_notification("Пароль успешно обновлён", "green")
        else:
            self.app.show_notification("Не удалось подтвердить смену", "red")

    def cancel_password_change(self, service_name):
        self.manager.cancel_password_change(service_name)
        self.refresh_services_list()
        self.show_service_details_panel(service_name)
        self.app.show_notification("Смена пароля отменена", "orange")

    def set_manual_password(self, service_name):
        manual_pw = self.manual_password_entry.get().strip()
        if not manual_pw:
            self.app.show_notification("Введите пароль", "red")
            return
        new_pw = self.manager.generate_pending_password(service_name, custom_password=manual_pw)
        if new_pw:
            self.manual_password_entry.delete(0, tk.END)
            self.show_service_details_panel(service_name)
            self.app.show_notification(
                "Пароль установлен как временный. Подтвердите или отмените смену.",
                "blue"
            )
        else:
            self.app.show_notification("Не удалось установить пароль", "red")

    # ---------- Панели добавления/изменения ----------
    def show_add_service_panel(self):
        self.clear_right_panel()
        ttk.Label(self.right_content, text="Добавление нового сервиса",
                  style='Title.TLabel').pack(pady=(0, 20), anchor=tk.W)

        form_frame = ttk.Frame(self.right_content)
        form_frame.pack(pady=(0, 20), fill=tk.X)

        ttk.Label(form_frame, text="Название сервиса:").pack(anchor=tk.W, pady=(0, 5))
        self.add_service_name = ttk.Entry(form_frame)
        self.add_service_name.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form_frame, text="Логин (необязательно):").pack(anchor=tk.W, pady=(0, 5))
        self.add_username = ttk.Entry(form_frame)
        self.add_username.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form_frame, text="Пароль (оставьте пустым для генерации):").pack(anchor=tk.W, pady=(0, 5))
        self.add_password = ttk.Entry(form_frame)
        self.add_password.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form_frame, text="Ссылка (необязательно):").pack(anchor=tk.W, pady=(0, 5))
        self.add_url = ttk.Entry(form_frame)
        self.add_url.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form_frame, text="Заметки (необязательно):").pack(anchor=tk.W, pady=(0, 5))
        self.add_notes = ttk.Entry(form_frame)
        self.add_notes.pack(fill=tk.X, pady=(0, 15))

        button_frame = ttk.Frame(self.right_content)
        button_frame.pack()
        ttk.Button(button_frame, text="Сохранить", command=self.save_new_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=self.show_no_service_selected).pack(side=tk.LEFT, padx=5)

    def save_new_service(self):
        service_name = self.add_service_name.get().strip()
        if not service_name:
            self.app.show_notification("Введите название сервиса", "red")
            return
        username = self.add_username.get().strip() or None
        password = self.add_password.get().strip() or None
        url = self.add_url.get().strip() or None
        notes = self.add_notes.get().strip() or None

        if self.manager.add_service(service_name, password, url, username, notes):
            self.refresh_services_list()
            for child in self.tree.get_children():
                if self.tree.item(child, 'values')[0] == service_name:
                    self.tree.selection_set(child)
                    self.tree.focus(child)
                    self.current_service = service_name
                    self.show_service_details_panel(service_name)
                    break
            self.app.show_notification("Сервис успешно добавлен", "green")
        else:
            self.app.show_notification("Сервис с таким именем уже существует", "red")

    # ---------- Изменение ссылки ----------
    def show_edit_url_panel(self, service_name):
        self.clear_right_panel()
        service_data = self.manager.get_service(service_name)
        current_url = service_data.get('url', '') if service_data else ''

        ttk.Label(self.right_content, text=f"Изменение ссылки: {service_name}",
                  style='Title.TLabel').pack(pady=(0, 20), anchor=tk.W)
        ttk.Label(self.right_content, text="Новая ссылка (оставьте пустым, чтобы удалить):").pack(anchor=tk.W, pady=(0, 5))
        self.edit_url_entry = ttk.Entry(self.right_content)
        if current_url:
            self.edit_url_entry.insert(0, current_url)
        self.edit_url_entry.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(self.right_content)
        button_frame.pack()
        ttk.Button(button_frame, text="Сохранить",
                   command=lambda: self.save_url_change(service_name)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=lambda: self.show_service_details_panel(service_name)).pack(side=tk.LEFT, padx=5)

    def save_url_change(self, service_name):
        new_url = self.edit_url_entry.get().strip() or None
        if self.manager.update_service_url(service_name, new_url):
            self.refresh_services_list()
            self.show_service_details_panel(service_name)
            self.app.show_notification("Ссылка успешно обновлена", "green")
        else:
            self.app.show_notification("Не удалось обновить ссылку", "red")

    def show_change_master_password(self, parent_window):
        dialog = tk.Toplevel(parent_window)
        dialog.title("Смена мастер-пароля")
        dialog.geometry("350x200")
        dialog.transient(parent_window)
        dialog.grab_set()
        dark = self.app.is_dark_theme()
        dialog.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Старый пароль:").pack(anchor=tk.W, pady=2)
        old_pw = ttk.Entry(frame, show="*", width=30)
        old_pw.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Новый пароль:").pack(anchor=tk.W, pady=2)
        new_pw = ttk.Entry(frame, show="*", width=30)
        new_pw.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Подтвердите новый пароль:").pack(anchor=tk.W, pady=2)
        confirm_pw = ttk.Entry(frame, show="*", width=30)
        confirm_pw.pack(fill=tk.X, pady=5)

        def change():
            old = old_pw.get()
            new = new_pw.get()
            confirm = confirm_pw.get()
            if not old or not new or not confirm:
                self.app.show_notification("Заполните все поля", "red")
                return
            if new != confirm:
                self.app.show_notification("Пароли не совпадают", "red")
                return
            if len(new) < 4:
                self.app.show_notification("Пароль должен быть не менее 4 символов", "red")
                return
            if self.manager.change_master_password(old, new):
                self.app.show_notification("Мастер-пароль успешно изменён", "green")
                dialog.destroy()
                parent_window.destroy()
            else:
                self.app.show_notification("Неверный старый пароль", "red")

        ttk.Button(frame, text="Изменить", command=change).pack(pady=10)
        ttk.Button(frame, text="Отмена", command=dialog.destroy).pack()

    def export_data(self, format_type):
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=[(format_type.upper(), f"*.{format_type}")]
        )
        if not file_path:
            return

        password = self.ask_master_password()
        if password is None:
            return

        if self.manager.export_data(password, format_type, file_path):
            self.app.show_notification(f"Данные экспортированы в {file_path}", "green")
        else:
            self.app.show_notification("Неверный пароль или ошибка экспорта", "red")

    def import_data(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            format_type = 'json'
        elif ext == '.csv':
            format_type = 'csv'
        else:
            self.app.show_notification("Неподдерживаемый формат", "red")
            return

        password = self.ask_master_password()
        if password is None:
            return

        from tkinter import messagebox
        merge = messagebox.askyesno("Импорт", "Объединить с существующими данными?\n(Нажмите 'Нет' для полной замены)")
        if self.manager.import_data(file_path, password, format_type, merge):
            self.app.show_notification("Данные импортированы успешно", "green")
            self.refresh_services_list()
        else:
            self.app.show_notification("Ошибка импорта или неверный пароль", "red")

    def ask_master_password(self):
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Введите мастер-пароль")
        dialog.geometry("300x120")
        dialog.transient(self.app.root)
        dialog.grab_set()
        dark = self.app.is_dark_theme()
        dialog.configure(bg='#2d2d2d' if dark else '#f0f0f0')

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Введите мастер-пароль для подтверждения:").pack(anchor=tk.W, pady=5)
        pw_entry = ttk.Entry(frame, show="*", width=30)
        pw_entry.pack(fill=tk.X, pady=5)

        result = [None]

        def confirm():
            result[0] = pw_entry.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=cancel).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result[0]

    # ---------- Изменение логина ----------
    def show_edit_username_panel(self, service_name):
        self.clear_right_panel()
        service_data = self.manager.get_service(service_name)
        current_username = service_data.get('username', '') if service_data else ''

        ttk.Label(self.right_content, text=f"Изменение логина: {service_name}",
                  style='Title.TLabel').pack(pady=(0, 20), anchor=tk.W)
        ttk.Label(self.right_content, text="Новый логин:").pack(anchor=tk.W, pady=(0, 5))
        self.edit_username_entry = ttk.Entry(self.right_content)
        if current_username:
            self.edit_username_entry.insert(0, current_username)
        self.edit_username_entry.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(self.right_content)
        button_frame.pack()
        ttk.Button(button_frame, text="Сохранить",
                   command=lambda: self.save_username_change(service_name)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=lambda: self.show_service_details_panel(service_name)).pack(side=tk.LEFT, padx=5)

    def save_username_change(self, service_name):
        new_username = self.edit_username_entry.get().strip()
        if self.manager.update_service_username(service_name, new_username):
            self.refresh_services_list()
            self.show_service_details_panel(service_name)
            self.app.show_notification("Логин успешно обновлён", "green")
        else:
            self.app.show_notification("Не удалось обновить логин", "red")

    # ---------- Изменение заметок ----------
    def show_edit_notes_panel(self, service_name):
        self.clear_right_panel()
        service_data = self.manager.get_service(service_name)
        current_notes = service_data.get('notes', '') if service_data else ''

        ttk.Label(self.right_content, text=f"Изменение заметок: {service_name}",
                  style='Title.TLabel').pack(pady=(0, 20), anchor=tk.W)
        ttk.Label(self.right_content, text="Новые заметки:").pack(anchor=tk.W, pady=(0, 5))
        self.edit_notes_entry = ttk.Entry(self.right_content)
        if current_notes:
            self.edit_notes_entry.insert(0, current_notes)
        self.edit_notes_entry.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(self.right_content)
        button_frame.pack()
        ttk.Button(button_frame, text="Сохранить",
                   command=lambda: self.save_notes_change(service_name)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=lambda: self.show_service_details_panel(service_name)).pack(side=tk.LEFT, padx=5)

    def save_notes_change(self, service_name):
        new_notes = self.edit_notes_entry.get().strip()
        if self.manager.update_service_notes(service_name, new_notes):
            self.refresh_services_list()
            self.show_service_details_panel(service_name)
            self.app.show_notification("Заметки успешно обновлены", "green")
        else:
            self.app.show_notification("Не удалось обновить заметки", "red")

    # ---------- Удаление сервиса ----------
    def show_delete_service_panel(self, service_name):
        self.clear_right_panel()
        ttk.Label(self.right_content, text="Подтверждение удаления",
                  style='Title.TLabel').pack(pady=(0, 15), anchor=tk.W)
        ttk.Label(self.right_content, text=f"Вы уверены, что хотите удалить сервис:",
                  font=('Arial', 11)).pack(pady=(0, 5))
        ttk.Label(self.right_content, text=f"{service_name}",
                  font=('Arial', 11, 'bold'), foreground='red').pack(pady=(0, 20))
        ttk.Label(self.right_content, text="Для подтверждения введите мастер-пароль:").pack(pady=(0, 5))
        self.delete_password_entry = ttk.Entry(self.right_content, show="*")
        self.delete_password_entry.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(self.right_content)
        button_frame.pack()
        ttk.Button(button_frame, text="Удалить",
                   command=lambda: self.confirm_delete_service(service_name)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена",
                   command=lambda: self.show_service_details_panel(service_name)).pack(side=tk.LEFT, padx=5)

    def confirm_delete_service(self, service_name):
        password = self.delete_password_entry.get()
        if not password:
            self.app.show_notification("Введите пароль", "red")
            return
        if password != self.manager.master_password:
            self.app.show_notification("Неверный пароль", "red")
            return
        if self.manager.delete_service(service_name):
            self.refresh_services_list()
            self.current_service = None
            self.show_no_service_selected()
            self.app.show_notification("Сервис успешно удален", "green")
        else:
            self.app.show_notification("Не удалось удалить сервис", "red")

    # ---------- История паролей ----------
    def show_password_history(self, service_name):
        history = self.manager.get_service_history(service_name)
        if not history:
            self.app.show_notification("История паролей пуста", "orange")
            return

        dark = self.app.is_dark_theme()
        bg = '#2d2d2d' if dark else '#f0f0f0'
        fg = '#ffffff' if dark else '#000000'

        history_window = tk.Toplevel(self.app.root)
        history_window.title(f"История паролей: {service_name}")
        history_window.geometry("580x450")
        history_window.transient(self.app.root)
        history_window.grab_set()
        history_window.configure(bg=bg)

        main_frame = tk.Frame(history_window, bg=bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text=f"Сохранённые пароли для {service_name}",
                  style='Title.TLabel', background=bg, foreground=fg).pack(pady=(0, 10))

        canvas_frame = tk.Frame(main_frame, bg=bg)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0, bg=bg)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for entry in reversed(history):
            dt = datetime.fromisoformat(entry['changed_at']).strftime("%d.%m.%Y %H:%M")
            password = entry['password']

            frame = tk.Frame(scrollable_frame, relief=tk.RIDGE, borderwidth=1, bg=bg)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=dt, width=18, background=bg, foreground=fg).pack(side=tk.LEFT, padx=5)

            pw_var = tk.StringVar(value='*' * len(password))
            pw_entry = ttk.Entry(frame, textvariable=pw_var, state='readonly', width=25)
            pw_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            show_flag = [False]

            def toggle_show(entry=pw_entry, pw=password, flag=show_flag):
                if flag[0]:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    entry.insert(0, '*' * len(pw))
                    entry.config(state='readonly')
                    flag[0] = False
                else:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    entry.insert(0, pw)
                    entry.config(state='readonly')
                    flag[0] = True

            ttk.Button(frame, text="👁", width=3, command=toggle_show).pack(side=tk.LEFT, padx=2)

            def copy_pw(pw=password):
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(pw)
                self.app.show_notification("Пароль скопирован в буфер обмена", "green")

            ttk.Button(frame, text="📋", width=3, command=copy_pw).pack(side=tk.LEFT, padx=2)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Закрыть", command=history_window.destroy).pack(side=tk.RIGHT, padx=5)