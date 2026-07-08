#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Точка входа для Tkinter версии менеджера паролей.
Запуск: python run_tkinter.py
"""

from gui.tkinter.app import TkinterApp

if __name__ == "__main__":
    app = TkinterApp()
    app.run()