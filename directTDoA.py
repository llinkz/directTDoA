#!/usr/bin/python
# -*- coding: utf-8 -*-

<<<<<<< HEAD
from Tkinter import *
import tkSimpleDialog, codecs, unicodedata, tkFileDialog
import threading, os, signal, subprocess, platform, tkMessageBox, time, re, glob, webbrowser, json, requests
from subprocess import PIPE
from PIL import Image, ImageTk
from shutil import copyfile
from tkColorChooser import askcolor
from datetime import datetime

VERSION = "directTDoA v4.20"


class Restart:

    @staticmethod
    def run():
        global proc_pid, proc2_pid
        try:  # to kill octave-cli process if exists
            os.kill(proc_pid, signal.SIGTERM)
        except:
            pass
        try:  # to kill kiwirecorder.py process if exists
            os.kill(proc2_pid, signal.SIGTERM)
        except:
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)  # restart directTDoA.py


class ReadKnownPointFile:

    @staticmethod
    def run():
        with open('directTDoA_knownpoints.db') as h:
            global my_info1, my_info2, my_info3
            i = 3  # skip the directTDoA_knownpoints.db comment lines at start
            lines = h.readlines()
            my_info1 = []
            my_info2 = []
            my_info3 = []
            while i < sum(1 for _ in open('directTDoA_knownpoints.db')):
                line = lines[i]
                inforegexp = re.search(r"(.*),(.*),(.*)", line)
                my_info1.append(inforegexp.group(1))
                my_info2.append(inforegexp.group(2))
                my_info3.append(inforegexp.group(3))
                i += 1
        h.close()


class CheckFileSize(threading.Thread):
    def __init__(self):
        super(CheckFileSize, self).__init__()

    def run(self):
        while True:
            for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                app.window2.Text3.insert('end -1 lines', wavfiles.rsplit(os.sep, 1)[1] + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB" + "\n")
            app.window2.Text3.see('end')
            time.sleep(0.5)
            app.window2.Text3.delete("0.0", END)


class ProcessFinished(threading.Thread):
    def __init__(self, parent=None):
        super(ProcessFinished, self).__init__()
        self.parent = parent

    def run(self):
        global tdoa_position, varfile, proc_pid, tdoa_in_progress
        llon = tdoa_position.rsplit(' ')[10]  # the longitude value returned by Octave process (without letters)
        llat = tdoa_position.rsplit(' ')[5] # the latitude value returned by Octave process (without letters)

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
        #copyfile(os.path.join('TDoA', 'pdf') + os.sep + "TDoA_" + varfile + ".pdf",
        #         os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
        #             frequency) + os.sep + "TDoA_" + varfile + ".pdf")
        with open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                frequency) + os.sep + "TDoA_" + varfile + "_found " + llat + sign1 + " " + llon + sign2, 'w') as tdoa_file:
            tdoa_file.write("https://tools.wmflabs.org/geohack/geohack.php?params=" + latstring + "_" + lonstring)
        tdoa_file.close()
        webbrowser.open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(frequency))
        app.window2.Button1.configure(state="normal", text="Start recording")
        app.window2.Button2.configure(state="disabled")
        app.window2.Button3.configure(state="normal")
        app.window2.Button4.configure(state="normal")
        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            os.remove(wavfiles)
        app.window2.Text3.delete("0.0", END)
        tdoa_in_progress = 0


class ReadConfigFile:
    def read_cfg(self):
        global dx0, dy0, dx1, dy1, dmap, mapfl, gpsfl, white, black, colorline, defaultbw
        with open('directTDoA.cfg', "r") as c:
            try:
                configline = c.readlines()
                dx0 = configline[3].split(',')[0]  # longitude min
                dy0 = configline[3].split(',')[1]  # latitude max
                dx1 = configline[3].split(',')[2]  # longitude max
                dy1 = configline[3].split(',')[3]  # latitude min
                dmap = configline[5].split('\n')[0]  # displayed map
                mapfl = configline[7].replace("\n", "").split(',')[0]  # map filter
                gpsfl = configline[7].replace("\n", "").split(',')[1]  # GPS/min filter
                white = configline[9].replace("\n", "").split(',')  # nodes whitelist
                black = configline[11].replace("\n", "").split(',')  # nodes blacklist
                colorline = configline[13].replace("\n", "").split(',')  # GUI map colors
                defaultbw = configline[15].replace("\n", "")  # default IQ rec bandwidth
            except:
                copyfile("directTDoA.cfg", "directTDoA.cfg.bak")
                sys.exit(
                    "Oops, something is wrong with the directTDoA.cfg config file format\nIf you have just updated, make sure all the required lines are present.\nYou can keep your directTDoA.cfg file and add the missing lines manually in order to keep your settings intact.\nCheck https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg for a sample.\nNote: a backup copy of your config file has been created as directTDoA.cfg.bak")
        c.close()


class SaveConfigFile:
    def save_cfg(self, field, input):
        global dmap, mapfl, gpsfl, white, black, colorline, defaultbw
        with open('directTDoA.cfg', "w") as u:
            u.write("This is " + VERSION + " config file\n")
            u.write("This file should be generated by directTDoA software only, in case something went wrong you can find a sample here: https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg\n")
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            if field == "mapc":
                u.write("# Default map picture \n%s\n" % input)
            else:
                u.write("# Default map picture \n%s\n" % dmap)
            if field == "mapfl":
                u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (input, gpsfl))
            elif field == "gpsfl":
                u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (mapfl, input))
            else:
                u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (mapfl, gpsfl))
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            if field == "nodecolor":
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % input)
            else:
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            if field == "defaultbw":
                u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % input)
            else:
                u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % defaultbw)
        u.close()


class CheckUpdate(threading.Thread):
    def __init__(self, parent=None):
        super(CheckUpdate, self).__init__()
        self.parent = parent

    def run(self):
        pierre_is_ok = "no"
        marco_is_ok = "no"
        try:
            checklinkfanel = requests.get("http://rx.linkfanel.net/kiwisdr_com.js", timeout=1)
            if checklinkfanel.status_code == 200:
                pierre_is_ok = "yes"
        except:
            pass
        try:
            checkmarco = requests.get("http://sibamanna.duckdns.org/snrmap_4bands.json", timeout=1)
            if checkmarco.status_code == 200:
                marco_is_ok = "yes"
        except:
            pass
        if pierre_is_ok == "no" and marco_is_ok == "yes" :
            print "Pierre's website is not reachable. Node listing update is not possible, try later."
        elif pierre_is_ok == "yes" and marco_is_ok == "no" :
            print "Marco's website is not reachable. Node listing update is not possible, try later."
        elif pierre_is_ok == "no" and marco_is_ok == "no" :
            print "Both Marco's & Pierre's websites are not reachable. Node listing update is not possible, try later."
        else :
            RunUpdate().run()


class RunUpdate(threading.Thread):
    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        try:
            nodelist = requests.get("http://rx.linkfanel.net/kiwisdr_com.js")  # getting the full KiwiSDR node list
            json_data = json.loads(nodelist.text[nodelist.text.find('['):].replace('},\n]\n;\n', '}]'))
            # Important info concerning UPDATE FAIL errors:
            # Sometimes some nodes datas are incompletely returned to kiwisdr.com/public so below is a dirty way to
            # bypass them, using their mac address.
            # ATM mac should be manually found in http://rx.linkfanel.net/kiwisdr_com.js webpage source code, search
            # using the line number returned by the update FAIL error text, will try to fix one day ....
            # json_data = json.loads(nodelist.text[nodelist.text.find('['):].replace('},\n]\n;\n', '}]').replace('985dad7f54fc\",','985dad7f54fc\"'))
            #json_data = json.loads(nodelist.text)  # when kiwisdr_com.js will be in real json format
            snrlist = requests.get("http://sibamanna.duckdns.org/snrmap_4bands.json")
            json_data2 = json.loads(snrlist.text)
            try:
                linkz_status = requests.get("http://linkz.ddns.net:8073/status", timeout=3)
                s_fix = re.search('fixes_min=(.*)', linkz_status.text)
                l_fixes = s_fix.group(1)
            except:
                l_fixes = 0
                pass
            if os.path.isfile('directTDoA_server_list.db') is True:
                os.remove('directTDoA_server_list.db')
            with codecs.open('directTDoA_server_list.db', 'w', encoding='utf8') as g:
                g.write("[\n")
                for i in range(len(json_data)):  # parse all nodes from linkfanel website / json db
                    if '20 kHz' not in json_data[i]['sdr_hw'] and 'GPS' in json_data[i]['sdr_hw']:  # parse GPS nodes
                        for index, element in enumerate(json_data2['features']):  # check IS0KYB db
                            if json_data[i]['id'] in json.dumps(json_data2['features'][index]):
                                if json_data[i]['tdoa_id'] == '':
                                    node_id = json_data[i]['url'].split('//', 1)[1].split(':', 1)[0].replace(".", "").replace("-", "").replace("proxykiwisdrcom", "").replace("ddnsnet", "")
                                    try:
                                        ipfield = re.search(
                                            r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b',
                                            json_data[i]['url'].split('//', 1)[1].split(':', 1)[0])
                                        node_id = "ip" + str(ipfield.group(1)).replace(".", "")
                                    except:
                                        pass
                                    try:
                                        hamcallfield = re.search(r"(.*)(\s|,|\/|^)([A-Za-z]{1,2}[0-9][A-Za-z]{1,3})(\s|,|\/|\@|\-)(.*)", json_data[i]['name'])
                                        node_id = hamcallfield.group(3).upper()
                                    except:
                                        pass
                                else:
                                    node_id = json_data[i]['tdoa_id']
                                try:
                                    gpsfield = re.search(
                                        r"([-+]?[0-9]{1,2}(\.[0-9]*)?)(,| ) ?([-+]?[0-9]{1,3}(\.[0-9]*))?", json_data[i]['gps'][1:-1])
                                    nodelat = gpsfield.group(1)
                                    nodelon = gpsfield.group(4)
                                except:
                                    # Admins not respecting KiwiSDR admin page GPS field format (nn.nnnnnn, nn.nnnnnn)
                                    # => nodes will be shown at top-right map edge, as it fails the update code process
                                    print "*** Error reading <gps> field : >> " + str(unicodedata.normalize("NFKD", json_data[i]['gps'][1:-1]).encode("ascii", "ignore")) + " << for \"" + unicodedata.normalize("NFKD", json_data[i]["name"]).encode("ascii", "ignore") + "\""
                                    print "*** This node will be displayed at 90N 180E position and is not usable for TDoA"
                                    nodelat = "90"
                                    nodelon = "180"
                                # (-?(90[:°d] * 00[:\'\'m]*00(\.0+)?|[0-8][0-9][ :°d]*[0-5][0-9][ :\'\'m]*[0-5][0-9](\.\d+)?)[ :\?\"s]*(N|n|S|s)?)[ ,]*(-?(180[ :°d]*00[ :\'\'m]*00(\.0+)?|(1[0-7][0-9]|0[0-9][0-9])[ :°d]*[0-5][0-9][ :\'\'m]*[0-5][0-9](\.\d+)?)[ :\?\"s]*(E|e|W|w)?)
                                g.write(' { \"mac\":\"' + json_data[i]['id'] + '\", \"url\":\"' + json_data[i]['url'].split('//', 1)[1] + '\", \"gps\":\"' + json_data[i]['fixes_min'] + '\", \"id\":\"' + node_id + '\", \"lat\":\"' + nodelat + '\", \"lon\":\"' + nodelon + '\", \"name\":\"' + unicodedata.normalize("NFKD", json_data[i]["name"]).encode("ascii", "ignore").replace("\"", "") + '\", \"users\":\"' + json_data[i]['users'] + '\", \"usersmax\":\"' + json_data[i]['users_max'] + '\", \"snr1\":\"' + str(element['properties']['snr1_avg']) + '\", \"snr2\":\"' + str(element['properties']['snr2_avg']) + '\", \"snr3\":\"' + str(element['properties']['snr3_avg']) + '\", \"snr4\":\"' + str(element['properties']['snr4_avg']) + '\", \"nlvl1\":\"' + str(element['properties']['bg1_avg']) + '\", \"nlvl2\":\"' + str(element['properties']['bg2_avg']) + '\", \"nlvl3\":\"' + str(element['properties']['bg3_avg']) + '\", \"nlvl4\":\"' + str(element['properties']['bg4_avg']) + '\"},\n')
                            else:
                                pass
                    else:
                        pass
                # here is the hardcode for my own KiwiSDR, it will soon include real SNR/noise values.. thx Marco
                g.write(' { "mac":"04a316df1bca", "url":"linkz.ddns.net:8073", "gps":"' + str(l_fixes) + '", "id":"linkz", "lat":"45.4", "lon":"5.3", "name":"directTDoA GUI developer, French Alps", "users":"0", "usersmax":"4", "snr1":"0", "snr2":"0", "snr3":"0", "snr4":"0", "nlvl1":"0", "nlvl2":"0", "nlvl3":"0", "nlvl4":"0"}\n]')
                g.close()
                # normally if update process is ok, we can make a backup copy of the server listing
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
                Restart().run()
        except Exception as e:
            print e
            print "UPDATE FAIL, sorry"
=======
import Tkinter as tk
import Tkinter as ttk
from Tkinter import *
import ttk
import threading
import os
import signal
import subprocess
from subprocess import PIPE
import platform
from os.path import dirname, abspath
from PIL import Image, ImageTk
import tkMessageBox
import time
import urllib2
import re
import glob
from shutil import copyfile
import webbrowser


VERSION = "directTDoA v2.20 by linkz"


class RunUpdate(threading.Thread):

    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        global kiwi_nodenumber, kiwi_errors, kiwi_update, kiwi_names, kiwi_users, kiwi_users_max, kiwi_coords
        global kiwi_loc, kiwi_sw_version, kiwi_antenna, kiwi_uptime, kiwi_hostname, kiwi_id, kiwi_lat, kiwi_lon
        global addme
        try:
            webpage = urllib2.urlopen("http://kiwisdr.com/public/")  # get the server infos page
            datatowrite = webpage.read()
            with open("kiwisdr.com_public_TDoA.htm", 'wb') as w:
                w.write(datatowrite) # dl listing source
            kiwi_nodenumber = 0; kiwi_errors = 0
            kiwi_id = []; kiwi_sdr_hw = []; kiwi_lat = []; kiwi_lon = []
            kiwi_update = []; kiwi_names = []; kiwi_users = []; kiwi_users_max = []; kiwi_loc = []
            kiwi_sw_version = []; kiwi_antenna = []; kiwi_uptime = []; kiwi_hostname = []
            addme = 1
            with open('kiwisdr.com_public_TDoA.htm', "r") as f:
                for line in f:  # parse the listing source html file, line after line, could be a better process, later
                    update = re.search(
                        r'(Monday, |Tuesday, |Wednesday, |Thursday, |Friday, |Saturday, |Sunday, )(.*) <br>', line)
                    id = re.search(r'<!-- id=(.*) -->', line)
                    name = re.search(r'<!-- name=(.*) -->', line)
                    sdrhw = re.search(r'<!-- sdr_hw=(.*) -->', line)
                    users = re.search(r'<!-- users=(.*) -->', line)
                    users_max = re.search(r'<!-- users_max=(.*) -->', line)
                    coords = re.search(r'<!-- gps=\((\s?|\@)(\-?\d+\.?\d+)\D*,\s?(\-?\d+\.?\d+).* -->', line)
                    coords2 = re.search(r'<!-- gps=\((.*)N\s?(.*)E\) -->', line)
                    loc = re.search(r'<!-- loc=(.*) -->', line)
                    sw_version = re.search(r'<!-- sw_version=KiwiSDR_v(.*) -->', line)
                    antenna = re.search(r'<!-- antenna=(.*) -->', line)
                    uptime = re.search(r'<!-- uptime=(.*) -->', line)
                    hostname = re.search(r'<a href=\'http://(.*)\' .*', line)  # (?!:)
                    # starting to construct the lists
                    if update:
                        kiwi_update.append(update.group(2))

                    #  < !-- id = b0d5cc554471 -->
                    if id:
                        kiwi_id.append(id.group(1))
                        addme = 1

                    #    <!-- name=0-30MHz kiwiSDR BCL-LOOP13rev2.0 Hokushin Denshi KOBE JAPAN | -->
                    if name and addme == 1:
                        kiwi_names.append(
                            name.group(1).replace(".", "").replace(",", "").replace('"', '').replace("'", ""))
                    elif name is False:
                        kiwi_names.append('none')
                    #    <!-- sdr_hw=KiwiSDR v1.195 ⁣ 📡 GPS ⁣ -->

                    if sdrhw and addme == 1:
                        if "GPS" not in line:
                            kiwi_id.pop()
                            kiwi_names.pop()
                            addme = 0
                        else:
                            kiwi_sdr_hw.append("GPS")
                            addme = 1

                    if users and addme == 1:
                        kiwi_users.append(users.group(1))

                    if users_max and addme == 1:
                        kiwi_users_max.append(users_max.group(1))

                    if coords and addme == 1:
                        kiwi_lat.append(coords.group(2))
                        kiwi_lon.append(coords.group(3))

                    if coords2 and addme == 1:
                        kiwi_lat.append('34.761722')
                        kiwi_lon.append('135.171528')

                    if loc and addme == 1:
                        kiwi_loc.append(loc.group(1).decode('ascii', 'ignore').replace(".", "").replace(",", " "))
                    elif loc is False and addme == 1:
                        kiwi_loc.append('none')

                    if sw_version and addme == 1:
                        kiwi_sw_version.append(sw_version.group(1))

                    if antenna and addme == 1:
                        kiwi_antenna.append(
                            antenna.group(1).decode('ascii', 'ignore').replace(".", "").replace(",", " "))
                    elif antenna is False and addme == 1:
                        kiwi_antenna.append('none')

                    if uptime and addme == 1:
                        #a = int(datetime.timedelta(seconds=int(uptime.group(1))))
                        kiwi_uptime.append(uptime.group(1))

                    if hostname and addme == 1:
                        kiwi_hostname.append(hostname.group(1))
                    else:
                        pass
            f.close()
            os.remove('kiwisdr.com_public_TDoA.htm')
            if platform.system() == "Windows":
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
            if platform.system() == "Linux":
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
            os.remove('directTDoA_server_list.db')
            u = 0
            node_block = []
            with open('directTDoA_server_list.db', "w") as g:
                g.write("%s\n" % int(len(kiwi_id) + 1))
                while u < len(kiwi_id) :
                    node_block.append(kiwi_id[u])
                    node_block.append(kiwi_hostname[u])
                    node_block.append(kiwi_lat[u])
                    node_block.append(kiwi_lon[u])
                    node_block.append(kiwi_names[u].replace("\xe2\x80\xa2 ", "").replace("\xc2\xb3", "").replace("\xf0\x9f\x93\xbb", ""))
                    node_block.append(kiwi_users[u])
                    node_block.append(kiwi_users_max[u])
                    node_block.append(kiwi_sdr_hw[u])
                    #node_block.append(kiwi_loc[u])
                    #node_block.append(kiwi_antenna[u])
                    #node_block.append(kiwi_sw_version[u])
                    node_block.append(kiwi_uptime[u])

                    g.write("%s" % node_block)
                    g.write("\n")
                    u += 1
                    node_block = []
                mynode = "['ffffffffffff', 'linkz.ddns.net:8073', '45.5', '5.5', 'hf_linkz', '0', '4', 'GPS', '1']"
                g.write("%s" % mynode)
            g.close()
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)
        except urllib2.URLError, err:
            print "UPDATE FAIL, can't retrieve kiwisdr.com/public page"
            print str(err.reason)
