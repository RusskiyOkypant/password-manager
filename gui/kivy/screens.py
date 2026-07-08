import webbrowser
import os
from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.modalview import ModalView
from kivy.core.window import Window

from gui.kivy.widgets import (
    MultiLineButton, ServiceButton, GreenButton, BlueButton, RedButton, GrayButton,
    DarkPopup
)
from core.password_manager import PasswordManager


class CreateVaultScreen(Screen):
    def __init__(self, **kwargs):
        self.app = kwargs.pop('app')
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        title = Label(text='Создание нового хранилища', font_size='24sp',
                      size_hint=(1, 0.2), halign='center', color=(0, 0, 0, 1), bold=True)
        title.bind(size=title.setter('text_size'))
        layout.add_widget(title)

        input_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        input_layout.add_widget(Label(text='Придумайте мастер-пароль:', font_size='16sp',
                                      size_hint=(1, None), height=dp(30), color=(0, 0, 0, 1)))
        self.master_password = TextInput(password=True, multiline=False, size_hint=(1, None),
                                         height=dp(45), foreground_color=(0, 0, 0, 1),
                                         background_color=get_color_from_hex('#F5F5F5'),
                                         padding=dp(10), font_size='14sp')
        input_layout.add_widget(self.master_password)

        input_layout.add_widget(Label(text='Подтвердите мастер-пароль:', font_size='16sp',
                                      size_hint=(1, None), height=dp(30), color=(0, 0, 0, 1)))
        self.confirm_password = TextInput(password=True, multiline=False, size_hint=(1, None),
                                          height=dp(45), foreground_color=(0, 0, 0, 1),
                                          background_color=get_color_from_hex('#F5F5F5'),
                                          padding=dp(10), font_size='14sp')
        input_layout.add_widget(self.confirm_password)

        button_layout = BoxLayout(size_hint=(1, 0.2))
        self.create_button = GreenButton(text='Создать хранилище', font_size='18sp',
                                         size_hint=(1, None), height=dp(50))
        self.create_button.bind(on_press=self.create_vault)
        button_layout.add_widget(self.create_button)

        layout.add_widget(input_layout)
        layout.add_widget(button_layout)
        self.add_widget(layout)

    def create_vault(self, instance):
        password = self.master_password.text
        confirm = self.confirm_password.text
        if not password or not confirm:
            self.app.show_notification('Пароли не могут быть пустыми', 'red')
            return
        if password != confirm:
            self.app.show_notification('Пароли не совпадают', 'red')
            return
        if self.app.manager.create_vault(password, confirm):
            self.app.show_notification('Хранилище успешно создано!', 'green')
            self.app.main_screen.refresh_services()
            self.app.screen_manager.current = 'main'
        else:
            self.app.show_notification('Не удалось создать хранилище', 'red')


class UnlockScreen(Screen):
    def __init__(self, **kwargs):
        self.app = kwargs.pop('app')
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        title = Label(text='Разблокировка хранилища', font_size='24sp',
                      size_hint=(1, 0.3), halign='center', color=(0, 0, 0, 1), bold=True)
        title.bind(size=title.setter('text_size'))
        layout.add_widget(title)

        input_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        input_layout.add_widget(Label(text='Введите мастер-пароль:', font_size='16sp',
                                      size_hint=(1, None), height=dp(30), color=(0, 0, 0, 1)))
        self.password_input = TextInput(password=True, multiline=False, size_hint=(1, None),
                                        height=dp(45), foreground_color=(0, 0, 0, 1),
                                        background_color=get_color_from_hex('#F5F5F5'),
                                        padding=dp(10), font_size='14sp')
        input_layout.add_widget(self.password_input)

        button_layout = BoxLayout(size_hint=(1, 0.3))
        self.unlock_button = BlueButton(text='Разблокировать', font_size='18sp',
                                        size_hint=(1, None), height=dp(50))
        self.unlock_button.bind(on_press=self.unlock_vault)
        button_layout.add_widget(self.unlock_button)

        layout.add_widget(input_layout)
        layout.add_widget(button_layout)
        self.add_widget(layout)

    def unlock_vault(self, instance):
        password = self.password_input.text
        if not password:
            self.app.show_notification('Введите пароль', 'red')
            return
        if self.app.manager.unlock_vault(password):
            self.app.main_screen.refresh_services()
            self.app.screen_manager.current = 'main'
        else:
            self.app.show_notification('Неверный пароль', 'red')


