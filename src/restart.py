#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from Tkinter import sys
import signal


class Restart:

    @staticmethod
    def run():
        global proc_pid, proc2_pid
        try:  # ...to kill octave
            os.killpg(os.getpgid(proc_pid), signal.SIGKILL)
            # os.kill(proc_pid, signal.SIGKILL)
        except:
            pass
        try:  # to kill kiwirecorder.py
            os.killpg(os.getpgid(proc2_pid), signal.SIGKILL)
            # os.kill(proc2_pid, signal.SIGKILL)
        except:
            pass
        # restart directTDoA.py
        os.execv(sys.executable, [sys.executable] + sys.argv)

