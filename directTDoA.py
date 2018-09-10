#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import Tk

from src.zoomAdvanced import ZoomAdvanced
from src.mainWindow import MainWindow

VERSION = "directTDoA v3.00 by linkz"

class MainW(Tk, object):

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.window = ZoomAdvanced(self)
        self.window2 = MainWindow(self)


if __name__ == '__main__':
    app = MainW()
    app.title(VERSION)
    app.mainloop()