>>>>>>> Add files via upload


class OctaveProcessing(threading.Thread):
    def __init__(self, parent=None):
        super(OctaveProcessing, self).__init__()
        self.parent = parent

    def run(self):
<<<<<<< HEAD
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


class SnrProcessing(threading.Thread):  # work in progress
=======
        global varfile
        tdoa_filename = "proc_tdoa_" + varfile + ".m"
        if platform.system() == "Windows":
            exec_octave = 'C:\Octave\Octave-4.2.1\octave.vbs --no-gui '
            tdoa_filename = 'C:\Users\linkz\Desktop\TDoA-master-win\\' + tdoa_filename
            print str(exec_octave) + str(tdoa_filename)
        if platform.system() == "Linux":
            exec_octave = '/usr/bin/octave-cli'
        proc = subprocess.Popen([exec_octave, tdoa_filename], cwd=dirname(dirname(abspath(__file__))), stdout=PIPE,
                                shell=False)
        while True:
            line = proc.stdout.readline()
            # name = re.search(r'^   (.*)   (.*)$', line)
            #  regexp:  ^   (.*)   (.*)$
            if line != '':
                # self.parent.writelog("OCTAVE full", line.rstrip())
                pass  # self.parent.writelog("Octave INFO", line.rstrip())
            if "iq/" in line:
                self.parent.writelog("processing " + line.rstrip())
            if "tdoa" in line:
                self.parent.writelog(line.rstrip())
            if "finished" in line:
                self.parent.writelog("processing finished, killing " + str(proc.pid) + " pid.")
                os.kill(proc.pid, signal.SIGKILL)
                executable = sys.executable
                args = sys.argv[:]
                args.insert(0, sys.executable)
                os.execvp(sys.executable, args)
                #os.kill(os.getpid(), signal.SIGKILL)


