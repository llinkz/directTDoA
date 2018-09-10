#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import os
import sys
import subprocess
from subprocess import PIPE


class SnrProcessing(threading.Thread):  # work in progress
    def __init__(self, parent=None):
        super(SnrProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global proc3, snrfreq
        proc3 = subprocess.Popen(
            [sys.executable, 'microkiwi_waterfall.py', '--file=wf.bin', '-z', '8', '-o', str(snrfreq), '-s',
             str(snrhost)], stdout=PIPE, shell=False)
        while True:
            line3 = proc3.stdout.readline()
            if "bytes" in line3:
                print line3.rstrip()
                os.kill(proc3.pid)
                pass