class MainScreen(Screen):
    def __init__(self, **kwargs):
        self.app = kwargs.pop('app')
        super().__init__(**kwargs)
        self.current_service = None
        self._refresh_scheduled = False
        self.current_query = ''  # для поиска

        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Верхняя панель
        top_bar = BoxLayout(size_hint=(1, 0.08), spacing=dp(10))
        title_label = Label(text='Менеджер паролей', font_size='20sp',
                            halign='left', valign='middle', color=(0, 0, 0, 1), bold=True)
        title_label.bind(size=title_label.setter('text_size'))
        self.sync_button = GreenButton(text='Синхронизация', size_hint=(0.4, 1), font_size='14sp')
        self.sync_button.bind(on_press=self.show_sync_info)
        top_bar.add_widget(title_label)
        top_bar.add_widget(self.sync_button)
        main_layout.add_widget(top_bar)

        # Разделитель
        separator = BoxLayout(size_hint=(1, 0.002))
        with separator.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.8, 0.8, 0.8, 1)
            self.separator_rect = Rectangle(size=separator.size, pos=separator.pos)
        separator.bind(size=self._update_separator_rect, pos=self._update_separator_rect)
        main_layout.add_widget(separator)

        # Основное содержимое (горизонтальное разделение)
        content_layout = BoxLayout(orientation='horizontal', spacing=dp(10))

        # Левая панель (список сервисов)
        left_panel = BoxLayout(orientation='vertical', size_hint=(0.6, 1))

        # Кнопка добавления
        add_button = GreenButton(text='+ Добавить сервис', size_hint=(1, 0.08), font_size='16sp')
        add_button.bind(on_press=self.show_add_service)
        left_panel.add_widget(add_button)

        # Поле поиска
        search_box = BoxLayout(size_hint=(1, 0.06), spacing=dp(5))
        search_box.add_widget(Label(text='🔍', size_hint_x=0.1))
        self.search_input = TextInput(hint_text='Поиск...', multiline=False, size_hint_x=0.9,
                                      background_color=get_color_from_hex('#F5F5F5'),
                                      foreground_color=(0, 0, 0, 1))
        self.search_input.bind(text=self.on_search)
        search_box.add_widget(self.search_input)
        left_panel.add_widget(search_box)

        # Список сервисов
        scroll_view = ScrollView(size_hint=(1, 0.86), do_scroll_x=False)
        self.services_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(5))
        self.services_grid.bind(minimum_height=self.services_grid.setter('height'))
        scroll_view.add_widget(self.services_grid)
        left_panel.add_widget(scroll_view)

        # Правая панель (детали)
        self.right_panel = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        self.details_label = Label(text='Выберите сервис\nдля просмотра пароля',
                                   font_size='16sp', halign='center', valign='middle',
                                   color=(0.5, 0.5, 0.5, 1))
        self.details_label.bind(size=self.details_label.setter('text_size'))
        self.right_panel.add_widget(self.details_label)

        content_layout.add_widget(left_panel)
        content_layout.add_widget(self.right_panel)
        main_layout.add_widget(content_layout)

        self.add_widget(main_layout)
        self.app.main_screen = self
        self.bind(on_enter=self.on_enter)

    def _update_separator_rect(self, instance, value):
        if hasattr(self, 'separator_rect'):
            self.separator_rect.size = instance.size
            self.separator_rect.pos = instance.pos

    def on_enter(self, *args):
        self.refresh_services()

    def on_search(self, instance, value):
        self.current_query = value.strip()
        self.refresh_services()

    def refresh_services(self, dt=None):
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        Clock.schedule_once(self._refresh_services_impl, 0)

    def _refresh_services_impl(self, dt):
        try:
            app = self.app
            if self.current_query:
                services = app.manager.search_services(self.current_query)
            else:
                services = app.manager.list_services()

            self.services_grid.clear_widgets()

            if not services:
                no_services_label = Label(text='Нет сохраненных сервисов\n\nНажмите "+ Добавить сервис"',
                                          font_size='14sp', halign='center', valign='middle',
                                          color=(0.7, 0.7, 0.7, 1))
                no_services_label.bind(size=no_services_label.setter('text_size'))
                self.services_grid.add_widget(no_services_label)
                self.services_grid.height = dp(100)
            else:
                buttons = []
                for service in services:
                    service_data = app.manager.get_service(service)
                    created_at = datetime.fromisoformat(service_data['created_at'])
                    formatted_date = created_at.strftime("%d.%m.%Y")
                    status_text, status_color = app.manager.get_password_age_status(
                        service_data['created_at']
                    )
                    display_text = f'{service}\nСоздан: {formatted_date}\nСтатус: {status_text}'
                    service_btn = ServiceButton(text=display_text, size_hint=(1, None), height=dp(80))
                    if status_text == "Требуется замена":
                        service_btn.background_color = get_color_from_hex('#FFEBEE')
                    elif status_text == "Рекомендуется замена":
                        service_btn.background_color = get_color_from_hex('#FFF3E0')
                    else:
                        service_btn.background_color = get_color_from_hex('#E8F5E8')
                    service_btn.bind(on_press=lambda btn, s=service: self.show_service_details(s))
                    buttons.append(service_btn)

                for btn in buttons:
                    self.services_grid.add_widget(btn)

            self.update_sync_status()
            if self.current_service and self.current_service in services:
                self.show_service_details(self.current_service)
            else:
                self.current_service = None
        finally:
            self._refresh_scheduled = False

    def update_sync_status(self):
        status_text, status_color = self.app.manager.get_sync_status()
        self.sync_button.text = status_text[:15] + "..." if len(status_text) > 15 else status_text
        if status_color == (0, 0.8, 0, 1):
            self.sync_button.background_color = get_color_from_hex('#4CAF50')
        elif status_color == (1, 0.5, 0, 1):
            self.sync_button.background_color = get_color_from_hex('#FF9800')
        else:
            self.sync_button.background_color = get_color_from_hex('#F44336')

    def show_service_details(self, service_name):
        self.current_service = service_name
        app = self.app
        service_data = app.manager.get_service(service_name)
        if not service_data:
            return
        app.manager.update_last_accessed(service_name)

        self.right_panel.clear_widgets()
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        details_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10),
                                   size_hint_y=None)
        details_layout.bind(minimum_height=details_layout.setter('height'))

        # Заголовок
        title = Label(text=service_name, font_size='20sp', size_hint_y=None, height=dp(40),
                      halign='left', color=(0, 0, 0, 1), bold=True)
        title.bind(size=title.setter('text_size'))
        details_layout.add_widget(title)

        # Дата создания
        created_at = datetime.fromisoformat(service_data['created_at'])
        formatted_date = created_at.strftime("%d.%m.%Y в %H:%M")
        date_label = Label(text=f'Создан: {formatted_date}', font_size='14sp',
                           size_hint_y=None, height=dp(30), color=(0, 0, 0, 1))
        details_layout.add_widget(date_label)

        # Статус
        status_text, status_color = app.manager.get_password_age_status(service_data['created_at'])
        status_label = Label(text=f'Статус: {status_text}', font_size='14sp',
                             color=status_color, size_hint_y=None, height=dp(30), bold=True)
        details_layout.add_widget(status_label)

        # Логин
        username = service_data.get('username', '')
        if username:
            username_label = Label(text=f'Логин: {username}', font_size='14sp',
                                   size_hint_y=None, height=dp(30), color=(0, 0, 0, 1))
            details_layout.add_widget(username_label)

        # Заметки
        notes = service_data.get('notes', '')
        if notes:
            notes_label = Label(text=f'Заметки: {notes}', font_size='14sp',
                                size_hint_y=None, height=dp(30), color=(0, 0, 0, 1))
            details_layout.add_widget(notes_label)

        # Ссылка
        url = service_data.get('url', '')
        if url:
            url_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
            url_layout.add_widget(Label(text='Ссылка на сайт:', font_size='14sp',
                                        size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
            url_button = BlueButton(text='Перейти на сайт', font_size='14sp',
                                    size_hint_y=None, height=dp(40))
            url_button.bind(on_press=lambda x: webbrowser.open(url))
            url_layout.add_widget(url_button)
            details_layout.add_widget(url_layout)

        # Пароль
        password_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        password_layout.add_widget(Label(text='Пароль:', font_size='14sp',
                                         size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        password_inner = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=dp(5))

        pending = service_data.get('pending_password')
        if pending:
            password_display = TextInput(text=pending, readonly=True, size_hint=(0.7, 1),
                                         foreground_color=(0, 0, 0, 1),
                                         background_color=get_color_from_hex('#F5F5F5'),
                                         padding=dp(10), font_size='14sp')
            password_inner.add_widget(password_display)
            buttons_layout = BoxLayout(orientation='horizontal', size_hint=(0.3, 1), spacing=dp(5))
            confirm_btn = GreenButton(text='✅', size_hint=(0.5, 1))
            confirm_btn.bind(on_press=lambda x: self.confirm_password_change(service_name))
            cancel_btn = RedButton(text='❌', size_hint=(0.5, 1))
            cancel_btn.bind(on_press=lambda x: self.cancel_password_change(service_name))
            buttons_layout.add_widget(confirm_btn)
            buttons_layout.add_widget(cancel_btn)
            password_inner.add_widget(buttons_layout)
        else:
            self.password_display = TextInput(text=service_data['current_password'],
                                              password=True, readonly=True,
                                              size_hint=(0.7, 1), foreground_color=(0, 0, 0, 1),
                                              background_color=get_color_from_hex('#F5F5F5'),
                                              padding=dp(10), font_size='14sp')
            password_inner.add_widget(self.password_display)
            buttons_layout = BoxLayout(orientation='horizontal', size_hint=(0.3, 1), spacing=dp(5))
            self.show_password_btn = ToggleButton(text='👁', size_hint=(0.5, 1),
                                                  background_normal='', background_down='',
                                                  background_color=get_color_from_hex('#E0E0E0'),
                                                  color=(0, 0, 0, 1))
            self.show_password_btn.bind(state=self.toggle_password_visibility)
            copy_btn = Button(text='📋', size_hint=(0.5, 1),
                              background_normal='', background_down='',
                              background_color=get_color_from_hex('#E0E0E0'),
                              color=(0, 0, 0, 1))
            copy_btn.bind(on_press=lambda x: self.copy_password(service_name))
            buttons_layout.add_widget(self.show_password_btn)
            buttons_layout.add_widget(copy_btn)
            password_inner.add_widget(buttons_layout)

        password_layout.add_widget(password_inner)
        details_layout.add_widget(password_layout)

        # Кнопки действий (включая настройки)
        actions_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, height=dp(250))
        generate_btn = BlueButton(text='Сгенерировать новый пароль', font_size='14sp',
                                  size_hint_y=None, height=dp(45))
        generate_btn.bind(on_press=lambda x: self.generate_pending_password(service_name))
        actions_layout.add_widget(generate_btn)

        manual_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=dp(5))
        self.manual_password_input = TextInput(password=True, multiline=False, size_hint=(0.7, 1),
                                               foreground_color=(0, 0, 0, 1),
                                               background_color=get_color_from_hex('#F5F5F5'),
                                               padding=dp(10), font_size='14sp')
        manual_layout.add_widget(self.manual_password_input)
        manual_set_btn = BlueButton(text='Установить', size_hint=(0.3, 1))
        manual_set_btn.bind(on_press=lambda x: self.set_manual_password(service_name))
        manual_layout.add_widget(manual_set_btn)
        actions_layout.add_widget(manual_layout)

        history_btn = BlueButton(text='История паролей', font_size='14sp',
                                 size_hint_y=None, height=dp(45))
        history_btn.bind(on_press=lambda x: self.show_password_history(service_name))
        actions_layout.add_widget(history_btn)

        change_url_btn = BlueButton(text='Изменить ссылку', font_size='14sp',
                                    size_hint_y=None, height=dp(45))
        change_url_btn.bind(on_press=lambda x: self.show_change_url(service_name))
        actions_layout.add_widget(change_url_btn)

        change_username_btn = BlueButton(text='Изменить логин', font_size='14sp',
                                         size_hint_y=None, height=dp(45))
        change_username_btn.bind(on_press=lambda x: self.show_change_username(service_name))
        actions_layout.add_widget(change_username_btn)

        change_notes_btn = BlueButton(text='Изменить заметки', font_size='14sp',
                                      size_hint_y=None, height=dp(45))
        change_notes_btn.bind(on_press=lambda x: self.show_change_notes(service_name))
        actions_layout.add_widget(change_notes_btn)

        delete_btn = RedButton(text='Удалить сервис', font_size='14sp',
                               size_hint_y=None, height=dp(45))
        delete_btn.bind(on_press=lambda x: self.show_delete_service(service_name))
        actions_layout.add_widget(delete_btn)

        # Кнопка настроек (добавляем в конец)
        settings_btn = BlueButton(text='⚙️ Настройки', font_size='14sp',
                                  size_hint_y=None, height=dp(45))
        settings_btn.bind(on_press=lambda x: self.show_settings_popup())
        actions_layout.add_widget(settings_btn)

        details_layout.add_widget(actions_layout)

        scroll_view.add_widget(details_layout)
        self.right_panel.add_widget(scroll_view)

    # ---------- Вспомогательные методы ----------
    def toggle_password_visibility(self, instance, state):
        if hasattr(self, 'password_display'):
            self.password_display.password = (state == 'normal')

    def copy_password(self, service_name):
        app = self.app
        service_data = app.manager.get_service(service_name)
        if service_data:
            Clipboard.copy(service_data['current_password'])
            app.show_notification('Пароль скопирован в буфер обмена', 'green')
            app.manager.update_last_accessed(service_name)
            self.refresh_services()

    # ---------- Всплывающие окна для добавления, изменения, удаления ----------
    def show_add_service(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text='Название сервиса:', color=(1, 1, 1, 1), font_size='14sp'))
        service_name_input = TextInput(multiline=False, size_hint_y=None, height=dp(45),
                                       foreground_color=(1, 1, 1, 1),
                                       background_color=get_color_from_hex('#555555'),
                                       padding=dp(10), font_size='14sp')
        content.add_widget(service_name_input)

        content.add_widget(Label(text='Логин (необязательно):', color=(1, 1, 1, 1), font_size='14sp'))
        username_input = TextInput(multiline=False, size_hint_y=None, height=dp(45),
                                   foreground_color=(1, 1, 1, 1),
                                   background_color=get_color_from_hex('#555555'),
                                   padding=dp(10), font_size='14sp')
        content.add_widget(username_input)

        content.add_widget(Label(text='Пароль (оставьте пустым для генерации):', color=(1, 1, 1, 1), font_size='14sp'))
        password_input = TextInput(multiline=False, password=True, size_hint_y=None, height=dp(45),
                                   foreground_color=(1, 1, 1, 1),
                                   background_color=get_color_from_hex('#555555'),
                                   padding=dp(10), font_size='14sp')
        content.add_widget(password_input)

        content.add_widget(Label(text='Ссылка (необязательно):', color=(1, 1, 1, 1), font_size='14sp'))
        url_input = TextInput(multiline=False, size_hint_y=None, height=dp(45),
                              foreground_color=(1, 1, 1, 1),
                              background_color=get_color_from_hex('#555555'),
                              padding=dp(10), font_size='14sp')
        content.add_widget(url_input)

        content.add_widget(Label(text='Заметки (необязательно):', color=(1, 1, 1, 1), font_size='14sp'))
        notes_input = TextInput(multiline=False, size_hint_y=None, height=dp(45),
                                foreground_color=(1, 1, 1, 1),
                                background_color=get_color_from_hex('#555555'),
                                padding=dp(10), font_size='14sp')
        content.add_widget(notes_input)

        buttons = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        def save_service(btn):
            name = service_name_input.text.strip()
            if not name:
                self.app.show_notification('Введите название сервиса', 'red')
                return
            pw = password_input.text.strip() or None
            url = url_input.text.strip() or None
            uname = username_input.text.strip() or None
            notes = notes_input.text.strip() or None
            if self.app.manager.add_service(name, pw, url, uname, notes):
                self.refresh_services()
                popup.dismiss()
                self.app.show_notification('Сервис успешно добавлен', 'green')
            else:
                self.app.show_notification('Сервис с таким именем уже существует', 'red')

        save_btn = GreenButton(text='Сохранить')
        save_btn.bind(on_press=save_service)
        cancel_btn = GrayButton(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)

        popup = DarkPopup(title='Добавление нового сервиса', content=content, size_hint=(0.9, 0.8))
        popup.open()

    def show_change_url(self, service_name):
        service_data = self.app.manager.get_service(service_name)
        current_url = service_data.get('url', '') if service_data else ''
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=f'Изменение ссылки: {service_name}', color=(1, 1, 1, 1),
                                 font_size='16sp', bold=True))
        content.add_widget(Label(text='Новая ссылка (оставьте пустым, чтобы удалить):',
                                 color=(1, 1, 1, 1), font_size='14sp'))
        url_input = TextInput(text=current_url, multiline=False, size_hint_y=None, height=dp(45),
                              foreground_color=(1, 1, 1, 1),
                              background_color=get_color_from_hex('#555555'),
                              padding=dp(10), font_size='14sp')
        content.add_widget(url_input)
        buttons = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        def save_url(btn):
            new_url = url_input.text.strip() or None
            if self.app.manager.update_service_url(service_name, new_url):
                self.refresh_services()
                popup.dismiss()
                self.app.show_notification('Ссылка успешно обновлена', 'green')
            else:
                self.app.show_notification('Не удалось обновить ссылку', 'red')
        save_btn = GreenButton(text='Сохранить')
        save_btn.bind(on_press=save_url)
        cancel_btn = GrayButton(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = DarkPopup(title='Изменение ссылки', content=content, size_hint=(0.9, 0.5))
        popup.open()

    def show_change_username(self, service_name):
        service_data = self.app.manager.get_service(service_name)
        current_username = service_data.get('username', '') if service_data else ''
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=f'Изменение логина: {service_name}', color=(1, 1, 1, 1),
                                 font_size='16sp', bold=True))
        content.add_widget(Label(text='Новый логин:', color=(1, 1, 1, 1), font_size='14sp'))
        uname_input = TextInput(text=current_username, multiline=False, size_hint_y=None, height=dp(45),
                                foreground_color=(1, 1, 1, 1),
                                background_color=get_color_from_hex('#555555'),
                                padding=dp(10), font_size='14sp')
        content.add_widget(uname_input)
        buttons = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        def save_uname(btn):
            new_uname = uname_input.text.strip()
            if self.app.manager.update_service_username(service_name, new_uname):
                self.refresh_services()
                popup.dismiss()
                self.app.show_notification('Логин успешно обновлён', 'green')
            else:
                self.app.show_notification('Не удалось обновить логин', 'red')
        save_btn = GreenButton(text='Сохранить')
        save_btn.bind(on_press=save_uname)
        cancel_btn = GrayButton(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = DarkPopup(title='Изменение логина', content=content, size_hint=(0.9, 0.5))
        popup.open()

    def show_change_notes(self, service_name):
        service_data = self.app.manager.get_service(service_name)
        current_notes = service_data.get('notes', '') if service_data else ''
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=f'Изменение заметок: {service_name}', color=(1, 1, 1, 1),
                                 font_size='16sp', bold=True))
        content.add_widget(Label(text='Новые заметки:', color=(1, 1, 1, 1), font_size='14sp'))
        notes_input = TextInput(text=current_notes, multiline=False, size_hint_y=None, height=dp(45),
                                foreground_color=(1, 1, 1, 1),
                                background_color=get_color_from_hex('#555555'),
                                padding=dp(10), font_size='14sp')
        content.add_widget(notes_input)
        buttons = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        def save_notes(btn):
            new_notes = notes_input.text.strip()
            if self.app.manager.update_service_notes(service_name, new_notes):
                self.refresh_services()
                popup.dismiss()
                self.app.show_notification('Заметки успешно обновлены', 'green')
            else:
                self.app.show_notification('Не удалось обновить заметки', 'red')
        save_btn = GreenButton(text='Сохранить')
        save_btn.bind(on_press=save_notes)
        cancel_btn = GrayButton(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = DarkPopup(title='Изменение заметок', content=content, size_hint=(0.9, 0.5))
        popup.open()

    def show_delete_service(self, service_name):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text='Подтверждение удаления', font_size='18sp',
                                 color=(1, 1, 1, 1), bold=True))
        content.add_widget(Label(text='Вы уверены, что хотите удалить сервис:',
                                 color=(1, 1, 1, 1), font_size='14sp'))
        content.add_widget(Label(text=service_name, font_size='16sp',
                                 color=get_color_from_hex('#FF5252'), bold=True))
        content.add_widget(Label(text='Для подтверждения введите мастер-пароль:',
                                 color=(1, 1, 1, 1), font_size='14sp'))
        password_input = TextInput(password=True, multiline=False, size_hint_y=None, height=dp(45),
                                   foreground_color=(1, 1, 1, 1),
                                   background_color=get_color_from_hex('#555555'),
                                   padding=dp(10), font_size='14sp')
        content.add_widget(password_input)
        buttons = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))

        def delete_service(btn):
            pw = password_input.text
            if not pw:
                self.app.show_notification('Введите пароль', 'red')
                return
            if pw != self.app.manager.master_password:
                self.app.show_notification('Неверный пароль', 'red')
                return
            if self.app.manager.delete_service(service_name):
                self.refresh_services()
                popup.dismiss()
                self.app.show_notification('Сервис успешно удален', 'green')
            else:
                self.app.show_notification('Не удалось удалить сервис', 'red')
        delete_btn = RedButton(text='Удалить')
        delete_btn.bind(on_press=delete_service)
        cancel_btn = GrayButton(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(delete_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = DarkPopup(title='Удаление сервиса', content=content, size_hint=(0.9, 0.6))
        popup.open()

    # ---------- Действия с паролем ----------
    def generate_pending_password(self, service_name):
        new_pw = self.app.manager.generate_pending_password(service_name)
        if new_pw:
            Clipboard.copy(new_pw)
            self.show_service_details(service_name)
            self.app.show_notification(
                'Пароль скопирован в буфер обмена. Вставьте его на сайте, затем нажмите "Подтвердить смену".',
                'blue', duration=5
            )
        else:
            self.app.show_notification('Не удалось сгенерировать пароль', 'red')

    def confirm_password_change(self, service_name):
        if self.app.manager.confirm_password_change(service_name):
            self.refresh_services()
            self.show_service_details(service_name)
            self.app.show_notification('Пароль успешно обновлён', 'green')
        else:
            self.app.show_notification('Не удалось подтвердить смену', 'red')

    def cancel_password_change(self, service_name):
        self.app.manager.cancel_password_change(service_name)
        self.refresh_services()
        self.show_service_details(service_name)
        self.app.show_notification('Смена пароля отменена', 'orange')

    def set_manual_password(self, service_name):
        manual_pw = self.manual_password_input.text.strip()
        if not manual_pw:
            self.app.show_notification('Введите пароль', 'red')
            return
        new_pw = self.app.manager.generate_pending_password(service_name, custom_password=manual_pw)
        if new_pw:
            self.manual_password_input.text = ''
            self.show_service_details(service_name)
            self.app.show_notification(
                'Пароль установлен как временный. Подтвердите или отмените смену.',
                'blue'
            )
        else:
            self.app.show_notification('Не удалось установить пароль', 'red')

    def show_password_history(self, service_name):
        history = self.app.manager.get_service_history(service_name)
        if not history:
            self.app.show_notification('История паролей пуста', 'orange')
            return

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        scroll = ScrollView(size_hint=(1, 0.9))
        list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        list_layout.bind(minimum_height=list_layout.setter('height'))
        for entry in reversed(history):
            dt = datetime.fromisoformat(entry['changed_at']).strftime("%d.%m.%Y %H:%M")
            password = entry['password']
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(5))
            row.add_widget(Label(text=dt, size_hint_x=0.4, color=(1, 1, 1, 1)))
            pw_label = Label(text='*' * min(len(password), 10), size_hint_x=0.3, color=(1, 1, 1, 1))
            row.add_widget(pw_label)
            show_btn = BlueButton(text='👁', size_hint_x=0.15, height=dp(30))
            copy_btn = BlueButton(text='📋', size_hint_x=0.15, height=dp(30))

            show_flag = [False]
            def toggle_show(lbl=pw_label, pw=password, flag=show_flag):
                if flag[0]:
                    lbl.text = '*' * min(len(pw), 10)
                    flag[0] = False
                else:
                    lbl.text = pw
                    flag[0] = True
            show_btn.bind(on_press=lambda x: toggle_show())

            def copy_pw(pw=password):
                Clipboard.copy(pw)
                self.app.show_notification('Пароль скопирован', 'green')
            copy_btn.bind(on_press=lambda x: copy_pw())

            row.add_widget(show_btn)
            row.add_widget(copy_btn)
            list_layout.add_widget(row)

        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        close_btn = GrayButton(text='Закрыть', size_hint=(1, None), height=dp(40))
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)

        popup = DarkPopup(title=f'История паролей: {service_name}', content=content,
                          size_hint=(0.9, 0.7))
        popup.open()

    def show_sync_info(self, instance):
        status_text, status_color = self.app.manager.get_sync_status()
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=status_text, color=(1, 1, 1, 1), font_size='14sp'))

        if self.app.manager.has_internet and self.app.manager.token_valid:
            sync_btn = GreenButton(text='Синхронизировать сейчас', size_hint=(1, None), height=dp(45))
            def sync_now(btn):
                if self.app.manager.upload_if_modified():
                    self.app.show_notification('Данные синхронизированы', 'green')
                else:
                    self.app.show_notification('Не удалось синхронизировать', 'red')
                popup.dismiss()
            sync_btn.bind(on_press=sync_now)
            content.add_widget(sync_btn)

        ok_btn = GrayButton(text='OK', size_hint=(1, None), height=dp(45))
        ok_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(ok_btn)

        popup = DarkPopup(title='Синхронизация', content=content, size_hint=(0.8, 0.4))
        popup.open()