class SnrProcessing(threading.Thread):
>>>>>>> Add files via upload
    def __init__(self, parent=None):
        super(SnrProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global proc3, snrfreq
<<<<<<< HEAD
        proc3 = subprocess.Popen(
            [sys.executable, 'microkiwi_waterfall.py', '--file=wf.bin', '-z', '8', '-o', str(snrfreq), '-s',
             str(snrhost)], stdout=PIPE, shell=False)
=======
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux":
            execname = 'python2'
        proc3 = subprocess.Popen(
            [execname, 'microkiwi_waterfall.py', '--file=wf.bin', '-z', '8', '-o', str(snrfreq), '-s', str(snrhost)], stdout=PIPE, shell=False)
>>>>>>> Add files via upload
        while True:
            line3 = proc3.stdout.readline()
            if "bytes" in line3:
                print line3.rstrip()
                os.kill(proc3.pid)
                pass


class StartKiwiSDR(threading.Thread):
<<<<<<< HEAD
=======

>>>>>>> Add files via upload
    def __init__(self, parent=None):
        super(StartKiwiSDR, self).__init__()
        self.parent = parent

    def run(self):
<<<<<<< HEAD
        global frequency, lpcut, hpcut, proc2_pid
        global parent, line, IQfiles, varfile
        IQfiles = []
        line = []
        if (ultimate.get()) is 1:
            proc2 = subprocess.Popen(
                [sys.executable, 'kiwirecorder.py', '-s', ','.join(str(p).rsplit('$')[0] for p in ultimatelist), '-p',
                 ','.join(str(p).rsplit('$')[1] for p in ultimatelist),
                 '--station=' + ','.join(str(p).rsplit('$')[3] for p in ultimatelist), '-f', str(frequency), '-L',
                 str(0 - lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False, preexec_fn=os.setsid)
            self.parent.writelog("ultimateTDoA IQ Recordings in progress...please wait")
            self.parent.writelog('Command line: kiwirecorder.py -s ' + ','.join(
                str(p).rsplit('$')[0] for p in ultimatelist) + ' -p ' + ','.join(
                str(p).rsplit('$')[1] for p in ultimatelist) + ' -station=' + ','.join(
                str(p).rsplit('$')[3] for p in ultimatelist) + ' -f ' + str(frequency) + ' -L ' + str(
                0 - lpcut) + ' -H ' + str(hpcut) + ' -m iq -w')
        else:
            proc2 = subprocess.Popen(
            [sys.executable, 'kiwirecorder.py', '-s', ','.join(str(p).rsplit('$')[0] for p in fulllist), '-p',
             ','.join(str(p).rsplit('$')[1] for p in fulllist),
             '--station=' + ','.join(str(p).rsplit('$')[3] for p in fulllist), '-f', str(frequency), '-L',
             str(0 - lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False, preexec_fn=os.setsid)
            self.parent.writelog("IQ Recordings in progress...please wait")
            self.parent.writelog(
            'Command line: kiwirecorder.py -s ' + ','.join(str(p).rsplit('$')[0] for p in fulllist) + ' -p ' + ','.join(
                str(p).rsplit('$')[1] for p in fulllist) + ' -station=' + ','.join(
                str(p).rsplit('$')[3] for p in fulllist) + ' -f ' + str(frequency) + ' -L ' + str(
                0 - lpcut) + ' -H ' + str(hpcut) + ' -m iq -w')
        proc2_pid = proc2.pid


class StartKiwiSDRclient(threading.Thread):
    def __init__(self, parent=None):
        super(StartKiwiSDRclient, self).__init__()
        self.parent = parent

    def run(self):
        global parent, kiwisdrclient_pid, server_host, server_port, frequency, listenmode, dd
        try:
            #  '-g', '1', '50', '0', '-100', '6', '1000'  <==== static AGC settings
            #  1= AGC (on)  50=Manual Gain (dB) 0=Hang (off)  -100=Threshold (dB) 6=Slope (dB) 1000=Decay (ms)
            #  -L and -H are demod filters settings, values are override by kiwiSDRclient.py (BW=3600Hz)
            proc8 = subprocess.Popen(
                [sys.executable, 'KiwiSDRclient.py', '-s', str(server_host), '-p', str(server_port), '-f',
                 str(frequency), '-m', dd, '-L', '0', '-H', '5000', '-g', '1', '50', '0', '-100', '6', '1000'],
                stdout=PIPE, shell=False)
            kiwisdrclient_pid = proc8.pid
            listenmode = "1"
            app.window2.writelog("Starting Listen mode    [ " + server_host + " / " + frequency + " kHz / " + str(dd).upper() + " ]")
        except:
            print "error: unable to demodulate this node"
            listenmode = "0"


class FillMapWithNodes(threading.Thread):
=======
        global parent, line, nbfile, IQfiles, hostlisting, namelisting, frequency, portlisting, lpcut, hpcut, proc2, t
        IQfiles = []
        line = []
        nbfile = 1
        t = 0
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux":
            execname = 'python2'
        proc2 = subprocess.Popen(
            [execname, 'kiwirecorder.py', '-s', str(hostlisting), str(namelisting), '-f', str(frequency), '-p',
             str(portlisting), '-L', str(lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False)
        self.parent.writelog("IQ recording in progress...please wait")
        while proc2.pid is not None:
            time.sleep(1)
            if platform.system() == "Windows":
                for wavfiles in glob.glob("..\\iq\\*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("..\\iq\\", "")
                    self.parent.writelog2("~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0
            if platform.system() == "Linux":
                for wavfiles in glob.glob("../iq/*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("../iq/", "")
                    self.parent.writelog2("~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0

    def connectionfailed(self):
        print "connection failed."


class FillMapWithNodes(threading.Thread):

>>>>>>> Add files via upload
    def __init__(self, parent=None):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
<<<<<<< HEAD
        global manual_bound_x, manual_bound_y, manual_bound_xsize, manual_bound_ysize, map_preset, map_manual, nodecount
        if os.path.isfile('directTDoA_server_list.db') is True:
            with open('directTDoA_server_list.db') as f:
                db_data = json.load(f)
                nodecount = len(db_data)
                for i in range(nodecount):
                    try:
                        temp_snr_avg = (int(db_data[i]["snr1"]) + int(db_data[i]["snr2"]) + int(
                                db_data[i]["snr3"]) + int(db_data[i]["snr4"])) / 4
                        if db_data[i]["mac"] in white:    # favorite node color
                                node_color = (self.color_variant(colorline[1], (int(temp_snr_avg) - 45) * 5))
                        elif db_data[i]["mac"] in black:  # blacklist node color
                                node_color = (self.color_variant(colorline[2], (int(temp_snr_avg) - 45) * 5))
                        else:                             # standard node color
                                node_color = (self.color_variant(colorline[0], (int(temp_snr_avg) - 45) * 5))
                    except Exception as e:
                        pass
                    try:
                        if mapfl == "1" and db_data[i]["mac"] not in black:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "2" and db_data[i]["mac"] in white:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "3" and db_data[i]["mac"] in black:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "0":
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                    except Exception as e:
                        print e
                        pass
        self.parent.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map pos.
        self.parent.show_image()

    def convert_lat(self, lat):
        if float(lat) > 0:  # nodes are between LATITUDE 0 and 90N
            return 987.5 - (float(lat) * 11)
        else:  # nodes are between LATITUDE 0 and 60S
            return 987.5 + (float(0 - float(lat)) * 11)

    def convert_lon(self, lon):
        return (1907.5 + ((float(lon) * 1910) / 180))

    def color_variant(self, hex_color, brightness_offset=1):
        # source : https://chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join(["0" + hex(i)[2:] if len(hex(i)[2:]) < 2 else hex(i)[2:] for i in new_rgb_int])

    def add_point(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r):
        global gpsfl
        #  a   b    c    d   e   f   g    h     i     j   k    l    m    n    o   p   q   r
        # lon lat color host mac id name user usermx gps snr1 snr2 snr3 snr4 bg1 bg2 bg3 bg4
        if int(j) >= int(gpsfl):  # GPS/min filter
            try:
                self.parent.canvas.create_rectangle(float(b), float(a), float(b) + 5, float(a) + 5, fill=str(c),
                                                    outline="black", activefill='white', tag=str(
                        '$'.join(map(str, [d, e, f, g, h, i, j, k, l, m, n, o, p, q, r]))))
                self.parent.canvas.tag_bind(str('$'.join(map(str, [d, e, f, g, h, i, j, k, l, m, n, o, p, q, r]))),
                                            "<Button-1>", self.parent.onClick)
            except Exception as error_add_point:
                print error_add_point

    def deletePoint(self, n):  # city/site map point deletion process
        self.parent.canvas.delete(self.parent, n.rsplit(' (')[0])


class ZoomAdvanced(Frame):  # src stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 :)
    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        parent.geometry("1200x700+150+10")
        global dx0, dy0, dx1, dy1, listenmode, fulllist
        global dmap, host, white, black, mapfl, mapboundaries_set, ultimate, ultimatelist
        # host = Variable
        fulllist = []
        ultimatelist = []
        ReadConfigFile().read_cfg()
        listenmode = "0"
        mapboundaries_set = None
        self.x = self.y = 0
        # Create canvas and put image on it
        self.canvas = Canvas(self.master, highlightthickness=0)
=======
        time.sleep(0.5)
        with open('directTDoA_server_list.db') as h:
            global my_x_zeros, my_y_zeros, my_x_ones, my_y_ones, mycolor, my_host, my_tag, select
            i = 1
            lines = h.readlines()
            nbgpsnodes = lines[0]
            my_tag = []
            my_host = []
            my_lat = []
            my_lon = []
            my_name = []
            my_user = []
            my_usermx = []
            while i < (int(nbgpsnodes) + 1):
                line = lines[i]
                id = re.search(r"\['(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)'\]$", line)
                my_tag.append(id.group(1))
                my_host.append(id.group(2))
                my_lat.append(id.group(3))
                my_lon.append(id.group(4))
                my_name.append(id.group(5).replace(" ", "_"))
                my_user.append(id.group(6))
                my_usermx.append(id.group(7))
                i += 1
        h.close()
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            mapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        my_x_zeros = []
        my_y_zeros = []
        my_x_ones = []
        my_y_ones = []
        mycolor = []
        n = 0
        while n < len(my_tag):
            if float(my_lon[n]) > 0:  # nodes are between LONGITUDE 0 to +180
                my_x_zeros.append(1907.5 + ((float(my_lon[n]) * 1910) / 180))
                my_x_ones.append(my_x_zeros[n] + 5)
            else:  # nodes are between LONGITUDE -180 to 0
                my_x_zeros.append(1907.5 + ((float(my_lon[n]) * 1910) / 180))
                my_x_ones.append(my_x_zeros[n] + 5)
            if float(my_lat[n]) > 0:  # nodes are between LATITUDE 0 to +90
                my_y_zeros.append(987.5 - (float(my_lat[n]) * 11))
                my_y_ones.append(987.5 - (float(my_lat[n]) * 11) + 5)
            else:  # nodes are between LATITUDE 0 to -60
                my_y_zeros.append(987.5 + (float(0 - float(my_lat[n])) * 11))
                my_y_ones.append(987.5 + (float(0 - float(my_lat[n])) * 11) + 5)
            if (int(my_user[n])) / (int(my_usermx[n])) == 0:  # OK slots available on the node
                if my_tag[n] in white:  # if favorite  node color = white
                    mycolor.append('yellow')
                elif my_tag[n] in black:  # if blacklisted  node color = black
                    mycolor.append('black')
                else:
                    mycolor.append('green')  # if normal node color = green
            else:
                mycolor.append('red')  # if no slots, map point is always created red
            n += 1

        if mapfilter == "0":  # display all nodes
            m = 0
            while m < len(my_tag):
                self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                m += 1
        if mapfilter == "1":  # display standard + favorites
            m = 0
            while m < len(my_tag):
                if my_tag[m] not in black:
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                else:
                    pass
                m += 1
        if mapfilter == "2":  # display favorites only
            m = 0
            while m < len(my_tag):
                if my_tag[m] in white:
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                else:
                    pass
                m += 1
        if mapfilter == "3":  # display blacklisted only
            m = 0
            while m < len(my_tag):
                if my_tag[m] in black:
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                else:
                    pass
                m += 1
        self.parent.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map position
        self.parent.show_image()

    def deletePoint(self, n):  # city mappoint deletion process
        self.parent.canvas.delete(self.parent, n.rsplit(' (')[0])


class Zoom_Advanced(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        parent.geometry("1000x700+300+0")
        global dx0, dy0, dx1, dy1, serverlist, portlist, namelist, zoomlevel, map, host, white, black, mapfilter
        host = Variable
        serverlist = []
        portlist = []
        namelist = []
        zoomlevel = 1
        map = 'directTDoA_WORLD-wide.jpg'
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            map = configline[3].split('\n')[0]
            mapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        self.x = self.y = 0
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0)
>>>>>>> Add files via upload
        self.sbarv = Scrollbar(self, orient=VERTICAL)
        self.sbarh = Scrollbar(self, orient=HORIZONTAL)
        self.sbarv.config(command=self.canvas.yview)
        self.sbarh.config(command=self.canvas.xview)
        self.canvas.config(yscrollcommand=self.sbarv.set)
        self.canvas.config(xscrollcommand=self.sbarh.set)
        self.sbarv.grid(row=0, column=1, stick=N + S)
        self.sbarh.grid(row=1, column=0, sticky=E + W)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)  # map move
        self.canvas.bind('<B1-Motion>', self.move_to)  # map move
<<<<<<< HEAD
        #self.canvas.bind_all('<MouseWheel>', self.wheel)  # Windows Zoom disabled in this version !
        #self.canvas.bind('<Button-5>', self.wheel)  # Linux Zoom disabled in this version !
        #self.canvas.bind('<Button-4>', self.wheel)  # Linux Zoom disabled in this version !
        self.canvas.bind("<ButtonPress-3>", self.on_button_press)  # red rectangle selection
        self.canvas.bind("<B3-Motion>", self.on_move_press)  # red rectangle selection
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release)  # red rectangle selection
        self.image = Image.open(dmap)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the image
=======
        self.canvas.bind('<MouseWheel>', self.wheel)  # Windows Zoom disabled in this version !
        # self.canvas.bind('<Button-5>', self.wheel)  # Linux Zoom disabled in this version !
        # self.canvas.bind('<Button-4>', self.wheel)  # Linux Zoom disabled in this version !
        self.canvas.bind("<ButtonPress-3>", self.on_button_press)  # red rectangle selection
        self.canvas.bind("<B3-Motion>", self.on_move_press)  # red rectangle selection
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release)  # red rectangle selection
        # self.image = Image.open('directTDoA_WORLD-wide2.jpg')  # open image
        # self.image = Image.open('blackmarble-2016-3km-in-world-at-night-map3.jpg')  # open image
        self.image = Image.open(map)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
>>>>>>> Add files via upload
        self.delta = 2.0  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.rect = None
        self.start_x = None
        self.start_y = None
<<<<<<< HEAD
        self.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map pos.
        self.show_image()
        FillMapWithNodes(self).start()

    def displaySNR(self):  # work in progress
        pass

    def on_button_press(self, event):
        global map_preset, map_manual
        if map_preset == 1:
            self.deletePoint(sx0, sy0, "mappreset")
            self.rect = None
            map_preset = 0
=======
        FillMapWithNodes(self).start()

    def displaySNR(self):
        print host

    def on_button_press(self, event):
        # save mouse drag start position
>>>>>>> Add files via upload
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # create rectangle if not yet exist
        if not self.rect:
<<<<<<< HEAD
            self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red', tag="mapmanual")

    def on_move_press(self, event):  # draw mapping bordering for the final TDoA map
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map, map_preset, map_manual
        if map_preset == 1:
            pass
        else:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            lonmin = str((((self.start_x - 1910) * 180) / 1910)).rsplit('.')[0]
            lonmax = str(((cur_x - 1910) * 180) / 1910).rsplit('.')[0]
            latmax = str(0 - ((cur_y - 990) / 11)).rsplit('.')[0]
            latmin = str(((self.start_y - 990) / 11)).rsplit('.')[0]

            if cur_x > self.start_x and cur_y > self.start_y:
                lat_max_map = str(0 - int(latmin))
                lat_min_map = latmax
                lon_max_map = str(lonmax)
                lon_min_map = str(lonmin)

            if cur_x < self.start_x and cur_y > self.start_y:
                lat_max_map = str(0 - int(latmin))
                lat_min_map = latmax
                lon_max_map = str(lonmin)
                lon_min_map = str(lonmax)

            if cur_x > self.start_x and cur_y < self.start_y:
                lat_max_map = str(latmax)
                lat_min_map = str(0 - int(latmin))
                lon_max_map = str(lonmax)
                lon_min_map = str(lonmin)

            if cur_x < self.start_x and cur_y < self.start_y:
                lat_max_map = str(latmax)
                lat_min_map = str(0 - int(latmin))
                lon_max_map = str(lonmin)
                lon_min_map = str(lonmax)

            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            if event.x > 0.98 * w:
                self.canvas.xview_scroll(1, 'units')
            elif event.x < 0.02 * w:
                self.canvas.xview_scroll(-1, 'units')
            if event.y > 0.98 * h:
                self.canvas.yview_scroll(1, 'units')
            elif event.y < 0.02 * h:
                self.canvas.yview_scroll(-1, 'units')
            # expand rectangle as you drag the mouse
            self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
            self.show_image()

    def on_button_release(self, event):
        global mapboundaries_set, map_preset, map_manual, lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global ultimatelist, ultimatefav, white
        if (ultimate.get()) is 1:  # ultimateTDoA mode
            ultimatelist = []
            if os.path.isfile('directTDoA_server_list.db') is True:
                with open('directTDoA_server_list.db') as f:
                    db_data2 = json.load(f)
                    nodecount2 = len(db_data2)
                    for y in range(nodecount2):
                        if ultimatefav.get() == 1:
                            if (int(lat_min_map) < int(float(db_data2[y]["lat"])) < int(lat_max_map)) and (
                                    int(lon_min_map) < int(float(db_data2[y]["lon"])) < int(lon_max_map)) and \
                                    db_data2[y]["mac"] in white:
                                ultimatelist.append(
                                    db_data2[y]["url"].rsplit(':')[0] + "$" + db_data2[y]["url"].rsplit(':')[1] + "$" +
                                    db_data2[y]["mac"] + "$" + db_data2[y]["id"].replace("/", ""))
                        else:
                            if (int(lat_min_map) < int(float(db_data2[y]["lat"])) < int(lat_max_map)) and (
                                    int(lon_min_map) < int(float(db_data2[y]["lon"])) < int(lon_max_map)):
                                ultimatelist.append(
                                    db_data2[y]["url"].rsplit(':')[0] + "$" + db_data2[y]["url"].rsplit(':')[1] + "$" +
                                    db_data2[y]["mac"] + "$" + db_data2[y]["id"].replace("/", ""))
                    app.title(
                        VERSION + " - ultimateTDoA nodes : " + ' + '.join(str(p).rsplit('$')[3] for p in ultimatelist))
                    if len(ultimatelist) != 0:
                        app.window2.writelog("ultimateTDoA listing contains " + str(len(ultimatelist)) + " nodes")
                    app.window2.label4.configure(text="[LATITUDE] range: " + str(lat_min_map) + "° " + str(
                        lat_max_map) + "°  [LONGITUDE] range: " + str(lon_min_map) + "° " + str(lon_max_map) + "°")
            if len(ultimatelist) == 0:
                app.window2.writelog("No node location found within this area, Please retry..")
                app.title(VERSION)
                ultimatelist = []

        else:
            if map_preset == 1 and map_manual == 0:
                pass
            else:
                app.window2.label4.configure(text="[LATITUDE] range: " + str(lat_min_map) + "° " + str(
                    lat_max_map) + "°  [LONGITUDE] range: " + str(lon_min_map) + "° " + str(lon_max_map) + "°")
                mapboundaries_set = 1
                map_manual = 1

    def create_point(self, y, x, n):  # map known point creation process, works only when self.imscale = 1.0
        global currentcity, selectedcity
        #  city coordinates y & x (degrees) converted to pixels
        xx0 = (1907.5 + ((float(x) * 1910) / 180))
        xx1 = xx0 + 5
        if float(y) > 0:                                    # point is located in North Hemisphere
            yy0 = (987.5 - (float(y) * 11))
            yy1 = (987.5 - (float(y) * 11) + 5)
        else:                                               # point is located in South Hemisphere
            yy0 = (987.5 + (float(0 - (float(y) * 11))))
            yy1 = (987.5 + (float(0 - float(y)) * 11) + 5)

        self.canvas.create_rectangle(xx0, yy0, xx1, yy1, fill=colorline[3], outline="black", activefill=colorline[3],
                                     tag=selectedcity.rsplit(' (')[0])
        self.canvas.create_text(xx0, yy0 - 10, text=selectedcity.rsplit(' (')[0], justify='center', fill=colorline[3],
                                tag=selectedcity.rsplit(' (')[0])

    def deletePoint(self, y, x, n):  # deletion process (rectangles)
        FillMapWithNodes(self).deletePoint(n.rsplit(' (')[0])

    def onClick(self, event):  # host sub menus
        global snrcheck, snrhost, host, white, black, listenmode, frequency
        host = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        self.menu = Menu(self, tearoff=0, fg="black", bg="grey", font='TkFixedFont 7')
        self.menu2 = Menu(self.menu, tearoff=0, fg="black", bg="white", font='TkFixedFont 7')
        #  host.rsplit("$", 14)[#] <<
        #  0=host  1=id  2=short name  3=name  4=users  5=users max  6=GPS fix/min
        #  7=SNR 0-2 MHz  8=SNR 2-10 MHz  9=SNR 10-20 MHz  10=SNR 20-30 MHz
        #  11=Noise 0-2 MHz  12=Noise 2-10 MHz 13=Noise 10-20 MHz  14=Noise 20-30 MHz
        temp_snr_avg = (int(host.rsplit("$", 14)[7]) + int(host.rsplit("$", 14)[8]) + int(
            host.rsplit("$", 14)[9]) + int(host.rsplit("$", 14)[10])) / 4
        temp_noise_avg = (int(host.rsplit("$", 14)[11]) + int(host.rsplit("$", 14)[12]) + int(
            host.rsplit("$", 14)[13]) + int(host.rsplit("$", 14)[14])) / 4
        font_snr1 = font_snr2 = font_snr3 = font_snr4 = 'TkFixedFont 7'
        frequency = app.window2.Entry1.get()
        try:  # check if the node is answering
            chktimeout = 1  # timeout of the node check
            checkthenode = requests.get("http://" + str(host).rsplit("$", 14)[0] + "/status", timeout=chktimeout)
            infonodes = checkthenode.text.split("\n")
            try:  # node filtering
                permit_web = "no"
                is_gps_ok = "no"
                if infonodes[6].rsplit("=", 2)[1] == infonodes[7].rsplit("=", 2)[1]:  # users Vs. users_max
                    self.menu.add_command(label=str(host).rsplit("$", 14)[2] + " node have no available slots",
                                          background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                          foreground=self.get_font_color(
                                              (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                          command=None)
                elif infonodes[1].rsplit("=", 2)[1] == "yes":  # offline=no/yes
                    self.menu.add_command(label=str(host).rsplit("$", 14)[2] + " node is currently offline",
                                          background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                          foreground=self.get_font_color(
                                              (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                          command=None)
                elif infonodes[15].rsplit("=", 2)[1] <= "0":  # tdoa_ch=1 or more
                    self.menu.add_command(
                        label=str(host).rsplit("$", 14)[2] + " node have no TDoA channels set in its configuration [" +
                              infonodes[6].rsplit("=", 2)[1] + "/" + infonodes[7].rsplit("=", 2)[1] + " users]",
                        background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                        foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                        command=None)
                    permit_web = "yes"
                elif infonodes[12].rsplit("=", 2)[1] == "0":  # fixes_min=0
                    self.menu.add_command(label=str(host).rsplit("$", 14)[
                                                    2] + " node have currently 0 GPS fixes per min ..wait a bit.. [" +
                                                infonodes[6].rsplit("=", 2)[1] + "/" + infonodes[7].rsplit("=", 2)[
                                                    1] + " users]",
                                          background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                          foreground=self.get_font_color(
                                              (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                          command=None)
                    permit_web = "yes"
                else:  # all ok for this node
                    permit_web = "yes"
                    is_gps_ok = "yes"
                matches = [el for el in fulllist if host.rsplit(':')[0] in el]
                if len(matches) != 1 and is_gps_ok == "yes":
                    self.menu.add_command(label="Add " + str(host).rsplit("$", 14)[2] + " for TDoA process [" +
                                                    infonodes[12].rsplit("=", 2)[1] + " GPS fix/min] [" +
                                                    infonodes[6].rsplit("=", 2)[1] + "/" + infonodes[7].rsplit("=", 2)[
                                                        1] + " users]", background=(
                        self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                              foreground=self.get_font_color(
                                                  (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                              command=self.populate)

                elif len(matches) == 1:
                    self.menu.add_command(label="Remove " + str(host).rsplit("$", 14)[2] + " from TDoA process [" +
                                                    infonodes[12].rsplit("=", 2)[1] + " GPS fix/min] [" +
                                                    infonodes[6].rsplit("=", 2)[1] + "/" + infonodes[7].rsplit("=", 2)[
                                                        1] + " users]", background=(
                        self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                              foreground=self.get_font_color(
                                                  (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                              command=self.depopulate)

            except Exception:
                if "not found" in infonodes[13]:
                    self.menu.add_command(
                        label=str(host).rsplit("$", 14)[2] + " node is not available. (proxy.kiwisdr.com error)",
                        background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                        foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                        command=None)
                    permit_web = "no"

        except requests.RequestException as reqerr:
            try:  # trying to deal with requests exceptions texts...
                reqer = \
                str(reqerr.message).replace("'", "").replace(",", "").replace(":", "").replace("))", "").rsplit(">", 2)[
                    1]
            except:
                reqer = str(reqerr.message).rsplit(":", 1)[1]
            self.menu.add_command(label=str(host).rsplit("$", 14)[2] + " node is not available. " + str(reqer),
                                      background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                      foreground=self.get_font_color(
                                          (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))), command=None)
            permit_web = "no"

        self.menu.add_command(label=str(host.rsplit("$", 14)[3]).replace("_", " "), state=NORMAL,
                              background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                              foreground=self.get_font_color(
                                  (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))), command=None)

        if permit_web == "yes" and frequency != "" and 5 < float(frequency) < 30000:
            try:
                self.menu.add_command(
                    label="Open \"" + str(host).rsplit("$", 14)[0] + "/f=" + str(frequency) + "iqz8\" in browser",
                    state=NORMAL, background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                    foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                    command=self.openinbrowser)
                if float(frequency) <= 2000:
                    font_snr1 = 'TkFixedFont 8 bold'
                elif 2001 < float(frequency) <= 10000:
                    font_snr2 = 'TkFixedFont 8 bold'
                elif 10001 < float(frequency) <= 20000:
                    font_snr3 = 'TkFixedFont 8 bold'
                elif 20001 < float(frequency) <= 30000:
                    font_snr4 = 'TkFixedFont 8 bold'
            except:
                pass

        if permit_web == "yes" and listenmode == "0" and frequency != "" and 5 < float(frequency) < 30000:
            self.menu.add_cascade(
                label="Listen using " + str(host).rsplit("$", 14)[0],
                state=NORMAL, background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                menu=self.menu2)
            self.menu2.add_command(label="USB",
                                   background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                   foreground=self.get_font_color(
                                       (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                   command=lambda *args: self.listenmode("usb"))
            self.menu2.add_command(label="LSB",
                                   background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                   foreground=self.get_font_color(
                                       (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                   command=lambda *args: self.listenmode("lsb"))
            self.menu2.add_command(label="AM",
                                   background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                   foreground=self.get_font_color(
                                       (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                                   command=lambda *args: self.listenmode("am"))

        if listenmode == "1":
            self.menu.add_command(
                label="Stop Listen Mode",
                state=NORMAL, background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                command=self.stoplistenmode)

        self.menu.add_separator()
        self.menu.add_command(label="AVG SNR on 0-30 MHz: " + str(temp_snr_avg) + " dB - AVG Noise: " + str(
            temp_noise_avg) + " dBm (S" + str(self.convert_dbm_to_smeter(int(temp_noise_avg))) + ")",
                              background=(self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5)),
                              foreground=self.get_font_color(
                                  (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))), command=None)
        self.menu.add_separator()
        self.menu.add_command(
            label="AVG SNR on 0-2 MHz: " + host.rsplit("$", 14)[7] + " dB - AVG Noise: " + host.rsplit("$", 14)[
                11] + " dBm (S" + str(self.convert_dbm_to_smeter(int(host.rsplit("$", 14)[11]))) + ")",
            background=(self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[7]) - 50) * 5)),
            foreground=self.get_font_color(
                (self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[7]) - 50) * 5))), font=font_snr1,
            command=None)
        self.menu.add_command(
            label="AVG SNR on 2-10 MHz: " + host.rsplit("$", 14)[8] + " dB - AVG Noise: " + host.rsplit("$", 14)[
                12] + " dBm (S" + str(self.convert_dbm_to_smeter(int(host.rsplit("$", 14)[12]))) + ")",
            background=(self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[8]) - 50) * 5)),
            foreground=self.get_font_color(
                (self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[8]) - 50) * 5))), font=font_snr2,
            command=None)
        self.menu.add_command(
            label="AVG SNR on 10-20 MHz: " + host.rsplit("$", 14)[9] + " dB - AVG Noise: " + host.rsplit("$", 14)[
                13] + " dBm (S" + str(self.convert_dbm_to_smeter(int(host.rsplit("$", 14)[13]))) + ")",
            background=(self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[9]) - 50) * 5)),
            foreground=self.get_font_color(
                (self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[9]) - 50) * 5))), font=font_snr3,
            command=None)
        self.menu.add_command(
            label="AVG SNR on 20-30 MHz: " + host.rsplit("$", 14)[10] + " dB - AVG Noise: " + host.rsplit("$", 14)[
                14] + " dBm (S" + str(self.convert_dbm_to_smeter(int(host.rsplit("$", 14)[14]))) + ")",
            background=(self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[10]) - 50) * 5)),
            foreground=self.get_font_color(
                (self.color_variant("#FFFF00", (int(host.rsplit("$", 14)[10]) - 50) * 5))), font=font_snr4,
            command=None)
        self.menu.add_separator()
        if host.rsplit('$', 14)[1] in white:  # if node is a favorite
            self.menu.add_command(label="remove from favorites", command=self.remfavorite)
        elif host.rsplit('$', 14)[1] not in black:
            self.menu.add_command(label="add to favorites", command=self.addfavorite)
        if host.rsplit('$', 14)[1] in black:  # if node is blacklisted
            self.menu.add_command(label="remove from blacklist", command=self.remblacklist)
        elif host.rsplit('$', 14)[1] not in white:
=======
            self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red')

    def on_move_press(self, event):  # draw mapping bordering for the final TDoA map need
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        lonmin = str((((self.start_x - 1910) * 180) / 1910)).rsplit('.')[0]
        lonmax = str(((curX - 1910) * 180) / 1910).rsplit('.')[0]
        latmax = str(0 - ((curY - 990) / 11)).rsplit('.')[0]
        latmin = str(((self.start_y - 990) / 11)).rsplit('.')[0]

        if curX > self.start_x and curY > self.start_y:
            lat_max_map = str(0 - int(latmin))
            lat_min_map = latmax
            lon_max_map = str(lonmax)
            lon_min_map = str(lonmin)

        if curX < self.start_x and curY > self.start_y:
            lat_max_map = str(0 - int(latmin))
            lat_min_map = latmax
            lon_max_map = str(lonmin)
            lon_min_map = str(lonmax)

        if curX > self.start_x and curY < self.start_y:
            lat_max_map = str(latmax)
            lat_min_map = str(0 - int(latmin))
            lon_max_map = str(lonmax)
            lon_min_map = str(lonmin)

        if curX < self.start_x and curY < self.start_y:
            lat_max_map = str(latmax)
            lat_min_map = str(0 - int(latmin))
            lon_max_map = str(lonmin)
            lon_min_map = str(lonmax)

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if event.x > 0.9*w:
            self.canvas.xview_scroll(1, 'units')
        elif event.x < 0.1*w:
            self.canvas.xview_scroll(-1, 'units')
        if event.y > 0.9*h:
            self.canvas.yview_scroll(1, 'units')
        elif event.y < 0.1*h:
            self.canvas.yview_scroll(-1, 'units')
        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
        self.show_image()

    def on_button_release(self, event):
        if platform.system() == "Windows":
            tkMessageBox.showinfo("TDoA map Geographical boundaries set", message=
lon_min_map + "°                   LONGITUDE                      " + lon_max_map + "°" + '''
 +---------------------------------------+   ''' + lat_max_map + '''°
 |                                                                   | 
 |                                                                   |
 |                                                                   |   LATITUDE
 |                                                                   |
 |                                                                   |
 +---------------------------------------+   ''' + lat_min_map + "°")
        if platform.system() == "Linux":
            tkMessageBox.showinfo("TDoA map Geographical boundaries set",
                                  message="LONGITUDE RANGE: from " + lon_min_map + "° to " + lon_max_map + "°\nLATITUDE RANGE: from " + lat_min_map + "° to " + lat_max_map + "°")
        pass

    def createPoint(self, y ,x ,n):  # city mappoint creation process, works only when self.imscale = 1.0
        global currentcity, selectedcity, zoomlevel
        print self.canvas.canvasx(x)
        print self.canvas.canvasy(y)
        #  city coordinates y & x (degrees) converted to pixels
        xx0 = (1907.5 + ((float(x) * 1910) / 180))
        xx1 = xx0 + 5
        if float(y) > 0:                                    # city is located in North Hemisphere
            yy0 = (987.5 - (float(y) * 11))
            yy1 = (987.5 - (float(y) * 11) + 5)
        else:                                               # city is located in South Hemisphere
            yy0 = (987.5 + (float(0 - (float(y) * 11))))
            yy1 = (987.5 + (float(0 - float(y)) * 11) + 5)

        self.canvas.create_rectangle(xx0, yy0, xx1, yy1, fill='yellow', outline="black", activefill='yellow',
                                         tag=selectedcity.rsplit(' (')[0])
        self.canvas.create_text(xx0, yy0 - 10, text=selectedcity.rsplit(' (')[0], justify='center', fill="yellow",
                                    tag=selectedcity.rsplit(' (')[0])

    def deletePoint(self, y, x, n):  # city map point deletion process
        FillMapWithNodes(self).deletePoint(n.rsplit(' (')[0])

    def onFocusIn(self, event):
        coordonnees = self.canvas.coords(self.canvas.find_withtag(CURRENT))
        self.canvas.create_text(coordonnees[0], coordonnees[1] - 10,
                                text=self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0],
                                justify='center', fill="white",
                                tag="tag" + self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0])

    def onFocusOff(self, event):
        time.sleep(0.005)
        self.canvas.delete("tag"+self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0])

    def onClick(self, event):
        global snrcheck, snrhost, host, white, black, frequency
        # x1, x2, y1, y2, o, full_list, snrcheck, snrhost, host
        host = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        self.menu = Menu(self, tearoff=0, fg="black", bg="gray", font='TkFixedFont 7')
        self.menu.add_command(label="Use: " + str(host).rsplit("$", 4)[0] + " (" + str(host).rsplit("$", 4)[3] + "/" +
                                    str(host).rsplit("$", 4)[4] + " users) for TdoA process",
                              command=self.populate)  # Host + Users Vs Users Max
        self.menu.add_command(
            label="Open \"" + str(host).rsplit("$", 4)[0] + "/f=" + str(frequency) + "iqz8\" in browser",
            command=self.openinbrowser)
        self.menu.add_command(label=str(host).rsplit("$", 4)[2].replace("_", " "), state=DISABLED, font='TkFixedFont 7',
                              command=None)
        self.menu.add_separator()
        if host.rsplit('$', 4)[1] in white:  # if node is a favorite
            self.menu.add_command(label="remove from favorites", command=self.remfavorite)
        elif host.rsplit('$', 4)[1] not in black:
            self.menu.add_command(label="add to favorites", command=self.addfavorite)
        if host.rsplit('$', 4)[1] in black:  # if node is blacklisted
            self.menu.add_command(label="remove from blacklist", command=self.remblacklist)
        elif host.rsplit('$', 4)[1] not in white:
