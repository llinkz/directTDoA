#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import Tk
from tkinter import DoubleVar
from src.zoomAdvanced import ZoomAdvanced
from src.mainWindow import MainWindow

VERSION = "directTDoA v3.00 by linkz"

class MainW(Tk, object):

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.checkfilesize = ""
        self.line = ""
        self.i = 0
        self.latmin = ""
        self.latmax = ""
        self.lonmin = ""
        self.lonmax = ""
        self.bbox1 = ""
        
        self.frequency = DoubleVar(self, 10000.0)
        self.bgc = '#d9d9d9'  # GUI background color
        self.fgc = '#000000'  # GUI foreground color
        self.dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        self.lpcut = 5000  # default low pass filter
        self.hpcut = 5000  # default high pass filter
        self.lat_min_map = ""
        self.lat_max_map = ""
        self.lon_min_map = ""
        self.lon_max_map = ""
        self.selectedlat = ""
        self.selectedlon = ""
        self.selectedcity = ""
        self.map_preset = 0
        self.map_manual = 0

        self.window = ZoomAdvanced(self)
        self.window2 = MainWindow(self)


if __name__ == '__main__':
    app = MainW()
    app.VERSION = VERSION
    app.title(VERSION)
    app.mainloop()
