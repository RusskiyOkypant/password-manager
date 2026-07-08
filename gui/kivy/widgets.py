from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.clipboard import Clipboard
from kivy.utils import get_color_from_hex


class MultiLineButton(Button):
    """Кнопка с многострочным текстом и автоматической высотой"""
    text = StringProperty('')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = 'center'
        self.valign = 'middle'
        self.text_size = (self.width, None)
        self.bind(size=self._update_text_size)
        self.bind(text=self._update_text_size)
        Clock.schedule_once(self._initial_adjustment, 0.1)

    def _initial_adjustment(self, dt):
        if self.text:
            self.text_size = (self.width - dp(20), None)
            self.height = max(dp(60), len(self.text.split('\n')) * dp(20) + dp(20))

    def _update_text_size(self, *args):
        if self.text and self.width > 0:
            Clock.schedule_once(lambda dt: self._do_update(), 0)

    def _do_update(self):
        if self.text and self.width > 0:
            self.text_size = (self.width - dp(20), None)
            required_height = max(dp(60), len(self.text.split('\n')) * dp(20) + dp(20))
            if abs(self.height - required_height) > 1:
                self.height = required_height


class ServiceButton(MultiLineButton):
    """Кнопка для отображения сервиса в списке"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.color = (0, 0, 0, 1)
        self.background_color = (0.95, 0.95, 0.95, 1)
        self.font_size = '13sp'
        self.padding = (dp(5), dp(5))
        self.halign = 'left'

    def _do_update(self):
        if self.text and self.width > 0:
            self.text_size = (self.width - dp(20), None)
            self.height = dp(80)


class GreenButton(MultiLineButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = get_color_from_hex('#4CAF50')
        self.color = (1, 1, 1, 1)
        self.font_size = kwargs.get('font_size', '14sp')


class BlueButton(MultiLineButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = get_color_from_hex('#2196F3')
        self.color = (1, 1, 1, 1)
        self.font_size = kwargs.get('font_size', '14sp')


class RedButton(MultiLineButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = get_color_from_hex('#F44336')
        self.color = (1, 1, 1, 1)
        self.font_size = kwargs.get('font_size', '14sp')


class GrayButton(MultiLineButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = get_color_from_hex('#9E9E9E')
        self.color = (1, 1, 1, 1)
        self.font_size = kwargs.get('font_size', '14sp')


class DarkPopup(Popup):
    """Всплывающее окно с тёмным фоном и белым текстом"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex('#333333')
        self.title_color = (1, 1, 1, 1)
        self.separator_color = get_color_from_hex('#555555')


class NotificationPopup(Popup):
    """Всплывающее уведомление (автоматически закрывается через заданное время)"""
    def __init__(self, message, color='green', duration=2, **kwargs):
        super().__init__(**kwargs)
        self.title = ''
        self.background_color = get_color_from_hex('#333333')
        self.size_hint = (0.8, 0.3)
        self.auto_dismiss = False

        # Определяем цвет текста и фона
        colors = {
            'green': ('#4CAF50', 'white'),
            'red': ('#F44336', 'white'),
            'orange': ('#FF9800', 'black'),
            'yellow': ('#FFEB3B', 'black'),
            'blue': ('#2196F3', 'white')
        }
        bg_color, text_color = colors.get(color, ('#4CAF50', 'white'))

        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        label = Label(text=message, color=get_color_from_hex(text_color), font_size='14sp')
        layout.add_widget(label)

        self.content = layout
        Clock.schedule_once(lambda dt: self.dismiss(), duration)

    def dismiss(self):
        super().dismiss()