>>>>>>> Add files via upload
            self.menu.add_command(label="add to blacklist", command=self.addblacklist)

        # self.menu.add_command(label="check SNR", state=DISABLED, command=self.displaySNR)  # for next devel
        # if snrcheck == True:
        #     print "SNR requested on " + str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     print snrfreq
        #     snrhost = str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     SnrProcessing(self).start()
        #     app.title("Checking SNR for" + str(snrhost) + ". Please wait")

        self.menu.post(event.x_root, event.y_root)

<<<<<<< HEAD
    def get_font_color(self, ff):  # adapting the font color regarding background luminosity
        # stackoverflow.com/questions/946544/good-text-foreground-color-for-a-given-background-color/946734#946734
        rgb_hex = [ff[x:x + 2] for x in [1, 3, 5]]
        if int(rgb_hex[0], 16)*0.299 + int(rgb_hex[1], 16)*0.587 + int(rgb_hex[2], 16)*0.114 > 186:
            return "#000000"
        else:
            return "#FFFFFF"
        # if (red*0.299 + green*0.587 + blue*0.114) > 186 use #000000 else use #ffffff
        pass

    def convert_dbm_to_smeter(self, dbm):
        dBm_values = [-121, -115, -109, -103, -97, -91, -85, -79, -73, -63, -53, -43, -33, -23, -13, -3]
        if dbm != 0:
            return next(x[0] for x in enumerate(dBm_values) if x[1] > dbm)
        else:
            return "--"

    def color_variant(self, hex_color, brightness_offset=1):
        # source : https://chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join(["0" + hex(i)[2:] if len(hex(i)[2:]) < 2 else hex(i)[2:] for i in new_rgb_int])

    def addfavorite(self):
        global white, black
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 14)[1] in white:
=======
    def addfavorite(self):
        # print str(host).rsplit("$", 4)[2].replace("_", " ")  # Name
        # print host.rsplit('$', 4)[1]  # ID
        global white, black
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            map = configline[3].split('\n')[0]
            mapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        if host.rsplit('$', 4)[1] in white:
>>>>>>> Add files via upload
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already in the favorite list !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
<<<<<<< HEAD
                u.write("This is " + VERSION + " config file\n")
                u.write(
                    "This file should be generated by directTDoA software only, in case something went wrong you can find a sample here: https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg\n")
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                    mapfl, gpsfl))
                if white[0] == "":
                    u.write("# Whitelist \n%s\n" % host.rsplit('$', 14)[1])
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                else:
                    white.append(host.rsplit('$', 14)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
                u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % defaultbw)
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the favorite list !")
            Restart().run()

    def remfavorite(self):
        global white, black, newwhite
        newwhite = []
        ReadConfigFile().read_cfg()
        for f in white:
            if f != host.rsplit('$', 14)[1]:
                newwhite.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("This is " + VERSION + " config file\n")
            u.write(
                "This file should be generated by directTDoA software only, in case something went wrong you can find a sample here: https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg\n")
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                mapfl, gpsfl))
            u.write("# Whitelist \n%s\n" % ','.join(newwhite))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % defaultbw)
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the favorites list !")
        Restart().run()

    def addblacklist(self):
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 14)[1] in black:
=======
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % (map))
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
                if white[0] == "":
                    u.write("# Whitelist \n%s\n" % host.rsplit('$', 4)[1])
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                else:
                    white.append(host.rsplit('$', 4)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the favorite list !")
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)

    def remfavorite(self):
        global white, black, newwhite
        newwhite =[]
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            map = configline[3].split('\n')[0]
            mapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        for f in white:
            if f != host.rsplit('$', 4)[1]:
                newwhite.append(f)
        print ','.join(newwhite)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (map))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
            u.write("# Whitelist \n%s\n" % ','.join(newwhite))
            u.write("# Blacklist \n%s\n" % ','.join(black))
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the favorites list !")
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    def addblacklist(self):
        #print host.rsplit('$', 4)[1]  # ID
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            map = configline[3].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        if host.rsplit('$', 4)[1] in black:
>>>>>>> Add files via upload
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already blacklisted !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
<<<<<<< HEAD
                u.write("This is " + VERSION + " config file\n")
                u.write(
                    "This file should be generated by directTDoA software only, in case something went wrong you can find a sample here: https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg\n")
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                    mapfl, gpsfl))
                if black[0] == "":
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % host.rsplit('$', 14)[1])
                else:
                    black.append(host.rsplit('$', 14)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
                u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % defaultbw)
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the blacklist !")
            Restart().run()

    def remblacklist(self):
        global white, black, newblack
        newblack = []
        ReadConfigFile().read_cfg()
        for f in black:
            if f != host.rsplit('$', 14)[1]:
                newblack.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("This is " + VERSION + " config file\n")
            u.write(
                "This file should be generated by directTDoA software only, in case something went wrong you can find a sample here: https://raw.githubusercontent.com/llinkz/directTDoA/master/directTDoA.cfg\n")
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % dmap)
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                mapfl, gpsfl))
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(newblack))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.write("# Default IQ recording bandwidth (in Hz) \n%s\n" % defaultbw)
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the blacklist !")
        Restart().run()

    def openinbrowser(self):
        if frequency != 10000:
            url = "http://" + str(host).rsplit("$", 14)[0] + "/?f=" + str(frequency) + "iqz8"
            webbrowser.open_new(url)
        else:
            url = "http://" + str(host).rsplit("$", 14)[0]
            webbrowser.open_new(url)

    def listenmode(self, d):
        global server_host, server_port, frequency, listenmode, kiwisdrclient_pid, dd
        server_host = str(host).rsplit("$", 14)[0].rsplit(":", 2)[0]
        server_port = str(host).rsplit("$", 14)[0].rsplit(":", 2)[1]
        frequency = app.window2.Entry1.get()
        dd = d
        if listenmode == "0":
            StartKiwiSDRclient(self).start()
        else:
            os.kill(kiwisdrclient_pid, signal.SIGTERM)
            StartKiwiSDRclient(self).start()

    def stoplistenmode(self):
        global listenmode, kiwisdrclient_pid
        os.kill(kiwisdrclient_pid, signal.SIGTERM)
        listenmode = "0"
        app.window2.writelog("Stopping Listen mode")

    def populate(self):
        if len(fulllist) < 6:
            fulllist.append(
                host.rsplit(':')[0] + "$" + host.rsplit(':')[1].rsplit('$')[0] + "$" + host.rsplit('$')[1] + "$" +
                host.rsplit('$')[2].replace("/", ""))
            app.title(VERSION + " - Selected nodes : " + ' + '.join(str(p).rsplit('$')[3] for p in fulllist))
=======
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % (map))
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
                if black[0] == "":
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % host.rsplit('$', 4)[1])
                else:
                    black.append(host.rsplit('$', 4)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the blacklist !")
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)

    def remblacklist(self):
        global white, black, newblack
        newblack =[]
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            map = configline[3].split('\n')[0]
            mapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        for f in black:
            if f != host.rsplit('$', 4)[1]:
                newblack.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (map))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(newblack))
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the blacklist !")
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    def openinbrowser(self):
        global frequency
        if frequency != "10000":
            url = "http://" + str(host).rsplit("$", 4)[0] + "/?f=" + str(frequency) + "iqz8"
            webbrowser.open_new(url)
        else:
            url = "http://" + str(host).rsplit("$", 4)[0]
            webbrowser.open_new(url)

    def populate(self):
        global full_list, serverlist, portlist, namelist
        # host.rsplit(':')[0]   # host/ip
        # host.rsplit('$', 4)[0].rsplit(':')[1] # port
        if len(serverlist) < 6:
            if host.rsplit(':')[0] not in serverlist:
                serverlist.append(host.rsplit(':')[0])  # host
                portlist.append(host.rsplit(':')[1].rsplit('$')[0])  # port
                namelist.append(host.rsplit('$')[1])  # id
                app.title(
                    VERSION + " - " + str(serverlist).replace("[", "").replace("'", "").replace("]", "").replace(",",
                                                                                                                 " +"))
                full_list = str(serverlist).replace("[", "").replace("'", "").replace("]", "").replace(",", " +")
            else:
                tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                      message=str(host.rsplit(':')[0]) + " is already in the server list !")
>>>>>>> Add files via upload
        else:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message="[[[maximum server limit reached]]]")

<<<<<<< HEAD
    def depopulate(self):
        fulllist.remove(
            host.rsplit(':')[0] + "$" + host.rsplit(':')[1].rsplit('$')[0] + "$" + host.rsplit('$')[1] + "$" +
            host.rsplit('$')[2].replace("/", ""))
        if len(fulllist) != 0:
            app.title(VERSION + " - Selected nodes : " + ' + '.join(str(p).rsplit('$')[3] for p in fulllist))
        else:
            app.title(VERSION)

    def scroll_y(self, *args, **kwargs):
=======
    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
>>>>>>> Add files via upload
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
<<<<<<< HEAD
=======
        ''' Scroll canvas horizontally and redraw the image '''
>>>>>>> Add files via upload
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
<<<<<<< HEAD
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
=======
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
>>>>>>> Add files via upload
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
<<<<<<< HEAD
=======
        ''' Zoom with mouse wheel '''
>>>>>>> Add files via upload
        global bbox
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else:
            return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
<<<<<<< HEAD
            if int(i * self.imscale) < 2000:
                return  # block zoom if image is less than 600 pixels
=======
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
>>>>>>> Add files via upload
            self.imscale /= self.delta
            scale /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
<<<<<<< HEAD
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
=======
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
>>>>>>> Add files via upload
            self.imscale *= self.delta
            scale *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
<<<<<<< HEAD
=======
        ''' Show image on the Canvas '''
>>>>>>> Add files via upload
        global bbox1, bbox2, x1, x2, y1, y2
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
<<<<<<< HEAD
        self.canvas.configure(scrollregion=bbox)  # set scroll region
=======
        # self.canvas.configure(scrollregion=bbox)  # set scroll region
>>>>>>> Add files via upload
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


class MainWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        # self.parent = parent
<<<<<<< HEAD
        self.member1 = ZoomAdvanced(parent)
        if os.path.isfile('directTDoA_server_list.db') is not True:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ", message="oops no node db found, Click OK to run an update now")
            CheckUpdate().run()
        ReadKnownPointFile().run()
        global frequency
        global line, i, bgc, fgc, dfgc, lpcut, hpcut, currentbw, ultimate, ultimatefav
        global latmin, latmax, lonmin, lonmax, bbox1, lat_min_map, lat_max_map, lon_min_map, lon_max_map
        global selectedlat, selectedlon, selectedcity, map_preset, map_manual, rec_in_progress, tdoa_in_progress
        frequency = DoubleVar(self, 10000.0)
        ultimate = IntVar(self)
        ultimatefav = IntVar(self)
        bgc = '#d9d9d9'  # GUI background color
        fgc = '#000000'  # GUI foreground color
        dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        lpcut = hpcut = int(defaultbw) / 2
        currentbw = defaultbw
=======
        self.member1 = Zoom_Advanced(parent)
        global frequency, checkfilepid
        global main_pid, line, kiwi_update, i, bgc, fgc, dfgc, city, citylat, citylon, lpcut, hpcut
        global latmin, latmax, lonmin, lonmax, bbox1, lat_min_map, lat_max_map, lon_min_map, lon_max_map
        global selectedlat, selectedlon, zoomlevel
        main_pid = os.getpid()
        frequency = tk.DoubleVar()
        bgc = '#d9d9d9'
        fgc = '#000000'
        dfgc = '#a3a3a3'
        frequency = 10000
        lpcut = 5000
        hpcut = 5000
>>>>>>> Add files via upload
        lat_min_map = ""
        lat_max_map = ""
        lon_min_map = ""
        lon_max_map = ""
        selectedlat = ""
        selectedlon = ""
