#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import platform
import subprocess
import os
from processFinished import ProcessFinished

class OctaveProcessing(threading.Thread):
    def __init__(self, parent=None):
        super(OctaveProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global varfile, tdoa_position, bad_node, stdout, proc_pid
        tdoa_filename = "proc_tdoa_" + varfile + ".m"
        bad_node = False
        if platform.system() == "Windows":  # not working
            exec_octave = 'C:\Octave\Octave-4.2.1\octave.vbs --no-gui'
            # tdoa_filename = 'C:\Users\linkz\Desktop\TDoA-master-win\\' + tdoa_filename  # work in progress for Windows
        if platform.system() == "Linux" or platform.system() == "Darwin":
            exec_octave = 'octave'
        proc = subprocess.Popen([exec_octave, tdoa_filename], cwd=os.path.join('TDoA'), stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, shell=False , preexec_fn=os.setsid)
        proc_pid = proc.pid
        logfile = open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
            frequency) + os.sep + "TDoA_" + varfile + "_log.txt", 'w')
        for line in proc.stdout:
            # sys.stdout.write(line)
            logfile.write(line)
            if "most likely position:" in line:
                tdoa_position = line
            if "finished" in line:
                logfile.close()
                ProcessFinished(self).start()
                proc.terminate()
        proc.wait()
