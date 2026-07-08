import tkinter as tk
from tkinter import ttk

def center_window(window, width=900, height=600):
    """Центрирует окно на экране"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_error(parent, message):
    """Показывает сообщение об ошибке через всплывающее окно (если уведомления не работают)"""
    # Для единообразия можно использовать messagebox, но мы будем использовать встроенные уведомления
    # Этот метод можно задействовать, если уведомления недоступны
    from tkinter import messagebox
    messagebox.showerror("Ошибка", message)

def get_treeview_selected(tree):
    """Возвращает имя сервиса, выбранного в Treeview, или None"""
    selected = tree.selection()
    if selected:
        return tree.item(selected[0], 'values')[0]
    return None