<<<<<<< HEAD
        selectedcity = ""
        map_preset = 0
        map_manual = 0
        rec_in_progress = 0
        tdoa_in_progress = 0
        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.69, relheight=0.4, relwidth=1)
        self.label0.configure(bg=bgc, fg=fgc, width=214)
        # top left map legend
        self.label00 = Label(parent)
        self.label00.place(x=0, y=0, height=14, width=75)
        self.label00.configure(bg="grey", font="TkFixedFont 7", anchor="w", fg="black", text="Legend:")
        self.label01 = Label(parent)
        self.label01.place(x=0, y=14, height=14, width=75)
        self.label01.configure(bg="grey", font="TkFixedFont 7", anchor="w", fg=colorline[0], text="█ Standard")
        self.label02 = Label(parent)
        self.label02.place(x=0, y=28, height=14, width=75)
        self.label02.configure(bg="grey", font="TkFixedFont 7", anchor="w", fg=colorline[1], text="█ Favorite")
        self.label03 = Label(parent)
        self.label03.place(x=0, y=42, height=14, width=75)
        self.label03.configure(bg="grey", font="TkFixedFont 7", anchor="w", fg=colorline[2], text="█ Blacklisted")
        self.label04 = Label(parent)
        self.label04.place(x=0, y=56, height=14, width=75)
        self.label04.configure(bg="grey", font="TkFixedFont 7", anchor="w", fg="#001E00", text="█ no SNR data")
        self.Entry1 = Entry(parent, textvariable=frequency)
        self.Entry1.place(relx=0.06, rely=0.892, height=24, relwidth=0.1)
        self.Entry1.configure(bg="white", disabledforeground=dfgc, font="TkFixedFont", fg=fgc,
                              insertbackground=fgc, width=214)
        self.label1 = Label(parent)
        self.label1.place(relx=0.01, rely=0.895)
        self.label1.configure(bg=bgc, font="TkFixedFont", fg=fgc, text="Freq:")
        self.label2 = Label(parent)
        self.label2.place(relx=0.162, rely=0.895)
        self.label2.configure(bg=bgc, font="TkFixedFont", fg=fgc, text="kHz")
        self.Button1 = Button(parent)  # Start recording button
        self.Button1.place(relx=0.77, rely=0.89, height=24, relwidth=0.10)
        self.Button1.configure(activebackground=bgc, activeforeground=fgc, bg=bgc, disabledforeground=dfgc,
                               fg=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start recording", command=self.clickstart, state="normal")
        self.Button2 = Button(parent)  # Stop & Start TDoA button
        self.Button2.place(relx=0.88, rely=0.89, height=24, relwidth=0.1)
        self.Button2.configure(activebackground=bgc, activeforeground=fgc, bg=bgc, disabledforeground=dfgc,
                               fg=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start TDoA proc", command=self.clickstop, state="disabled")
        self.Choice = Entry(parent)
        self.Choice.place(relx=0.01, rely=0.95, height=21, relwidth=0.18)
        self.Choice.insert(0, "TDoA map city/site search here")
        self.ListBox = Listbox(parent)
        self.ListBox.place(relx=0.2, rely=0.95, height=21, relwidth=0.3)
        self.label3 = Label(parent)  # Known point
        self.label3.place(relx=0.54, rely=0.95, height=21, relwidth=0.3)
        self.label3.configure(bg=bgc, font="TkFixedFont", fg=fgc, width=214, text="", anchor="w")
        self.label4 = Label(parent)  # Map boundaries information
        self.label4.place(relx=0.2, rely=0.895, height=21, relwidth=0.55)
        self.label4.configure(bg=bgc, font="TkFixedFont", fg=fgc, width=214, text="", anchor="w")
        self.Checkbutton1 = Checkbutton(parent)  # ultimateTDoA check box
        self.Checkbutton1.place(relx=0.55, rely=0.895, height=21, relwidth=0.11)
        self.Checkbutton1.configure(bg=bgc, font="TkFixedFont 8", fg=fgc, width=214,
                                    text="ultimateTDoA mode", anchor="w", variable=ultimate, command=self.checkboxcheck)
        self.Checkbutton2 = Checkbutton(parent)  # ultimateTDoA favorite nodes
        self.Checkbutton2.place(relx=0.66, rely=0.895, height=21, relwidth=0.08)
        self.Checkbutton2.configure(bg=bgc, font="TkFixedFont 8", fg=fgc, width=214, state="disabled",
                                    text="favorites only", anchor="w", variable=ultimatefav)
        self.Button5 = Button(parent)  # Restart GUI button
        self.Button5.place(relx=0.81, rely=0.94, height=24, relwidth=0.08)
        self.Button5.configure(activebackground=bgc, activeforeground=fgc, bg="red", disabledforeground=dfgc,
                               fg=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Restart GUI", command=Restart().run, state="normal")
        self.Button3 = Button(parent)  # Update button
        self.Button3.place(relx=0.90, rely=0.94, height=24, relwidth=0.08)
        self.Button3.configure(activebackground=bgc, activeforeground=fgc, bg=bgc, disabledforeground=dfgc,
                               fg=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="update map", command=self.runupdate, state="normal")
        self.Button4 = Button(parent)  # Purge node list button
        self.Button4.place(relx=0.72, rely=0.94, height=24, relwidth=0.08)
        self.Button4.configure(activebackground=bgc, activeforeground=fgc, bg="orange", disabledforeground=dfgc,
                               fg=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Purge Nodes", command=self.purgenode, state="normal")
        self.Text2 = Text(parent)  # Console window
        self.Text2.place(relx=0.005, rely=0.7, relheight=0.18, relwidth=0.6)
        self.Text2.configure(bg="black", font="TkTextFont", fg="red", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")
        self.writelog("This is " + VERSION + ", a GUI written for python 2.7 / Tk")
        self.writelog("All credits to Christoph Mayer for his excellent TDoA work : http://hcab14.blogspot.com")
        self.writelog("Thanks to Pierre (linkfanel) for his listing of available KiwiSDR nodes")
        self.writelog("Thanks to Marco (IS0KYB) for his SNR measurements listing of the KiwiSDR network")
        self.writelog(
            "Already computed TDoA runs : " + str([len(d) for r, d, folder in os.walk(os.path.join('TDoA', 'iq'))][0]))
        self.writelog("There are " + str(nodecount) + " KiwiSDRs in the db. Have fun !")
        self.writelog("The default IQ recording bandwidth is set to " + defaultbw + "Hz")
        vsb2 = Scrollbar(parent, orient="vertical", command=self.Text2.yview)  # adding scrollbar to console
        vsb2.place(relx=0.6, rely=0.7, relheight=0.18, relwidth=0.02)
        self.Text2.configure(yscrollcommand=vsb2.set)
        self.Text3 = Text(parent)  # IQ recs file size window
        self.Text3.place(relx=0.624, rely=0.7, relheight=0.18, relwidth=0.37)
        self.Text3.configure(bg="white", font="TkTextFont", fg="black", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")

        # -------------------------------------------------LOGGING AND MENUS--------------------------------------------
        menubar = Menu(self)
        parent.config(menu=menubar)
        filemenu = Menu(menubar, tearoff=0)  # Map Settings
        filemenu2 = Menu(menubar, tearoff=0)  # Map Presets
        filemenu3 = Menu(menubar, tearoff=0)  # IQ Bandwidth
        filemenu4 = Menu(menubar, tearoff=0)  # About
        menubar.add_cascade(label="Map Settings", menu=filemenu)
        submenu1 = Menu(filemenu, tearoff=0)
        submenu2 = Menu(filemenu, tearoff=0)
        submenu3 = Menu(filemenu, tearoff=0)
        filemenu.add_cascade(label='Default map', menu=submenu1, underline=0)
        submenu1.add_command(label="Browse maps folder", command=self.choose_map)
        filemenu.add_cascade(label='Map Filters', menu=submenu2, underline=0)
        submenu2.add_command(label="Minimum GPS fixes/min", command=self.min_gps_filter)
        submenu2.add_command(label="Display All nodes", command=lambda *args: self.setmapfilter('0'))
        submenu2.add_command(label="Display Standard + Favorites", command=lambda *args: self.setmapfilter('1'))
        submenu2.add_command(label="Display Favorites", command=lambda *args: self.setmapfilter('2'))
        submenu2.add_command(label="Display Blacklisted", command=lambda *args: self.setmapfilter('3'))
        filemenu.add_cascade(label='Set Colors', menu=submenu3, underline=0)
        submenu3.add_command(label="Standard node color", command=lambda *args: self.color_change(0))
        submenu3.add_command(label="Favorite node color", command=lambda *args: self.color_change(1))
        submenu3.add_command(label="Blacklisted node color", command=lambda *args: self.color_change(2))
        submenu3.add_command(label="Known map point color", command=lambda *args: self.color_change(3))
        menubar.add_cascade(label="Map Presets", menu=filemenu2)
        filemenu2.add_command(label="Europe", command=lambda *args: self.map_preset(0))
        filemenu2.add_command(label="Africa", command=lambda *args: self.map_preset(1))
        filemenu2.add_command(label="Middle-East", command=lambda *args: self.map_preset(2))
        filemenu2.add_command(label="South Asia", command=lambda *args: self.map_preset(8))
        filemenu2.add_command(label="South-East Asia", command=lambda *args: self.map_preset(7))
        filemenu2.add_command(label="East Asia", command=lambda *args: self.map_preset(5))
        filemenu2.add_command(label="North America", command=lambda *args: self.map_preset(9))
        filemenu2.add_command(label="Central America", command=lambda *args: self.map_preset(6))
        filemenu2.add_command(label="South America", command=lambda *args: self.map_preset(3))
        filemenu2.add_command(label="Oceania", command=lambda *args: self.map_preset(4))
        filemenu2.add_command(label="West Russia", command=lambda *args: self.map_preset(10))
        filemenu2.add_command(label="East Russia", command=lambda *args: self.map_preset(11))
        filemenu2.add_command(label="USA", command=lambda *args: self.map_preset(12))
        filemenu2.add_command(label="World (use with caution)", command=lambda *args: self.map_preset(13))
        # next map boundaries presets come here, keep preset "20" for reset
        filemenu2.add_command(label="--- RESET ---", command=lambda *args: self.map_preset(20))
        filemenu3.add_command(label="Set Default BW", command=self.set_bw)
        menubar.add_cascade(label="IQ bandwidth", menu=filemenu3)
        iqset = ['10000', '9000', '8000', '7000', '6000', '5000', '4000', '3000', '2000', '1000', '900', '800', '700',
                 '600', '500', '400', '300', '200', '100', '50']
        for bwlist in iqset:
            filemenu3.add_command(label=bwlist + " Hz", command=lambda bwlist=bwlist: self.set_iq(bwlist))
        menubar.add_cascade(label="?", menu=filemenu4)
        filemenu4.add_command(label="Help", command=self.help)
        filemenu4.add_command(label="About", command=self.about)
        filemenu4.add_command(label="Check for Update Now...", command=self.checkversion)
        self.listbox_update(my_info1)
        self.ListBox.bind('<<ListboxSelect>>', self.on_select)
        self.Choice.bind('<FocusIn>', self.resetcity)
        self.Choice.bind('<KeyRelease>', self.on_keyrelease)
        self.Entry1.delete(0, 'end')
        self.checkversion()
        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            os.remove(wavfiles)
        CheckFileSize().start()

    def checkboxcheck(self):
        if ultimate.get() == 1:
            self.Checkbutton2.configure(state="normal")
        if ultimate.get() == 0:
            self.Checkbutton2.configure(state="disabled")

    def on_keyrelease(self, event):
        value = event.widget.get()
        value = value.strip().lower()
        if value == '':
            data = my_info1
        else:
            data = []
            for item in my_info1:
                if value in item.lower():
                    data.append(item)
        self.listbox_update(data)

    def listbox_update(self, data):
        self.ListBox.delete(0, 'end')
        data = sorted(data, key=str.lower)
        for item in data:
            self.ListBox.insert('end', item)

    def on_select(self, event):  # KNOWN POINT SELECTION
        global selectedlat, selectedlon, selectedcity
        try:
            if event.widget.get(event.widget.curselection()) == " ":
                tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ", message="Type something in the left box to search for a point before clicking here")
            else:
                self.label3.configure(text="LAT: " + str(
                    my_info2[my_info1.index(event.widget.get(event.widget.curselection()))]) + " LON: " + str(
                    my_info3[my_info1.index(event.widget.get(event.widget.curselection()))]))
                selectedlat = str(my_info2[my_info1.index(event.widget.get(event.widget.curselection()))])
                selectedlon = str(my_info3[my_info1.index(event.widget.get(event.widget.curselection()))])
                selectedcity = event.widget.get(event.widget.curselection())
                self.member1.create_point(selectedlat, selectedlon, selectedcity)
        except:
            pass

    def resetcity(self, my_info1):
        global selectedlat, selectedlon, selectedcity
        self.Choice.delete(0, 'end')
        self.label3.configure(text="")
        if selectedcity is not "":
            self.member1.deletePoint(selectedlat, selectedlon, selectedcity)
            selectedcity = ""
            selectedlat = ""
            selectedlon = ""
=======
        city = ['pick a city for TDoA map point display or leave as it to hide (choose once)',
                  'Abu_Dhabi (United Arab Emirates)', 'Abuja (Nigeria)', 'Accra (Ghana)',
                  'Adamstown (Pitcairn Islands)', 'Addis_Ababa (Ethiopia)', 'Algiers (Algeria)', 'Alofi (Niue)',
                  'Amman (Jordan)', 'Amsterdam (Netherlands)', 'Andorra_la_Vella (Andorra)', 'Ankara (Turkey)',
                  'Antananarivo (Madagascar)', 'Apia (Samoa)', 'Ashgabat (Turkmenistan)', 'Asmara (Eritrea)',
                  'Astana (Kazakhstan)', 'Asuncion (Paraguay)', 'Atafu (Tokelau)', 'Athens (Greece)',
                  'Avarua (Cook Islands)', 'Baghdad (Iraq)', 'Baku (Azerbaijan)', 'Bamako (Mali)',
                  'Bandar_Seri_Begawan (Brunei Darussalam)', 'Bangkok (Thailand)', 'Bangui (Central African Republic)',
                  'Banjul (The Gambia)', 'Basseterre (Saint Kitts and Nevis)', 'Beijing (China)', 'Beirut (Lebanon)',
                  'Belgrade (Serbia)', 'Belmopan (Belize)', 'Berlin (Germany)', 'Bern (Switzerland)',
                  'Bishkek (Kyrgyzstan)', 'Bissau (Guinea-Bissau)', 'Bogota (Colombia)', 'Brasilia (Brazil)',
                  'Bratislava (Slovakia)', 'Brazzaville (Republic of Congo)', 'Bridgetown (Barbados)',
                  'Brussels (Belgium)', 'Bucharest (Romania)', 'Budapest (Hungary)', 'Buenos_Aires (Argentina)',
                  'Bujumbura (Burundi)', 'Cairo (Egypt)', 'Canberra (Australia)', 'Caracas (Venezuela)',
                  'Castries (Saint Lucia)', 'Charlotte_Amalie (US Virgin Islands)', 'Chisinau (Moldova)',
                  'Colombo (Sri Lanka)', 'Conakry (Guinea)', 'Copenhagen (Denmark)', 'Dakar (Senegal)',
                  'Damascus (Syria)', 'Dar_es_Salaam (Tanzania)', 'Dhaka (Bangladesh)',
                  'Diego_Garcia (British Indian Ocean Territory)', 'Dili (Timor-Leste)', 'Djibouti (Djibouti)',
                  'Doha (Qatar)', 'Douglas (Isle of Man)', 'Dublin (Ireland)', 'Dushanbe (Tajikistan)',
                  'El_Ayoun (Western Sahara)', 'Freetown (Sierra Leone)', 'Funafuti (Tuvalu)', 'Gaborone (Botswana)',
                  'George_Town (Cayman Islands)', 'Georgetown (Guyana)', 'Gibraltar (Gibraltar)',
                  'Grand_Turk (Turks and Caicos Islands)', 'Guatemala_City (Guatemala)', 'Gustavia (Saint Barthelemy)',
                  'Hagatna (Guam)', 'Hamilton (Bermuda)', 'Hanoi (Vietnam)', 'Harare (Zimbabwe)',
                  'Hargeisa (Somaliland)', 'Havana (Cuba)', 'Helsinki (Finland)', 'Honiara (Solomon Islands)',
                  'Islamabad (Pakistan)', 'Jakarta (Indonesia)', 'Jamestown (Saint Helena)', 'Jerusalem (Israel)',
                  'Jerusalem (Palestine)', 'Juba (South Sudan)', 'Kabul (Afghanistan)', 'Kampala (Uganda)',
                  'Kathmandu (Nepal)', 'Khartoum (Sudan)', 'Kigali (Rwanda)',
                  'King_Edward_Point (South Georgia and South Sandwich Islands)', 'Kingston (Jamaica)',
                  'Kingston (Norfolk Island)', 'Kingstown (Saint Vincent and the Grenadines)',
                  'Kinshasa (Democratic Republic of the Congo)', 'Kuala_Lumpur (Malaysia)', 'Kuwait_City (Kuwait)',
                  'Kyiv (Ukraine)', 'La_Paz (Bolivia)', 'Libreville (Gabon)', 'Lilongwe (Malawi)', 'Lima (Peru)',
                  'Lisbon (Portugal)', 'Ljubljana (Slovenia)', 'Lome (Togo)', 'London (United Kingdom)',
                  'Longyearbyen (Svalbard)', 'Luanda (Angola)', 'Lusaka (Zambia)', 'Luxembourg (Luxembourg)',
                  'Madrid (Spain)', 'Majuro (Marshall Islands)', 'Malabo (Equatorial Guinea)', 'Male (Maldives)',
                  'Managua (Nicaragua)', 'Manama (Bahrain)', 'Manila (Philippines)', 'Maputo (Mozambique)',
                  'Mariehamn (Aland Islands)', 'Marigot (Saint Martin)', 'Maseru (Lesotho)',
                  'Mata_Utu (Wallis and Futuna)', 'Mbabane (Swaziland)', 'Melekeok (Palau)', 'Mexico_City (Mexico)',
                  'Minsk (Belarus)', 'Mogadishu (Somalia)', 'Monaco (Monaco)', 'Monrovia (Liberia)',
                  'Montevideo (Uruguay)', 'Moroni (Comoros)', 'Moscow (Russia)', 'Muscat (Oman)', 'Antarctica',
                  'Heard Island and McDonald Islands', 'Hong Kong', 'Macau', 'Nairobi (Kenya)',
                  'Nassau (Bahamas)', 'N_Djamena (Chad)', 'New_Delhi (India)', 'Niamey (Niger)', 'Nicosia (Cyprus)',
                  'North_Nicosia (Northern Cyprus)', 'Nouakchott (Mauritania)', 'Noumea (New Caledonia)',
                  'Nuku_alofa (Tonga)', 'Nuuk (Greenland)', 'Oranjestad (Aruba)', 'Oslo (Norway)', 'Ottawa (Canada)',
                  'Ouagadougou (Burkina Faso)', 'Pago_Pago (American Samoa)',
                  'Palikir (Federated States of Micronesia)', 'Panama_City (Panama)', 'Papeete (French Polynesia)',
                  'Paramaribo (Suriname)', 'Paris (France)', 'Philipsburg (Sint Maarten)', 'Phnom_Penh (Cambodia)',
                  'Plymouth (Montserrat)', 'Podgorica (Montenegro)', 'Port_Louis (Mauritius)',
                  'Port_Moresby (Papua New Guinea)', 'Port_of_Spain (Trinidad and Tobago)', 'Port_au_Prince (Haiti)',
                  'Port_aux_Francais (French Southern and Antarctic Lands)', 'Porto_Novo (Benin)',
                  'Port_Vila (Vanuatu)', 'Prague (Czech Republic)', 'Praia (Cape Verde)', 'Pretoria (South Africa)',
                  'Pristina (Kosovo)', 'Pyongyang (North Korea)', 'Quito (Ecuador)', 'Rabat (Morocco)',
                  'Rangoon (Myanmar)', 'Reykjavik (Iceland)', 'Riga (Latvia)', 'Riyadh (Saudi Arabia)',
                  'Road_Town (British Virgin Islands)', 'Rome (Italy)', 'Roseau (Dominica)', 'Saint_Georges (Grenada)',
                  'Saint_Helier (Jersey)', 'Saint_Johns (Antigua and Barbuda)', 'Saint_Peter_Port (Guernsey)',
                  'Saint_Pierre (Saint Pierre and Miquelon)', 'Saipan (Northern Mariana Islands)',
                  'San_Jose (Costa Rica)', 'San_Juan (Puerto Rico)', 'San_Marino (San Marino)',
                  'San_Salvador (El Salvador)', 'Sanaa (Yemen)', 'Santiago (Chile)',
                  'Santo_Domingo (Dominican Republic)', 'Sao_Tome (Sao Tome and Principe)',
                  'Sarajevo (Bosnia and Herzegovina)', 'Seoul (South Korea)', 'Singapore (Singapore)',
                  'Skopje (Macedonia)', 'Sofia (Bulgaria)', 'Stanley (Falkland Islands)', 'Stockholm (Sweden)',
                  'Suva (Fiji)', 'Taipei (Taiwan)', 'Tallinn (Estonia)', 'Tarawa (Kiribati)', 'Tashkent (Uzbekistan)',
                  'Tbilisi (Georgia)', 'Tegucigalpa (Honduras)', 'Tehran (Iran)', 'The_Settlement (Christmas Island)',
                  'The_Valley (Anguilla)', 'Thimphu (Bhutan)', 'Tirana (Albania)', 'Tokyo (Japan)',
                  'Torshavn (Faroe Islands)', 'Tripoli (Libya)', 'Tunis (Tunisia)', 'Ulaanbaatar (Mongolia)',
                  'Vaduz (Liechtenstein)', 'Valletta (Malta)', 'Vatican_City (Vatican City)', 'Victoria (Seychelles)',
                  'Vienna (Austria)', 'Vientiane (Laos)', 'Vilnius (Lithuania)', 'Warsaw (Poland)',
                  'Washington (United States)', 'Wellington (New Zealand)', 'West_Island (Cocos Islands)',
                  'Willemstad (CuraÃ§ao)', 'Windhoek (Namibia)', 'Yamoussoukro (Cote d Ivoire)', 'Yaounde (Cameroon)',
                  'Yaren (Nauru)', 'Yerevan (Armenia)', 'Zagreb (Croatia)']
        citylat = ['0', '24.466', '9.0833', '5.55', '-25.0667', '9.0333', '36.75', '-19.0167', '31.95', '52.35', '42.5',
                   '39.9333', '-18.9167', '-13.8167', '37.95', '15.3333', '51.1667', '-25.2667', '-9.1667', '37.9833',
                   '-21.2', '33.3333', '40.3833', '12.65', '4.8833', '13.75', '4.3667', '13.45', '17.3', '39.9167',
                   '33.8667', '44.8333', '17.25', '52.5167', '46.9167', '42.8667', '11.85', '4.6', '-15.7833', '48.15',
                   '-4.25', '13.1', '50.8333', '44.4333', '47.5', '-34.5833', '-3.3667', '30.05', '-35.2667', '10.4833',
                   '14', '18.35', '47', '6.9167', '9.5', '55.6667', '14.7333', '33.5', '-6.8', '23.7167', '-7.3',
                   '-8.5833', '11.5833', '25.2833', '54.15', '53.3167', '38.55', '27.1536', '8.4833', '-8.5167',
                   '-24.6333', '19.3', '6.8', '36.1333', '21.4667', '14.6167', '17.8833', '13.4667', '32.2833',
                   '21.0333', '-17.8167', '9.55', '23.1167', '60.1667', '-9.4333', '33.6833', '-6.1667', '-15.9333',
                   '31.7667', '31.7667', '4.85', '34.5167', '0.3167', '27.7167', '15.6', '-1.95', '-54.2833', '18',
                   '-29.05', '13.1333', '-4.3167', '3.1667', '29.3667', '50.4333', '-16.5', '0.3833', '-13.9667',
                   '-12.05', '38.7167', '46.05', '6.1167', '51.5', '78.2167', '-8.8333', '-15.4167', '49.6', '40.4',
                   '7.1', '3.75', '4.1667', '12.1333', '26.2333', '14.6', '-25.95', '60.1167', '18.0731', '-29.3167',
                   '-13.95', '-26.3167', '7.4833', '19.4333', '53.9', '2.0667', '43.7333', '6.3', '-34.85', '-11.7',
                   '55.75', '23.6167', '0', '0', '0', '0', '-1.2833', '25.0833', '12.1', '28.6', '13.5167', '35.1667',
                   '35.1833', '18.0667', '-22.2667', '-21.1333', '64.1833', '12.5167', '59.9167', '45.4167', '12.3667',
                   '-14.2667', '6.9167', '8.9667', '-17.5333', '5.8333', '48.8667', '18.0167', '11.55', '16.7',
                   '42.4333', '-20.15', '-9.45', '10.65', '18.5333', '-49.35', '6.4833', '-17.7333', '50.0833',
                   '14.9167', '-25.7', '42.6667', '39.0167', '-0.2167', '34.0167', '16.8', '64.15', '56.95', '24.65',
                   '18.4167', '41.9', '15.3', '12.05', '49.1833', '17.1167', '49.45', '46.7667', '15.2', '9.9333',
                   '18.4667', '43.9333', '13.7', '15.35', '-33.45', '18.4667', '0.3333', '43.8667', '37.55', '1.2833',
                   '42', '42.6833', '-51.7', '59.3333', '-18.1333', '25.0333', '59.4333', '-0.8833', '41.3167',
                   '41.6833', '14.1', '35.7', '-10.4167', '18.2167', '27.4667', '41.3167', '35.6833', '62', '32.8833',
                   '36.8', '47.9167', '47.1333', '35.8833', '41.9', '-4.6167', '48.2', '17.9667', '54.6833', '52.25',
                   '38.8833', '-41.3', '-12.1667', '12.1', '-22.5667', '6.8167', '3.8667', '-0.5477', '40.1667', '45.8']
        citylon = ['0', '54.3667', '7.5333', '-0.2167', '-130.0833', '38.7', '3.05', '-169.9167', '35.9333', '4.9167',
                   '1.5167', '32.8667', '47.5167', '-171.7667', '58.3833', '38.9333', '71.4167', '-57.6667',
                   '-171.8333', '23.7333', '-159.7667', '44.4', '49.8667', '-8', '114.9333', '100.5167', '18.5833',
                   '-16.5667', '-62.7167', '116.3833', '35.5', '20.5', '-88.7667', '13.4', '7.4667', '74.6', '-15.5833',
                   '-74.0833', '-47.9167', '17.1167', '15.2833', '-59.6167', '4.3333', '26.1', '19.0833', '-58.6667',
                   '29.35', '31.25', '149.1333', '-66.8667', '-61', '-64.9333', '28.85', '79.8333', '-13.7', '12.5833',
                   '-17.6333', '36.3', '39.2833', '90.4', '72.4', '125.6', '43.15', '51.5333', '-4.4833', '-6.2333',
                   '68.7667', '-13.2033', '-13.2333', '179.2167', '25.9', '-81.3833', '-58.15', '-5.35', '-71.1333',
                   '-90.5167', '-62.85', '144.7333', '-64.7833', '105.85', '31.0333', '44.05', '-82.35', '24.9333',
                   '159.95', '73.05', '106.8167', '-5.7167', '35.2333', '35.2333', '31.6167', '69.1833', '32.55',
                   '85.3167', '32.5333', '30.05', '-36.5', '-76.8', '167.9667', '-61.2167', '15.3', '101.7', '47.9667',
                   '30.5167', '-68.15', '9.45', '33.7833', '-77.05', '-9.1333', '14.5167', '1.2167', '-0.0833',
                   '15.6333', '13.2167', '28.2833', '6.1167', '-3.6833', '171.3833', '8.7833', '73.5', '-86.25',
                   '50.5667', '120.9667', '32.5833', '19.9', '-63.0822', '27.4833', '-171.9333', '31.1333', '134.6333',
                   '-99.1333', '27.5667', '45.3333', '7.4167', '-10.8', '-56.1667', '43.2333', '37.6', '58.5833', '0',
                   '0', '0', '0', '36.8167', '-77.35', '15.0333', '77.2', '2.1167', '33.3667', '33.3667', '-15.9667',
                   '166.45', '-175.2', '-51.75', '-70.0333', '10.75', '-75.7', '-1.5167', '-170.7', '158.15',
                   '-79.5333', '-149.5667', '-55.1667', '2.3333', '-63.0333', '104.9167', '-62.2167', '19.2667',
                   '57.4833', '147.1833', '-61.5167', '-72.3333', '70.2167', '2.6167', '168.3167', '14.4667',
                   '-23.5167', '28.2167', '21.1667', '125.75', '-78.5', '-6.8167', '96.15', '-21.95', '24.1', '46.7',
                   '-64.6167', '12.4833', '-61.4', '-61.75', '-2.1', '-61.85', '-2.5333', '-56.1833', '145.75',
                   '-84.0833', '-66.1167', '12.4167', '-89.2', '44.2', '-70.6667', '-69.9', '6.7333', '18.4167',
                   '126.9833', '103.85', '21.4333', '23.3167', '-57.85', '18.05', '178.4167', '121.5167', '24.7167',
                   '169.5333', '69.25', '44.8333', '-87.2167', '51.4167', '105.7167', '-63.05', '89.6333', '19.8167',
                   '139.75', '-6.7667', '13.1667', '10.1833', '106.9167', '9.5167', '14.5', '12.45', '55.45', '16.3667',
                   '102.6', '25.3167', '21', '-77', '174.7833', '96.8333', '-68.9167', '17.0833', '-5.2667', '11.5167',
                   '166.9209', '44.5', '16']

        self.label0 = tk.Label(parent)
        self.label0.place(relx=0, rely=0.69, relheight=0.4, relwidth=1)
        self.label0.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="")

        self.Entry1 = tk.Entry(parent, textvariable=frequency)  # frequency box
        self.Entry1.place(relx=0.01, rely=0.892, height=24, relwidth=0.22)
        self.Entry1.configure(background="white", disabledforeground=dfgc, font="TkFixedFont", foreground=fgc,
                              insertbackground=fgc, width=214)
        self.Entry1.insert(0, "Enter Frequency here (kHz)")
        self.Entry1.bind('<FocusIn>', self.clickfreq)
        self.Entry1.bind('<Leave>', self.choosedfreq)

        self.Button1 = tk.Button(parent)  # Start recording button
        self.Button1.place(relx=0.77, rely=0.89, height=24, relwidth=0.10)
        self.Button1.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start recording", command=self.clickstart, state="disabled")

        self.Button2 = tk.Button(parent)  # Stop button
        self.Button2.place(relx=0.88, rely=0.89, height=24, relwidth=0.1)
        self.Button2.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start TDoA proc", command=self.clickstop, state="disabled")

        self.TCombobox1 = ttk.Combobox(parent, state="readonly")  # IQ BW Combobox
        self.TCombobox1.place(relx=0.24, rely=0.892, height=24, relwidth=0.1)
        self.TCombobox1.configure(font="TkTextFont",
                                  values=["IQ bandwidth", "10000", "5000", "4000", "3000", "2000", "1000", "500", "400",
                                          "300", "200", "100", "50"])
        self.TCombobox1.current(0)
        self.TCombobox1.bind("<<ComboboxSelected>>", self.bwchoice)

        #  2nd part of buttons
        self.citylist = ttk.Combobox(parent, values=list(city), state="readonly")  # KNOWN POINT to display on TDoA map
        self.citylist.place(relx=0.01, rely=0.94, relheight=0.03, relwidth=0.45)
        self.citylist.current(0)
        self.citylist.bind('<<ComboboxSelected>>', self.citychoice)

        self.label7 = tk.Label(parent)  # LABEL for KNOWN POINT coordinates
        self.label7.place(relx=0.52, rely=0.935, relheight=0.04, relwidth=0.3)
        self.label7.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="", anchor="w")
        print self.label7.cget("text")
        self.Button4 = tk.Button(parent)  # KNOWN POINT RESET
        self.Button4.place(relx=0.465, rely=0.94, height=22, relwidth=0.05)
        self.Button4.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="RESET", command=self.resetcity, state="disabled")

        self.Button3 = tk.Button(parent)  # Update button
        self.Button3.place(relx=0.90, rely=0.94, height=24, relwidth=0.08)
        self.Button3.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="update map", command=self.runupdate, state="normal")

        self.Text2 = tk.Text(parent)  # console window
        self.Text2.place(relx=0.005, rely=0.7, relheight=0.18, relwidth=0.6)
        self.Text2.configure(background="black", font="TkTextFont", foreground="red", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")
        self.writelog("This is " + VERSION + " (ounaid@gmail.com), a GUI written for python 2.7 / Tk")
        self.writelog("All credits to Christoph Mayer for his excellent TDoA work (https://github.com/hcab14/TDoA)")
        self.writelog("INFO:     Green = available nodes    -    Red = busy nodes")
        self.writelog("INFO: This is not real-time display, use update map button to refresh")
        self.writelog("TIPS: You can move the map by using left mouse button")
        vsb2 = ttk.Scrollbar(parent, orient="vertical", command=self.Text2.yview)  # adding scrollbar to console
        vsb2.place(relx=0.6, rely=0.7, relheight=0.18, relwidth=0.02)
        self.Text2.configure(yscrollcommand=vsb2.set)

        self.Text3 = tk.Text(parent)  # IQ recs file size window
        self.Text3.place(relx=0.624, rely=0.7, relheight=0.18, relwidth=0.37)
        self.Text3.configure(background="white", font="TkTextFont", foreground="black", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")

        menubar = Menu(self)
        parent.config(menu=menubar)
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Map Settings", menu=filemenu)
        submenu = Menu(filemenu, tearoff=0)
        submenu1 = Menu(filemenu, tearoff=0)
        submenu2 = Menu(filemenu, tearoff=0)
        filemenu.add_cascade(label='Default map', menu=submenu1, underline=0)
        submenu1.add_command(label="Grayscale",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_grayscale.jpg'))
        submenu1.add_command(label="Sat",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_sat.jpg'))
        submenu1.add_command(label="Black Marble (gamma=1)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_blackmarble-1.jpg'))
        submenu1.add_command(label="Black Marble (gamma=1.5)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_blackmarble-1.5.jpg'))
        submenu1.add_command(label="DNB (night)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_dnb.jpg'))
        submenu1.add_command(label="Snow cover",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_snow.jpg'))
        submenu1.add_command(label="Snow cover 2",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_snow2.jpg'))
        filemenu.add_cascade(label='Display Filter', menu=submenu2, underline=0)
        submenu2.add_command(label="All nodes", command=lambda *args: self.setMapFilter('0'))
        submenu2.add_command(label="Standard + Favorites", command=lambda *args: self.setMapFilter('1'))
        submenu2.add_command(label="Favorites", command=lambda *args: self.setMapFilter('2'))
        submenu2.add_command(label="Blacklisted", command=lambda *args: self.setMapFilter('3'))
        menubar.add_command(label="How to TDoA with this tool", command=self.about)
        menubar.add_command(label="General infos", command=self.general)

    # -------------------------------------------------LOGGING------------------------------------------------------
>>>>>>> Add files via upload

    def writelog(self, msg):  # the main console log text feed
        self.Text2.insert('end -1 lines', "[" + str(time.strftime('%H:%M.%S', time.gmtime())) + "] - " + msg + "\n")
        time.sleep(0.01)
        self.Text2.see('end')

<<<<<<< HEAD
    @staticmethod
    def help():
        master = Tk()
        w = Message(master, text="""
    1/ Hold Left-mouse button to move the World Map to your desired location
    2/ Enter the frequency, between 0 and 30000 (kHz)
    3/ Choose from the top bar menu a specific bandwidth for the IQ recordings if necessary
    4/ Choose KiwiSDR nodes by left-click on them and select \"Add:\" command to add them to the list (min=3 max=6)
    5/ You can remove undesired nodes from the list by using the \"Remove:\" command
    6/ Hold Right-mouse button to drag a rec rectangle to set the TDoA computed map geographical boundaries 
       or select one of the presets from the top bar menu, you can cancel by drawing again by hand or choose RESET
    7/ Type some text in the bottom left box to search for a city or TX site to display on final TDoA map (if needed)
    8/ Click Start Recording button and wait for some seconds (Recorded IQ files size are displayed in the white window)
    9/ Click Start TDoA button and WAIT until the TDoA process stops! (it may take some CPU process time!)
    10/ Calculated TDoA map is automatically displayed as 'Figure1' ghostscript pop-up window and it will close itself
    11/ A PDF file will be created automaticaly, it takes time, so wait for the final popup window
    12/ All TDoA process files (wav/m/pdf) will be automaticaly saved in a subdirectory of TDoA/iq/
    """, width=1000, font="TkFixedFont 8", bg="white", anchor="center")
        w.pack()

    @staticmethod
    def about():  # About menu
        master = Tk()
        w = Message(master, text="""
    Welcome to """ + VERSION + """

    I've decided to write that python GUI in order to compute the TDoA stuff faster & easier.
    Please note that I have no credits in all the GNU Octave calculation process (TDoA/m/*.m files).
    Also I have no credits in the all the kiwirecorder codes (TDoA/kiwiclient/*.py files).

    A backup copy of processed ".wav", ".m", ".pdf" files is automatically made in a TDoA/iq/ subdirectory
    Check TDoA/iq/<timeofprocess>_F<frequency>/ to find your files.
    You can compute again your IQ recordings, to do so, just run the ./recompute.sh script
    
    The World map is static, click UPDATE button to get an updated node list, only GPS enabled nodes are displayed
    KiwiSDR node informations are retrieved in real time when node square icon is clicked on the map

    Thanks to Christoph Mayer for the public release of his TDoA GNU-Octave scripts
    Thanks to John Seamons for including the GPS timestamps in IQ files
    Thanks to Dmitry Janushkevich for the original kiwirecorder project python scripts
    Thanks to Pierre Ynard (linkfanel) for the KiwiSDR network node listing used as source for GUI map update
    Thanks to Marco Cogoni (IS0KYB) for the KiwiSDR network SNR measurements listing used as source for GUI map update
    And.. Thanks to all KiwiSDR hosts with GPS activated and decent RX on both HF & GPS freqs...

    linkz 
    
    feedback, features request or help : contact me at ounaid at gmail dot com or IRC freenode #wunclub / #priyom
    """, width=1000, font="TkFixedFont 8", bg="white", anchor="center")
        w.pack()

    def map_preset(self, pmap):
        global mapboundaries_set, lon_min_map, lon_max_map, lat_min_map, lat_max_map, sx0, sx1, sy0, sy1, mappreset
        global map_preset, map_manual
        if map_preset == 1:
            self.member1.deletePoint(sx0, sy0, "mappreset")
        if pmap != 20:
            #  a= min_longitude  b= max_latitude  c= max_longitude  d= min_latitude
            if pmap == 0:  # Europe
                p = {'a': -12, 'b': 72, 'c': 50, 'd': 30}
            if pmap == 1:  # Africa
                p = {'a': -20, 'b': 40, 'c': 55, 'd': -35}
            if pmap == 2:  # Middle-East
                p = {'a': 25, 'b': 45, 'c': 65, 'd': 10}
            if pmap == 3:  # South America
                p = {'a': -85, 'b': 15, 'c': -30, 'd': -60}
            if pmap == 4:  # Oceania
                p = {'a': 110, 'b': -10, 'c': 180, 'd': -50}
            if pmap == 5:  # East Asia
                p = {'a': 73, 'b': 55, 'c': 147, 'd': 15}
            if pmap == 6:  # Central America
                p = {'a': -120, 'b': 33, 'c': -60, 'd': 5}
            if pmap == 7:  # South-East Asia
                p = {'a': 85, 'b': 30, 'c': 155, 'd': -12}
            if pmap == 8:  # South Asia
                p = {'a': 60, 'b': 39, 'c': 100, 'd': 4}
            if pmap == 9:  # North America
                p = {'a': -170, 'b': 82, 'c': -50, 'd': 13}
            if pmap == 10:  # East Russia
                p = {'a': 27, 'b': 77, 'c': 90, 'd': 40}
            if pmap == 11:  # West Russia
                p = {'a': 90, 'b': 82, 'c': 180, 'd': 40}
            if pmap == 12:  # USA
                p = {'a': -125, 'b': 55, 'c': -66, 'd': 20}
            if pmap == 13:  # World
                p = {'a': -179, 'b': 89, 'c': 179, 'd': -59}
                tkMessageBox.showinfo("WARNING",
                                      message="Using the entire World as TDoA map boundaries will take MANY CPU TIME.")
            ## next map boundaries presets come here
            sx0 = (1907.5 + ((float(p['a']) * 1910) / 180))
            sx1 = (1907.5 + ((float(p['c']) * 1910) / 180))
            if float(p['b']) > 0:  # point is located in North Hemisphere
                sy0 = (987.5 - (float(p['b']) * 11))
                sy1 = (987.5 - (float(p['d']) * 11))
            else:  # point is located in South Hemisphere
                sy0 = (987.5 + (float(0 - (float(p['b']) * 11))))
                sy1 = (987.5 + (float(0 - float(p['d'])) * 11))
            self.member1.canvas.create_rectangle(sx0, sy0, sx1, sy1, tag="mappreset", outline='yellow')
            self.member1.deletePoint(sx0, sy0, "mapmanual")
            lon_min_map = p['a']
            lat_max_map = p['b']
            lon_max_map = p['c']
            lat_min_map = p['d']
            mapboundaries_set = 1
            map_preset = 1
            map_manual = 0
            self.label4.configure(
                text="[LATITUDE] range: " + str(lat_min_map) + "° " + str(lat_max_map) + "°  [LONGITUDE] range: " + str(
                    lon_min_map) + "° " + str(lon_max_map) + "°")
        else:  # Reset the previous preset and permit the manual setting of map boundaries
            self.member1.deletePoint(sx0, sy0, "mappreset")
            mapboundaries_set = None
            map_preset = 0
            self.member1.rect = None
            map_manual = 1
            lon_min_map = None
            lat_max_map = None
            lon_max_map = None
            lat_min_map = None

    def setmapfilter(self, mapfl):
        ReadConfigFile().read_cfg()
        SaveConfigFile().save_cfg("mapfl", mapfl)
        Restart().run()

    def min_gps_filter(self):
        ReadConfigFile().read_cfg()
        gps_per_min_filter = tkSimpleDialog.askinteger("Input", "Min GPS fixes/min? (" + gpsfl + ")", parent=self,
                                                       minvalue=0, maxvalue=30)
        if gps_per_min_filter is None:
            gps_per_min_filter = 0
        SaveConfigFile().save_cfg("gpsfl", gps_per_min_filter)
        Restart().run()

    def color_change(self, value):  # node color choices
        global colorline
        color_n = askcolor()
        color_n = color_n[1]
        ReadConfigFile().read_cfg()
        if color_n:
            if value == 0:
                colorline = color_n + "," + colorline[1] + "," + colorline[2] + "," + colorline[3]
            elif value == 1:
                colorline = colorline[0] + "," + color_n + "," + colorline[2] + "," + colorline[3]
            elif value == 2:
                colorline = colorline[0] + "," + colorline[1] + "," + color_n + "," + colorline[3]
            elif value == 3:
                colorline = colorline[0] + "," + colorline[1] + "," + colorline[2] + "," + color_n
            SaveConfigFile().save_cfg("nodecolor", colorline)
            Restart().run()
        else:
            pass

    def choose_map(self):
        mapname = tkFileDialog.askopenfilename(initialdir="maps")
        if not mapname or not mapname.lower().endswith(('.png', '.jpg', '.jpeg')):
            tkMessageBox.showinfo("", message="Error, select png/jpg/jpeg files only.\n Loading default map now.")
            mapname = "maps/directTDoA_map_grayscale_with_sea.jpg"
        ReadConfigFile().read_cfg()
        SaveConfigFile().save_cfg("mapc", "maps/" + os.path.split(mapname)[1])
        Restart().run()
=======
    def writelog2(self, msg):  # the Checkfile log text feed
        global t
        if t == 0:
            self.Text3.delete("0.0", END)
            t = 1
        self.Text3.insert('end -1 lines', msg + "\n")
        time.sleep(0.01)
        self.Text2.see('end')

    @staticmethod
    def about():  # about menu
        tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                              message="""
    ø¤º°`°º¤ø,¸,ø¤°º¤ø-=[HOW TO USE THE GUI]=-ø¤º°`°º¤ø,¸,ø¤°º¤ø

    1/ Choose nodes by clicking on them (min=3 max=6)
        (Red squares are busy nodes and can't be used to record atm)
    
    2/ Enter a frequency and choose IQ recording bandwidth (if needed)
    (Note: recorded center frequency will be +5kHz by default)
    ex: if you enter 12540.2 it will record 12545.2 cf (-5kHz/+5kHz)
    
    3/ Hold Left-mouse button to move the World Map to your desired
    location
    
    4/ Hold Right-mouse button to drag a rec rectangle to setup
        TDoA computed map geographical boundaries (if needed)
    (defaults: LAT from 30° to 60° & LON from -10 to 20° =~ Europe)
    
    5/ Choose a city from the list to display on map (if needed)
    
    6/ Click Start Recording button and wait for some seconds
        (Recorded IQ files size are displayed in the white window)
    
    7/ Click Start TDoA button and WAIT until the TDoA process stops! 
        (it may take some CPU process time!)
        
    8/ Calculated TDoA map automatically displayed as picture pop-up
    
    9/ There is a .pdf created in TDoA/pdf directory, this file
        creation process takes more time !!!
    
        PLEASE WAIT UNTIL THE GUI STOPS BY ITSELF
""")

    @staticmethod
    def general():  # about menu
        tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                              message="""
    A backup copy of .wavs, .m and gnss_pos files is automatically
    made in a new "iq/<timeofprocess>_F<frequency>/" directory to 
    post-compute again the recs, 
    ex: for map boundaries modifications (check the saved .m file)
    or to re-compute w/o a specific node
 
    The World map is not real-time, click UPDATE button to refresh,
    of course, only GPS enabled nodes are displayed...
    
    Some errors are possible in the map node placement:
    The coordinates can be manually set by users, even if their GPS
    is activated...""")

    @staticmethod
    def setMapFilter(mapfilter):
        mapfilter = mapfilter
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % (map))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(black))
        u.close()
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    @staticmethod
    def saveconfig(map):  # save config menu
        global bbox2, mapfilter
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
        c.close()
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % (map))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfilter)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(black))
        u.close()
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)
>>>>>>> Add files via upload

    def runupdate(self):  # if UPDATE button is pushed
        self.Button1.configure(state="disabled")
        self.Button2.configure(state="disabled")
        self.Button3.configure(state="disabled")
<<<<<<< HEAD
        self.Button4.configure(state="disabled")
        CheckUpdate(self).start()  # start the update thread

    def purgenode(self):  # when Purge node list button is pushed
        global fulllist, ultimatelist
        ultimatelist = []
        fulllist = []
        app.title(VERSION)
        self.writelog("The full node listing has been erased.")


    # ---------------------------------------------------MAIN-----------------------------------------------------------

    def set_iq(self, m):
        global lpcut, hpcut, currentbw
        try:
            if 5 < int(self.Entry1.get()) < 30000:
                self.writelog("Setting IQ bandwidth at " + m + " Hz       | " + str(
                    float(self.Entry1.get()) - (float(m) / 2000)) + " | <---- " + str(
                    float(self.Entry1.get())) + " ----> | " + str(
                    float(self.Entry1.get()) + (float(m) / 2000)) + " |")
                currentbw = m
                lpcut = hpcut = int(m) / 2
            else:
                self.writelog("Error, frequency is too low or too high")
        except ValueError as ve:
            currentbw = m
            lpcut = hpcut = int(m) / 2
            self.writelog("Setting IQ bandwidth at " + m + " Hz")
            pass

    def set_bw(self):
        try:
            ReadConfigFile().read_cfg()
            SaveConfigFile().save_cfg("defaultbw", currentbw)
            Restart().run()
        except:
            pass

    def checkversion(self):
        try:
            checkver = requests.get('https://raw.githubusercontent.com/llinkz/directTDoA/master/README.md', timeout=2)
            gitsrctext = checkver.text.split("\n")
            if float(gitsrctext[0][2:].split("v", 1)[1]) > float(VERSION.split("v", 1)[1][:4]):
                tkMessageBox.showinfo(title="UPDATE INFORMATION", message=str(gitsrctext[0][2:]) + " has been released !\n\nCheck https://github.com/llinkz/directTDoA for change log & update.\n\nI hope you enjoy this software\n\n73 from linkz")
            else:
                pass
        except:
            print "Unable to verify version information. Sorry."
            pass

    # def checksnr(self):  # work in progress
    #     global snrcheck, snrfreq
    #     snrcheck = True
    #     snrfreq = float(self.Entry1.get())
    #     snrfreq = snrfreq + 202.94
    #     snrfreq = str(snrfreq)

    def clickstart(self):
        global frequency, latmin, latmax, lonmin, lonmax, lpcut, hpcut
        global starttime, x1, x2, y1, y2, mapboundaries_set, rec_in_progress

        if rec_in_progress == 1:  # stop rec process
            os.kill(proc2_pid, signal.SIGTERM)  # kills the kiwirecorder.py process
            time.sleep(0.5)
            rec_in_progress = 0
            self.Button1.configure(text="Start recording")
            self.Button4.configure(state="normal")
            if (ultimate.get()) is 1:
                self.Button2.configure(text="", state="disabled")
            self.create_m_file()
            self.writelog("IQ Recordings manually stopped... files has been saved in " + str(
                os.sep + os.path.join('TDoA', 'iq') + os.sep + starttime) + "_F" + str(frequency) + str(
                os.sep))
            if (ultimate.get()) is 1:
                try:
                    webbrowser.open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(frequency))
                except ValueError as e:
                    print e

        else:  # start rec process
            if (ultimate.get()) is 0 and mapboundaries_set is None:
                tkMessageBox.showinfo("WARNING",
                                      message="Set TDoA map Geographical boundaries, right click and draw red rectangle or select one of presets via the top bar menu.")
            else:
                lonmin = str((((bbox2[0] - 1910) * 180) / 1910)).rsplit('.')[0]  # LONGITUDE MIN
                lonmax = str(((bbox2[2] - 1910) * 180) / 1910).rsplit('.')[0]  # LONGITUDE MAX
                latmax = str(0 - ((bbox2[1] - 990) / 11)).rsplit('.')[0]  # LATITUDE MAX
                latmin = str(20 - ((bbox2[3] - 990) / 11)).rsplit('.')[0]  # LATITUDE MIN

                starttime = str(time.strftime('%Y%m%dT%H%M%S'))
                if self.Entry1.get() == '' or float(self.Entry1.get()) < 0 or float(self.Entry1.get()) > 30000:
                    self.writelog("ERROR: Please check the frequency !")
                elif (ultimate.get()) is 0 and len(fulllist) < 3:  # debug
                    self.writelog("ERROR: Select at least 3 nodes for TDoA processing !")
                elif (ultimate.get()) is 1 and len(ultimatelist) == 0:
                    self.writelog("ERROR: ultimateTDoA listing is empty !")
                else:
                    frequency = str(float(self.Entry1.get()))
                    self.Button1.configure(text="Stop recording")
                    if (ultimate.get()) is 0:
                        self.Button2.configure(text="Start TDoA proc", state="normal")
                    self.Button3.configure(state="disabled")
                    self.Button4.configure(state="disabled")
                    for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                        os.remove(wavfiles)
                    time.sleep(0.2)
                    self.Text3.delete("0.0", END)
                    StartKiwiSDR(self).start()
                    rec_in_progress = 1

    def clickstop(self):
        global proc_pid, proc2_pid, rec_in_progress, tdoa_in_progress
        if tdoa_in_progress == 1:  # Abort TDoA process
            self.Button1.configure(text="Start recording", state="normal")
            self.Button2.configure(text="", state="disabled")
            self.Button4.configure(state="normal")
            os.kill(proc_pid, signal.SIGTERM)  # kills the octave process
            self.writelog("Octave process has been aborted...")
            for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                os.remove(wavfiles)
            tdoa_in_progress = 0

        else:  # Start TDoA process
            tdoa_in_progress = 1
            os.kill(proc2_pid, signal.SIGTERM)  # kills the kiwirecorder.py process
            self.Button1.configure(text="", state="disabled")
            self.Button2.configure(text="Abort TDoA proc")
            if rec_in_progress == 1:
                self.create_m_file()
            self.writelog("Now running Octave process... please wait...")
            time.sleep(0.5)
            rec_in_progress = 0
            OctaveProcessing(self).start()

    def create_m_file(self):
        global IQfiles, frequency, varfile, selectedlat, selectedlon, currentbw
        global selectedcity, starttime, latmin, latmax, lonmin, lonmax
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        for file in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            IQfiles.append(os.path.split(file)[1])
        firstfile = IQfiles[0]
        varfile = str(firstfile.split("_", 2)[1].split("_", 1)[0])

        if (ultimate.get()) is 1:  # generate proc_tdoa_frequency.empty + compute_ultimate.sh---------------------------
            with open(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m", "w") as g:
                g.write("## -*- octave -*-\n")
                g.write("## This file was auto-generated by " + VERSION + "\n\n")
                g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n\n")
                g.write("""  # nodes
  
  input = tdoa_read_data(input);

  ## 200 Hz high-pass filter (removed in directTDoA v4.00)
  #  b = fir1(1024, 500/12000, 'high');
  n = length(input);
  #  for i=1:n
  #    input(i).z      = filter(b,1,input(i).z)(512:end);
  #  end

  tdoa  = tdoa_compute_lags(input, struct('dt',     12000,            # 1-second cross-correlation intervals
                                          'range',  0.005,            # peak search range is +-5 ms
                                          'dk',    [-2:2],            # use 5 points for peak fitting
                                          'fn', @tdoa_peak_fn_pol2fit # fit a pol2 to the peak
                                          ));
  for i=1:n
    for j=i+1:n
      tdoa(i,j).lags_filter = ones(size(tdoa(i,j).gpssec))==1;
    end
  end

  plot_info = struct('lat', [ """)
                g.write(str(lat_min_map) + ":0.05:" + str(lat_max_map) + "],\n")
                g.write("                     'lon', [ " + str(lon_min_map) + ":0.05:" + str(lon_max_map) + "],\n")
                g.write("                     'plotname', 'TDoA_")
                g.write(varfile + "',\n")
                g.write("                     'title', 'CF=" + frequency + " BW=" + str(currentbw) + " [" + str(
                    float(frequency) - (float(currentbw) / 2000)) + " <-> " + str(
                    float(frequency) + (float(currentbw) / 2000)) + "] - " + str(
                    datetime.utcnow().strftime('%d %b %Y %H%Mz')) + "'")

                if selectedlat == "" or selectedlon == "":
                    g.write(",\n                     'known_location', struct('coord', [0 0],\n")
                    g.write("                                              \'name\',  \'" "\')\n")
                    g.write("                    );\n\n\n")
                    g.write("  tdoa = tdoa_plot_map(input, tdoa, plot_info);\n")
                    g.write("\nsystem(\"cp pdf" + os.sep + "TDoA_" + str(varfile) + ".pdf iq" + os.sep + str(starttime) + "_F" + str(frequency) + os.sep + "TDoA_" + str(varfile) + "_`date -u +%d%b%Y_%H%M%Sz`.pdf\")")
                    g.write("\ndisp(\"finished\");\n")
                    g.write("endfunction\n")
                else:
                    g.write(
                        ",\n                     'known_location', struct('coord', [" + str(selectedlat) + " " + str(
                            selectedlon) + "],\n")
                    g.write("                                              \'name\',  \'" + str(
                        selectedcity.rsplit(' (')[0]).replace('_', ' ') + "\')\n")
                    g.write("""                    );\n

  tdoa = tdoa_plot_map(input, tdoa, plot_info);

system("cp pdf""" + os.sep + """TDoA_""" + str(varfile) + """.pdf iq""" + os.sep + str(starttime) + """_F""" + str(frequency) + os.sep + """TDoA_""" + str(varfile) + """_`date -u +%d%b%Y_%H%M%Sz`.pdf")
disp("finished");
endfunction """)

            g.close()
            self.writelog(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".empty file created")
            # backup of IQ, gnss_pos and .m file in a new directory named by the datetime process start and frequency
            time.sleep(0.5)
            os.makedirs(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(frequency))
            for file in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                copyfile(file, os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + file.rsplit(os.sep, 1)[1])
            copyfile(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m",
                     os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                         frequency) + os.sep + "proc_tdoa_" + varfile + ".empty")
            with open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + "compute_ultimate.sh", "w") as recompute:
                recompute.write("""#!/bin/sh
## This file is intended to copy back *.wav to iq directory
## and to open a node list selection script so you can choose which nodes you want to use to create .m file and run TDoA
cp ./*.wav ../
echo "### ultimateTDoA dynamic octave file process started..."
echo " "
declare -a FILELIST
declare -a NODELIST
declare PROCFILE
declare TEMPFILE

for e in *.empty; do 
    TEMPFILE=$e
done
PROCFILE="${TEMPFILE/empty/m}"
cp $TEMPFILE $PROCFILE

for f in *.wav; do 
    FILELIST[${#FILELIST[@]}+1]=$(echo "$f");
done

for ((g=1;g<=${#FILELIST[@]};g++)); do
	printf '%s %sKB\\n' "$g - ${FILELIST[g]}" "`du -k ${FILELIST[g]} |cut -f1`"
done
echo " "
echo "Enter node numbers you want to include in the TDoA process (min=3 max=6), separate them with a comma (ctrl+c to exit)"
read nodeschoice

nodes=$(echo $nodeschoice | tr "," "\\n")
for node in $nodes; do
	NODELIST[${#NODELIST[@]}+1]=$(echo "${FILELIST[node]}");
done

if [[ ("${#NODELIST[@]}" -gt 2) && ("${#NODELIST[@]}" -lt 7 ) ]]; then
	i="${#NODELIST[@]}"
	for ((h=1;h<=${#NODELIST[@]};h++)); do	
		sed -i '/\  # nodes/a \ \ input('$i').fn    = fullfile('\\''iq'\\'', '\\'''${NODELIST[h]}''\\'');' $PROCFILE
		((i--))
	done
else
	echo "ERROR: process aborted, please choose between 3 and 6 nodes !"
	sleep 2
	exit
fi

read -n1 -p "Do you want to edit $PROCFILE file before running octave process ? [y,n] " next 
case $next in  
  y|Y) $EDITOR $PROCFILE && cp $PROCFILE ../../ && cd ../.. && octave-cli $PROCFILE ;;
  n|N) cp $PROCFILE ../../ && cd ../.. && octave-cli $PROCFILE ;;
  *) exit ;;
esac""")
                recompute.close()
                os.chmod(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + "compute_ultimate.sh", 0o777)

        else:  # create standard TDoA mode files -----------------------------------------------------------------------
            with open(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m", "w") as g:
                g.write("## -*- octave -*-\n")
                g.write("## This file was auto-generated by " + VERSION + "\n\n")
                g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n\n")
                for i in range(len(IQfiles)):
                    g.write("  input(" + str(i + 1) + ").fn    = fullfile('iq', '" + str(IQfiles[i]) + "');\n")
                g.write("""
  input = tdoa_read_data(input);

  ## 200 Hz high-pass filter (removed in directTDoA v4.00)
#  b = fir1(1024, 500/12000, 'high');
  n = length(input);
#  for i=1:n
#    input(i).z      = filter(b,1,input(i).z)(512:end);
#  end

=======
        RunUpdate(self).start()  # start the update thread

    # ---------------------------------------------------MAIN-------------------------------------------------------
    def clickfreq(self, ff):
        self.Button1.configure(state='normal')
        self.Entry1.delete(0, 'end')
        self.Button1.configure(state='normal')

    def choosedfreq(self, ff):
        global frequency
        frequency = self.Entry1.get()

    def bwchoice(self, m):  # affects only the main window apparance, real-time
        global bw, lpcut, hpcut
        bw = self.TCombobox1.get()
        self.writelog("|<----" + str(int(bw)/2) + "Hz ----[tune frequency]---- " + str(int(bw)/2) + "Hz ---->|")
        lpcut = hpcut = int(bw) / 2

    def citychoice(self, m):  # affects only the main window apparance, real-time
        global city, citylat, citylon, selectedlat, selectedlon, selectedcity, zoomlevel
        self.label7.configure(text="LAT: " + str(citylat[city.index(self.citylist.get())]) + " LON: " + str(
            citylon[city.index(self.citylist.get())]))
        selectedlat = str(citylat[city.index(self.citylist.get())])
        selectedlon = str(citylon[city.index(self.citylist.get())])
        selectedcity = self.citylist.get()
        self.member1.createPoint(selectedlat, selectedlon, selectedcity)
        self.citylist.configure(state='disabled')
        self.Button4.configure(state='normal')

    def resetcity(self):
        global selectedlat, selectedlon
        self.citylist.configure(state='normal')
        self.citylist.current(0)
        self.citylist.selection_clear()
        self.label7.configure(text="")
        selectedlat = ""
        selectedlon = ""
        self.member1.deletePoint(selectedlat, selectedlon, selectedcity)

    def checksnr(self):
        global snrcheck, snrfreq
        snrcheck = True
        snrfreq = float(self.Entry1.get())
        snrfreq = snrfreq + 202.94
        snrfreq = str(snrfreq)

    def clickstart(self):
        global namelist, hostlist, namelisting, frequency, hostlisting, latmin, latmax, lonmin, lonmax, lpcut, hpcut
        global serverlist, portlist, portlisting, starttime, x1, x2, y1, y2
        lonmin = str((((bbox2[0] - 1910) * 180) / 1910)).rsplit('.')[0]  # LONGITUDE MIN
        lonmax = str(((bbox2[2] - 1910) * 180) / 1910).rsplit('.')[0]  # LONGITUDE MAX
        latmax = str(0 - ((bbox2[1] - 990) / 11)).rsplit('.')[0]  # LATITUDE MAX
        latmin = str(20 - ((bbox2[3] - 990) / 11)).rsplit('.')[0]  # LATITUDE MIN
        namelisting = ""
        hostlisting = ""
        portlisting = ""
        for i in range(len(serverlist)):

            ip = re.search(
                r'\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                serverlist[i])
            if ip:
                namelisting = namelisting + "ip" + str(ip.group(1)) + str(ip.group(2)) + str(ip.group(3)) + str(ip.group(4)) + ','
            else:
                namelisting = namelisting + serverlist[i].replace(".", "").replace("-", "") + ','
        namelisting = "--station=" + namelisting[:-1]
        for i in range(len(serverlist)):
            hostlisting = hostlisting + serverlist[i] + ','
        hostlisting = hostlisting[:-1]
        for i in range(len(portlist)):
            portlisting = portlisting + portlist[i] + ','
        portlisting = portlisting[:-1]
        starttime = str(time.strftime('%Y%m%dT%H%M%S'))
        if self.Entry1.get() == 'Enter Frequency here (kHz)':
            self.writelog("ERROR: Please enter a frequency first !")
        elif self.Entry1.get() == '' or float(self.Entry1.get()) < 0 or float(self.Entry1.get()) > 30000:
            self.writelog("ERROR: Please check the frequency !")
        elif len(namelist) < 1:
            self.writelog("ERROR: Select at least 3 nodes for TDoA processing !")
        else:
            frequency = str(float(self.Entry1.get()))
            self.Button1.configure(state="disabled")
            self.Button2.configure(state="normal")
            self.Button3.configure(state='disabled')
            if platform.system() == "Windows":
                for wavfiles in glob.glob("..\\iq\\*wav"):
                    os.remove(wavfiles)
                for gnssfiles in glob.glob("..\\gnss_pos\\*txt"):
                    os.remove(gnssfiles)
            if platform.system() == "Linux":
                for wavfiles in glob.glob("../iq/*wav"):
                    os.remove(wavfiles)
                for gnssfiles in glob.glob("../gnss_pos/*txt"):
                    os.remove(gnssfiles)
            time.sleep(1)
            StartKiwiSDR(self).start()

    def clickstop(self):
        global IQfiles, frequency, varfile, proc2, selectedlat, selectedlon
        global selectedcity, starttime, latmin, latmax, lonmin, lonmax, nbfile
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        if lat_min_map == "":  # set default map geo boundaries
            lat_min_map = 30
            lat_max_map = 60
            lon_min_map = -10
            lon_max_map = 20
        os.kill(proc2.pid, signal.SIGINT)
        # CheckFileSize(self).stop()
        if platform.system() == "Windows":
            for file in os.listdir("..\iq\\"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])

        if platform.system() == "Linux":
            for file in os.listdir("../iq//"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])
        firstfile = IQfiles[0]
        varfile = str(firstfile.split("_", 2)[1].split("_", 1)[0])
        for i in range(len(IQfiles)):
            print IQfiles[i]
            nbfile = len(IQfiles)

        self.writelog("IQ Recording(s) has been stopped...")
        self.Button2.configure(state="disabled")

        # make a backup of IQ and gnss_pos files in a new directory named by the datetime process start and frequency
        time.sleep(1)
        if platform.system() == "Windows":
            os.makedirs("..\iq\\" + starttime + "_F" + str(frequency))
            for file in os.listdir("..\iq\\"):
                if file.endswith(".wav"):
                    copyfile("..\iq\\" + file, "..\iq\\" + starttime  + "_F" + str(frequency)+ "\\" + file)
            for file in os.listdir("..\gnss_pos\\"):
                if file.endswith(".txt"):
                    copyfile("..\gnss_pos\\" + file, "..\iq\\" + starttime + "_F" + str(frequency) + "\\" + file)

        if platform.system() == "Linux":
            os.makedirs("../iq/" + starttime + "_F" + str(frequency))
            for file in os.listdir("../iq//"):
                if file.endswith(".wav"):
                    copyfile("../iq/" + file, "../iq/" + starttime  + "_F" + str(frequency)+ "/" + file)
            for file in os.listdir("../gnss_pos//"):
                if file.endswith(".txt"):
                    copyfile("../gnss_pos/" + file, "../iq/" + starttime  + "_F" + str(frequency)+ "/" + file)

        #  creating the .m file
        with open(dirname(dirname(abspath(__file__))) + '/proc_tdoa_' + varfile + ".m", "w") as g:
            g.write("## -*- octave -*-\n")
            g.write("\n")
            g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n")
            g.write("\n")
            for i in range(len(IQfiles)):
                # g.write("  input(" + str(i + 1) + ").fn    = 'iq/" + str(IQfiles[i]) + "';\n")  old format
                g.write("  input(" + str(i + 1) + ").fn    = fullfile('iq', '" + str(IQfiles[i]) + "');\n") # new format
            g.write("""
  input = tdoa_read_data(input);

  ## 200 Hz high-pass filter
  b = fir1(1024, 500/12000, 'high');
  n = length(input);
  for i=1:n
    input(i).z      = filter(b,1,input(i).z)(512:end);
  end

>>>>>>> Add files via upload
  tdoa  = tdoa_compute_lags(input, struct('dt',     12000,            # 1-second cross-correlation intervals
                                          'range',  0.005,            # peak search range is +-5 ms
                                          'dk',    [-2:2],            # use 5 points for peak fitting
                                          'fn', @tdoa_peak_fn_pol2fit # fit a pol2 to the peak
                                         ));
  for i=1:n
    for j=i+1:n
      tdoa(i,j).lags_filter = ones(size(tdoa(i,j).gpssec))==1;
    end
<<<<<<< HEAD
  end

  plot_info = struct('lat', [ """)
                g.write(str(lat_min_map) + ":0.05:" + str(lat_max_map) + "],\n")
                g.write("                     'lon', [ " + str(lon_min_map) + ":0.05:" + str(lon_max_map) + "],\n")
                g.write("                     'plotname', 'TDoA_")
                g.write(varfile + "',\n")
                g.write("                     'title', 'CF=" + frequency + " BW=" + str(currentbw) + " [" + str(
                    float(frequency) - (float(currentbw) / 2000)) + " <-> " + str(
                    float(frequency) + (float(currentbw) / 2000)) + "] - " + str(
                    datetime.utcnow().strftime('%d %b %Y %H%Mz')) + "'")

                if selectedlat == "" or selectedlon == "":
                    g.write(",\n                     'known_location', struct('coord', [0 0],\n")
                    g.write("                                              \'name\',  \'" "\')\n")
                    g.write("                    );\n\n\n")
                    g.write("  tdoa = tdoa_plot_map(input, tdoa, plot_info);\n")
                    g.write("\nsystem(\"cp pdf" + os.sep + "TDoA_" + str(varfile) + ".pdf iq" + os.sep + str(starttime) + "_F" + str(frequency) + os.sep + "TDoA_" + str(varfile) + "_`date -u +%d%b%Y_%H%M%Sz`.pdf\")")
                    g.write("\ndisp(\"finished\");\n")
                    g.write("endfunction\n")
                else:
                    g.write(",\n                     'known_location', struct('coord', [" + str(selectedlat) + " " + str(
                        selectedlon) + "],\n")
                    g.write("                                              \'name\',  \'" + str(
                        selectedcity.rsplit(' (')[0]).replace('_', ' ') + "\')\n")
                    g.write("""                    );\n

  tdoa = tdoa_plot_map(input, tdoa, plot_info);

system("cp pdf""" + os.sep + """TDoA_""" + str(varfile) + """.pdf iq""" + os.sep + str(starttime) + """_F""" + str(frequency) + os.sep + """TDoA_""" + str(varfile) + """_`date -u +%d%b%Y_%H%M%Sz`.pdf")
disp("finished");
endfunction """)

            g.close()
            self.writelog(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m file created")
            # backup of IQ, gnss_pos and .m file in a new directory named by the datetime process start and frequency
            time.sleep(0.5)
            os.makedirs(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(frequency))
            for file in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                copyfile(file, os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + file.rsplit(os.sep, 1)[1])
            copyfile(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m",
                     os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                         frequency) + os.sep + "proc_tdoa_" + varfile + ".m")
            with open(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + "recompute.sh", "w") as recompute:
                recompute.write("""#!/bin/sh
## This file is intended to copy back *.wav to iq directory and proc_tdoa_""" + varfile + """.m to TDoA directory
## and to open a file editor so you can modify .m file parameters.
cp ./*.wav ../
cp proc_tdoa_""" + varfile + """.m ../../
cd ../..
$EDITOR proc_tdoa_""" + varfile + """.m
octave-cli proc_tdoa_""" + varfile + """.m""")
                recompute.close()
                os.chmod(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                    frequency) + os.sep + "recompute.sh", 0o777)

=======
  end 

  plot_info = struct('lat', [ """)
            g.write(str(lat_min_map) + ":0.05:" + str(lat_max_map) + "],\n")
            g.write("                     'lon', [ " + str(lon_min_map) + ":0.05:" + str(lon_max_map) + "],\n")
            g.write("                     'plotname', 'TDoA_")
            g.write(varfile + "',\n")
            g.write("                     'title', '" + str(frequency) + " kHz " +
                    str(time.strftime('%Y%m%dT%H%MZ', time.gmtime())) + "'")

            if selectedlat == "" or selectedlon == "":
                g.write("\n                    );\n\n")
                g.write("  tdoa = tdoa_plot_map(input, tdoa, plot_info);\n")
                g.write("\ndisp(\"finished\");\n")
                g.write("endfunction\n")
            else:
                g.write(",\n                     'known_location', struct('coord', [" + str(selectedlat) + " " + str(
                    selectedlon) + "],\n")
                g.write("                                              \'name\',  \'" + str(
                    selectedcity.rsplit(' (')[0]) + "\')\n")
                g.write("""                    );\n

  tdoa = tdoa_plot_map(input, tdoa, plot_info);
  
disp("finished");
endfunction """)

        g.close()
        self.writelog("../proc_tdoa_" + varfile + ".m file created")
        #  backup the .m file in previously /iq/... created dir
        if platform.system() == "Windows":
            copyfile("..\\proc_tdoa_" + varfile + ".m",
                     "..\\iq\\" + starttime + "_F" + str(frequency) + "\\proc_tdoa_" + varfile + ".m")
        if platform.system() == "Linux":
            copyfile("../proc_tdoa_" + varfile + ".m",
                     "../iq/" + starttime + "_F" + str(frequency) + "/proc_tdoa_" + varfile + ".m")
        self.writelog("running Octave process now... please wait")
        time.sleep(1)
        OctaveProcessing(self).start()
>>>>>>> Add files via upload


class MainW(Tk, object):

<<<<<<< HEAD
    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.window = ZoomAdvanced(self)
        self.window2 = MainWindow(self)


def on_closing():
    global proc_pid, proc2_pid
    if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
        try:  # to kill octave
            os.kill(proc_pid, signal.SIGTERM)
        except:
            pass
        try:  # to kill kiwirecorder.py
            os.kill(proc2_pid, signal.SIGTERM)
        except:
            pass
        os.kill(os.getpid(), signal.SIGTERM)
        app.destroy()


if __name__ == '__main__':
    app = MainW()
    app.title(VERSION)
    app.protocol("WM_DELETE_WINDOW", on_closing)
=======
    def __init__(self, parent):
        Tk.__init__(self, parent)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.window = Zoom_Advanced(self)
        self.window2 = MainWindow(self)


if __name__ == '__main__':
    app = MainW(None)
    app.title(VERSION)
>>>>>>> Add files via upload
    app.mainloop()