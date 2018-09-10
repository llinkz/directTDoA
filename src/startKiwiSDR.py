#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
from subprocess import PIPE
import threading
import sys

class StartKiwiSDR(threading.Thread):

    def __init__(self, parent=None):
        super(StartKiwiSDR, self).__init__()
        self.parent = parent

    def run(self):
        global hostlisting, namelisting, frequency, portlisting, lpcut, hpcut, proc2_pid
        global parent, line, nbfile, IQfiles, t, varfile
        IQfiles = []
        line = []
        nbfile = 1
        t = 0
        proc2 = subprocess.Popen(
            [sys.executable, 'kiwirecorder.py', '-s', str(hostlisting), '-p', str(portlisting), str(namelisting), '-f',
             str(frequency), '-L', str(0 - lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False,
            preexec_fn=os.setsid)
        proc2_pid = proc2.pid
        self.parent.writelog("IQ Recordings in progress...please wait")
        #self.parent.writelog('kiwirecorder.py -s ' + str(hostlisting) + ' -p ' + str(portlisting) + ' ' + str(
        #    namelisting) + ' -f ' + str(frequency) + ' -L ' + str(0 - lpcut) + ' -H ' + str(hpcut) + ' -m iq -w')
        # debug