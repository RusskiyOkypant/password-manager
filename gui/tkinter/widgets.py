import tkinter as tk
from tkinter import ttk

class NotificationFrame:
    def __init__(self, parent, bg='white', fg='black', font=('Arial', 10)):
        self.parent = parent
        self._after_id = None
        self.frame = tk.Frame(parent, height=30, bg=bg)
        self.label = tk.Label(self.frame, text="", font=font, bg=bg, fg=fg)
        self.label.pack(fill=tk.BOTH, expand=True)
        self.frame.place_forget()

    def show(self, text, bg='#4CAF50', fg='white', duration=3000):
        self.frame.config(bg=bg)
        self.label.config(text=text, bg=bg, fg=fg)
        self.frame.place(relx=0.5, rely=1.0, anchor='s', relwidth=1.0, y=-5)
        self.frame.lift()
        if self._after_id:
            self.parent.after_cancel(self._after_id)
        self._after_id = self.parent.after(duration, self.hide)

    def hide(self):
        self.frame.place_forget()
        if self._after_id:
            self.parent.after_cancel(self._after_id)
            self._after_id = None


# ---------- Кастомные кнопки ----------
class BaseButton(ttk.Button):
    def __init__(self, parent, text, bg_color, fg_color='white', **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self.style = ttk.Style()
        style_name = f"{self.__class__.__name__}.TButton"
        self.style.configure(style_name, background=bg_color, foreground=fg_color,
                             font=('Arial', 10), padding=6)
        self.style.map(style_name, background=[('active', '#555555')])
        self.configure(style=style_name)

class GreenButton(BaseButton):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text, '#4CAF50', **kwargs)

class BlueButton(BaseButton):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text, '#2196F3', **kwargs)

class RedButton(BaseButton):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text, '#F44336', **kwargs)

class GrayButton(BaseButton):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text, '#9E9E9E', **kwargs)