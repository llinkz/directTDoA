#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import glob
import time
import threading

class CheckFileSize(threading.Thread):
    def __init__(self, parent=None):
        super(CheckFileSize, self).__init__()
        self.parent = parent

    def run(self):
        global t, checkfilesize
        checkfilesize = 1
        while t == 0:
            time.sleep(0.5)  # file size measurement refresh rate
            for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                self.parent.writelog2(
                    wavfiles.rsplit(os.sep, 1)[1] + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
            t = 0
