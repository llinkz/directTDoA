#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import os
import tkMessageBox
import webbrowser
from shutil import copyfile
from restart import Restart

class ProcessFinished(threading.Thread):
    def __init__(self, parent=None):
        super(ProcessFinished, self).__init__()
        self.parent = parent

    def run(self):
        global tdoa_position, varfile
        llon = tdoa_position.rsplit(' ')[5]  # the longitude value returned by Octave process (without letters)
        llat = tdoa_position.rsplit(' ')[10] # the latitude value returned by Octave process (without letters)

        if "-" in llat:  # adding the latitude letter "N" or "S"
            sign1 = "S"
            llat = llat[1:]  # removing the latitude minus sign
        else:
            sign1 = "N"
        if "-" in llon:  # adding the longitude letter "W" or "E"
            sign2 = "W"
            llon = llon[1:]  # removing the longitude minus sign
        else:
            sign2 = "E"
        #  llat + sign1 is now LATITUDE GPS decimal w/o the minus sign but with letter
        #  llon + sign2 is now LONGITUDE GPS decimal w/o the minus sign but with letter

        #  process to convert GPS decimal to DMS (for geohack website url arguments)
        mnt2, sec2 = divmod(float(llon) * 3600, 60)
        deg2, mnt2 = divmod(mnt2, 60)
        mnt1, sec1 = divmod(float(llat) * 3600, 60)
        deg1, mnt1 = divmod(int(mnt1), 60)
        latstring = str(int(deg1)) + "_" + str(int(mnt1)) + "_" + str(int(sec1)) + "_" + sign1  # geohack url lat arg
        lonstring = str(int(deg2)) + "_" + str(int(mnt2)) + "_" + str(int(sec2)) + "_" + sign2  # geohack url lon arg
        #  backup the .pdf file and saving most likely coords as text in previously created /iq/... dir
        copyfile(os.path.join('TDoA', 'pdf') + os.sep + "TDoA_" + varfile + ".pdf",
                 os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                     frequency) + os.sep + "TDoA_" + varfile + ".pdf")
        with open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                frequency) + os.sep + "TDoA_" + varfile + "_found " + llat + sign1 + " " + llon + sign2, 'w') as tdoa_file:
            tdoa_file.write("https://tools.wmflabs.org/geohack/geohack.php?params=" + latstring + "_" + lonstring)
        tdoa_file.close()
        # last popup window shown at end of process
        finish = tkMessageBox.askyesno(title="TDoA process just finished.",
                                       message="Most likely location coords are " + llat + "°" + sign1 + " " + llon + "°" + sign2 + "\n\nClick Yes to open \"Geohack\" webpage centered on most likely point found by the process\nClick No to open files directory and restart GUI")
        if finish:  # opens a web browser with geohack url containing most likely point coordinates & restart GUI
            webbrowser.open_new("https://tools.wmflabs.org/geohack/geohack.php?params=" + latstring + "_" + lonstring)
        elif finish is False:  # opens directory that containing TDoA files & restart GUI
            webbrowser.open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(frequency))
        Restart().run()
