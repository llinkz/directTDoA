#!/usr/bin/python
# -*- coding: utf-8 -*-
""" DirectTDoA python code. """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import codecs
import glob
import json
import os
import re
import signal
import platform
import subprocess
from subprocess import PIPE
import sys
import threading
import time
import webbrowser
import shutil
from shutil import copyfile
import socket
from collections import OrderedDict
from datetime import datetime

import requests
from PIL import Image, ImageTk
# python 2/3 compatibility
if sys.version_info[0] == 2:
    import tkFileDialog
    import tkMessageBox
    import ttk
    from Tkinter import Checkbutton, END, CURRENT, NORMAL, Message, Scale, IntVar, Listbox
    from Tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas, PhotoImage
    from tkColorChooser import askcolor
    from tkSimpleDialog import askstring, askinteger
    from tkFont import Font
else:
    import tkinter.filedialog as tkFileDialog
    import tkinter.messagebox as tkMessageBox
    from tkinter import Checkbutton, END, CURRENT, NORMAL, Message, Scale, IntVar, Listbox
    from tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas, PhotoImage, ttk
    from tkinter.colorchooser import askcolor
    from tkinter.simpledialog import askstring, askinteger
    from tkinter.font import Font

VERSION = "directTDoA v7.02"


class ReadKnownPointFile(object):
    """ Read known location list routine (see directTDoA_knownpoints.db file). """

    def __init__(self):
        pass

    @staticmethod
    def run():
        """ Read known location list routine (see directTDoA_knownpoints.db file). """
        with open('directTDoA_knownpoints.db') as h:
            global my_info1, my_info2, my_info3
            i = 3  # skip the 3x comment lines at start of the text file database
            lines = h.readlines()
            my_info1 = []
            my_info2 = []
            my_info3 = []
            while i < sum(1 for _ in open('directTDoA_knownpoints.db')):
                inforegexp = re.search(r"(.*),(.*),(.*)", lines[i])
                my_info1.append(inforegexp.group(1))
                my_info2.append(inforegexp.group(2))
                my_info3.append(inforegexp.group(3))
                i += 1


class ReadCfg(object):
    """ DirectTDoA configuration file read process. """

    def __init__(self):
        pass

    @staticmethod
    def read_cfg():
        """ DirectTDoA configuration file read process. """
        global CFG, DX0, DY0, DX1, DY1, DMAP, MAPFL, WHITELIST, BLACKLIST
        global STDCOLOR, FAVCOLOR, BLKCOLOR, POICOLOR, ICONSIZE, ICONTYPE, HIGHLIGHT
        global BGC, FGC, GRAD, THRES, CONS_B, CONS_F, STAT_B, STAT_F, MAP_BOX
        global TCPHOST, TCPPORT, TCPTRIGGER, IQDURATION, PKJ, UC, TDOAVERSION, GUI
        try:
            # Read the config file and declare variables
            with open('directTDoA.cfg', 'r') as config_file:
                CFG = json.load(config_file, object_pairs_hook=OrderedDict)
            DX0, DX1 = CFG["map"]["x0"], CFG["map"]["x1"]
            DY0, DY1 = CFG["map"]["y0"], CFG["map"]["y1"]
            DMAP, MAPFL, ICONSIZE = CFG["map"]["file"], CFG["map"]["mapfl"], CFG["map"]["iconsize"]
            STDCOLOR, FAVCOLOR, BLKCOLOR = CFG["map"]["std"], CFG["map"]["fav"], CFG["map"]["blk"]
            POICOLOR, ICONTYPE = CFG["map"]["poi"], CFG["map"]["icontype"]
            WHITELIST, BLACKLIST = CFG["nodes"]["whitelist"], CFG["nodes"]["blacklist"]
            HIGHLIGHT = CFG["map"]["hlt"]
            BGC, FGC, GRAD = CFG["guicolors"]["main_b"], CFG["guicolors"]["main_f"], CFG["guicolors"]["grad"]
            CONS_B, CONS_F = CFG["guicolors"]["cons_b"], CFG["guicolors"]["cons_f"]
            STAT_B, STAT_F = CFG["guicolors"]["stat_b"], CFG["guicolors"]["stat_f"]
            THRES, MAP_BOX = CFG["guicolors"]["thres"], CFG["map"]["mapbox"]
            TCPHOST, TCPPORT, IQDURATION = CFG["tcp"]["host"], CFG["tcp"]["port"], CFG["tcp"]["duration"]
            try:
                TCPTRIGGER = CFG["tcp"]["word"]
            except KeyError:
                SaveCfg().save_cfg("tcp", "word", "")
                TCPTRIGGER = CFG["tcp"]["word"]
            try:
                GUI = CFG["map"]["gui"]
            except KeyError:
                SaveCfg().save_cfg("map", "gui", "1200x700+150+10")
                GUI = CFG["map"]["gui"]
            PKJ, UC, TDOAVERSION = CFG["iq"]["pkj"], CFG["iq"]["uc"], CFG["iq"]["mode"]
        except (ImportError, ValueError):
            # If config file is not valid json
            tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="config file syntax error !")
            sys.exit()
        except OSError:
            # If config file is not found
            tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="config file not found !")
            sys.exit()


class SaveCfg(object):
    """ DirectTDoA configuration file save process. """

    def __init__(self):
        pass

    @staticmethod
    def save_cfg(cat, field, field_value):
        """ Save config routine. """
        # Sets the new parameter value to the right category
        CFG[cat][field] = field_value
        # Now save the config file
        with open('directTDoA.cfg', 'w') as config_file:
            json.dump(CFG, config_file, indent=2)


class CheckUpdate(threading.Thread):
    """ Check if the source is up before running the RunUpdate process. """

    def __init__(self):
        super(CheckUpdate, self).__init__()

    def run(self):
        APP.gui.writelog("Checking if http://kiwisdr.com/public is up ...")
        try:
            requests.get("http://kiwisdr.com/public", timeout=2)
            APP.gui.writelog("Ok looks good, KiwiSDR node listing update started ...")
            RunUpdate().run()
        except requests.ConnectionError:
            APP.gui.writelog("http://kiwisdr.com/public is not reachable. try again later.")
            APP.gui.start_rec_button.configure(state="normal")
            APP.gui.start_tdoa_button.configure(state="normal")
            APP.gui.update_button.configure(state="normal")
            APP.gui.purge_button.configure(state="normal")


class RunUpdate(threading.Thread):
    """ Update map process. """

    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        try:
            out = []
            tdoa_id_list = []
            # Get data from website source
            req = requests.get("http://kiwisdr.com/public/")
            # Get kiwisdr listing from kiwisdr.com/public and convert to JSON
            for html in req.text.split("<div class='cl-entry'>")[1:]:
                rx = {}
                for m in re.finditer("<!-- (id|fixes_min|tdoa_id|gps|name|snr)=(.*) -->", html):
                    rx[m.group(1)] = m.group(2)
                for n in re.finditer("<a href='(http|https)://(.*)' .+<br>", html):
                    rx['url'] = n.group(2).strip()
                if rx["fixes_min"] > "20":
                    out.append(rx)
            json_kiwisdr = json.dumps(out, ensure_ascii=False)
            json_data = json.loads(json_kiwisdr)

            # Analyse the kiwisdr.com/public JSON and create directTDoA db file
            with codecs.open('directTDoA_server_list.tmp', 'wb', encoding='utf8') as db_file:
                db_file.write("[\n")
                # line by line
                for i in range(len(json_data)):
                    # Add progress bar in the console window (* char for each node)
                    APP.gui.console_window.insert('end -1 lines', "*")
                    APP.gui.console_window.see('end')
                    time.sleep(0.005)

                    # Check if the "tdoa_id" field of the node has not been filled by the admin
                    if not json_data[i]['tdoa_id']:
                        try:
                            # Convert GPS data to maidenhead QRA locator, becomes the default tdoa_id
                            gps_data = re.search(r'([-+]?[0-9]{1,2}(\.[0-9]*)?)(,|\s) 'r'?([-+]?[0-9]{1,3}(\.[0-9]*))?',
                                                 json_data[i]['gps'][1:-1])
                            tdoa_id = self.to_grid(float(gps_data.group(1)), float(gps_data.group(4)))
                        except Exception as error:
                            print(error)
                        try:
                            # Try to get a Ham callsign from the name field, if success becomes the tdoa_id
                            hamcallfield = re.search(r"([A-Za-z]{1,2}[0-9]{1,2}[A-Za-z]{1,3})(\s|,|/|@|-)",
                                                     json_data[i]['name'])
                            tdoa_id = hamcallfield.group(1).upper()
                        except (IndexError, AttributeError):
                            pass
                    else:
                        tdoa_id = json_data[i]['tdoa_id']

                    # TDoA code is not supporting tdoa_id starting with a digit, so insert letter h at start
                    if tdoa_id[:1].isdigit():
                        tdoa_id = "h" + tdoa_id

                    # If tdoa_id already existing in the db, add a "/" + last digit from the port number
                    if tdoa_id in tdoa_id_list:
                        tdoa_id = tdoa_id + "/" + str(json_data[i]['url'][-1:])
                    tdoa_id_list.append(tdoa_id)

                    # Parse the geographical coordinates to get lat & lon values
                    try:
                        gpsfield = re.search(r'([-+]?[0-9]{1,2}(\.[0-9]*)?)(,|\s) 'r'?([-+]?[0-9]{1,3}(\.[0-9]*))?',
                                             json_data[i]['gps'][1:-1])
                        nodelat = gpsfield.group(1)
                        nodelon = gpsfield.group(4)
                    except Exception as gps_field_error:
                        # For admins not respecting GPS field format (nn.nnnnnn, nn.nnnnnn)
                        # => nodes will be shown at 0 LAT 0 LON
                        print("*** Error reading <gps> field : " + str(gps_field_error))
                        nodelat = nodelon = "0"

                    # Get the SNR score: [0] is 0-30 MHz [1] is 1.8-30 MHz - default to 15 if not available
                    try:
                        snr_search = json_data[i]['snr'].rsplit(",")[1]
                    except KeyError:
                        snr_search = "15"

                    # Build directTDoA db by writing a dict to the .tmp file
                    nodeinfo = dict(mac=json_data[i]['id'], url=json_data[i]['url'], id=tdoa_id, lat=nodelat,
                                    lon=nodelon,
                                    snr=snr_search)
                    # Order the line before writing it (necessary for rest of the code)
                    ordered_dict = ['mac', 'url', 'id', 'snr', 'lat', 'lon']
                    nodelist = [(key, nodeinfo[key]) for key in ordered_dict]
                    nodeinfo = OrderedDict(nodelist)
                    json_db = json.dumps(nodeinfo, ensure_ascii=False)
                    db_file.write(json_db + ",\n")
                db_file.seek(-2, os.SEEK_END)
                db_file.truncate()
                db_file.write("\n]")
                db_file.close()

                # Now look at db differences between before & after update process
                old_kiwi_data = json.load(open('directTDoA_server_list.db', 'r'))
                new_kiwi_data = json.load(open('directTDoA_server_list.tmp', 'r'))
                new_node = []
                for new in new_kiwi_data:
                    new_entry = dict(new)
                    new_in_old = next((old for old in old_kiwi_data if new["mac"] == old["mac"]), None)
                    if not new_in_old:
                        new_node.append(new_entry)
                old_node = []
                for old in old_kiwi_data:
                    old_entry = dict(old)
                    old_in_new = next((new for new in new_kiwi_data if old["mac"] == new["mac"]), None)
                    if not old_in_new:
                        old_node.append(old_entry)
                gain = []
                for x in range(len(new_node)):
                    gain.append(new_node[x]["id"])
                loss = []
                for y in range(len(old_node)):
                    loss.append(old_node[y]["id"])
                # If there are differences between before and after update
                if len(gain) != 0 and len(loss) != 0:
                    # python3 > display a YES/NO tkMessageBox window
                    if sys.version_info[0] == 3:
                        update_question = tkMessageBox.askquestion('Update ?', "added node(s): " + str(
                            " ".join(gain)) + "\n\nremoved node(s): " + str(" ".join(loss)) + "\n\nNew db size: " + str(
                            len(new_kiwi_data)) + "\nOld db size: " + str(len(old_kiwi_data)), icon='warning')
                        if update_question == 'yes':
                            APP.gui.writelog("The KiwiSDR listing update has been accepted.")
                            copyfile("directTDoA_server_list.tmp", "directTDoA_server_list.db")
                        else:
                            APP.gui.writelog("The KiwiSDR listing update has been aborted.")
                    # python2 > finish the process considering a YES answer but log infos
                    elif sys.version_info[0] == 2:
                        copyfile("directTDoA_server_list.tmp", "directTDoA_server_list.db")
                else:
                    APP.gui.writelog("No recent change reported between db sizes.")
                APP.gui.console_window.delete('end -1c linestart', END)
                APP.gui.console_window.insert('end', '\n')
        except Exception as update_error:
            APP.gui.writelog("UPDATE FAIL - ERROR : " + str(update_error))
        APP.gui.redraw()
        APP.gui.update_button.configure(state="normal")
        APP.gui.start_rec_button.configure(state="normal")
        APP.gui.start_tdoa_button.configure(state="normal")
        APP.gui.purge_button.configure(state="normal")
        os.remove("directTDoA_server_list.tmp")

    @staticmethod
    def to_grid(dec_lat, dec_lon):
        """ convert decimal lat/lon to maidenhead grid
        source: Walter Underwood K6WRU @ ham.stackexchange.com """

        upper = 'ABCDEFGHIJKLMNOPQRSTUVWX'
        lower = 'abcdefghijklmnopqrstuvwx'
        if not (-180 <= dec_lon < 180):
            sys.stderr.write('longitude must be -180<=lon<180, given %f\n' % dec_lon)
            sys.exit(32)
        if not (-90 <= dec_lat < 90):
            sys.stderr.write('latitude must be -90<=lat<90, given %f\n' % dec_lat)
            sys.exit(33)  # can't handle north pole, sorry, [A-R]
        adj_lat = dec_lat + 90.0
        adj_lon = dec_lon + 180.0
        grid_lat_sq = upper[int(adj_lat / 10)]
        grid_lon_sq = upper[int(adj_lon / 20)]
        grid_lat_field = str(int(adj_lat % 10))
        grid_lon_field = str(int((adj_lon / 2) % 10))
        adj_lat_remainder = (adj_lat - int(adj_lat)) * 60
        adj_lon_remainder = (adj_lon - int(adj_lon / 2) * 2) * 60
        grid_lat_subsq = lower[int(adj_lat_remainder / 2.5)]
        grid_lon_subsq = lower[int(adj_lon_remainder / 5)]
        return grid_lon_sq + grid_lat_sq + grid_lon_field + grid_lat_field + grid_lon_subsq + grid_lat_subsq


class StartRecording(threading.Thread):
    """ Recording IQ process. """

    def __init__(self, parent=None):
        super(StartRecording, self).__init__()
        self.parent = parent

    def run(self):
        global PROC2_PID
        CheckFileSize().start()
        which_list = fulllist
        which_action = "IQ Recordings in progress..."
        if (ultimate.get()) == 1:
            which_action = "ultimateTDoA IQ Recordings in progress..."
        if platform.system() == "Windows":
            client_type = VERSION + ' [win/record]'
        elif platform.system() == "Darwin":
            client_type = VERSION + ' [macOS/record]'
        else:
            client_type = VERSION + ' [linux/record]'
        proc2 = subprocess.Popen([sys.executable, 'kiwiclient' + os.sep + 'kiwirecorder.py', '-s',
                                  ','.join(str(p).rsplit('$')[0] for p in which_list), '-p',
                                  ','.join(str(p).rsplit('$')[1] for p in which_list),
                                  '--station=' + ','.join(str(p).rsplit('$')[3] for p in which_list), '-f',
                                  str(FREQUENCY), '-L', str(lpcut), '-H', str(hpcut), '-m', 'iq', '--tlimit', '120',
                                  '-u', client_type.replace(' ', '_'), '-w', '-d', os.path.join('TDoA', 'iq')],
                                 stdout=PIPE, shell=False)
        self.parent.writelog(which_action)
        PROC2_PID = proc2.pid


class CheckFileSize(threading.Thread):
    """ The process monitoring all iq/*.wav files size. """

    def __init__(self):
        super(CheckFileSize, self).__init__()

    def run(self):
        APP.gui.purge_button.configure(state="disabled")
        APP.gui.update_button.configure(state="disabled")
        wav_container = []
        rec_time = -1
        while True:
            for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                if wavfiles not in wav_container:
                    wav_container.append(wavfiles)
                try:
                    APP.gui.status_window.insert('end -1 lines',
                                                 wavfiles.rsplit(os.sep, 1)[1].rsplit("_", 3)[2] + "|" + str(
                                                     os.path.getsize(wavfiles) // 1024) + "KB   ")
                except OSError:
                    APP.gui.status_window.insert('end -1 lines', "\n")
            APP.gui.status_window.insert("end", "\n[" + str(len(wav_container)) + '/' + str(len(fulllist)) + "] ~" + str(rec_time) + "s")
            APP.gui.status_window.see('end')
            time.sleep(0.5)
            rec_time += 0.5
            APP.gui.status_window.delete("0.0", END)
            if rec_in_progress == 0:
                APP.gui.purge_button.configure(state="normal")
                APP.gui.update_button.configure(state="normal")
                break


class PlotIQ(threading.Thread):
    """ plot_iq.py processing routine """

    def __init__(self):
        super(PlotIQ, self).__init__()

    def run(self):
        run_dir = os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(FREQUENCY) + os.sep
        with open(os.devnull, 'w') as fp:
            subprocess.call([sys.executable, 'plot_iq.py'], cwd=os.path.join(run_dir), shell=False, stdout=fp)


class ComputeUltimate(threading.Thread):
    """ compute_ultimate.py processing routine """

    def __init__(self):
        super(ComputeUltimate, self).__init__()

    def run(self):
        run_dir = os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(FREQUENCY)
        with open(os.devnull, 'w') as fp:
            subprocess.call([sys.executable, 'compute_ultimate.py'], cwd=os.path.join(run_dir), shell=False, stdout=fp)


class OctaveProcessing(threading.Thread):
    """ Octave processing routine """

    def __init__(self):
        super(OctaveProcessing, self).__init__()

    def run(self):
        global tdoa_position, PROC_PID  # stdout
        octave_errors = [b'index-out-of-bounds', b'< 2 good stations found', b'Octave:nonconformant - args',
                         b'n_stn=2 is not supported', b'resample.m: p and q must be positive integers',
                         b'Octave:invalid-index', b'incomplete \'data\' chunk',
                         b'reshape: can\'t reshape 0x0 array to 242x258 array', b'malformed filename:']
        tdoa_filename = "proc_tdoa_" + KHZ_FREQ + ".m"
        proc = subprocess.Popen(['octave-cli', tdoa_filename], cwd=os.path.join('TDoA'), stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, shell=False)
        PROC_PID = proc.pid
        logfile = open(os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(
            FREQUENCY) + os.sep + "TDoA_" + KHZ_FREQ + "_log.txt", 'w')
        if sys.version_info[0] == 2:
            for octave_output in proc.stdout:
                logfile.write(octave_output)
                if "most likely position:" in octave_output:
                    tdoa_position = octave_output
                if "exluding" in octave_output:
                    APP.gui.status_window.insert('end -1 lines', octave_output)
                    APP.gui.status_window.see('end')
                if any(x in octave_output for x in octave_errors):
                    ProcessFailed(octave_output).start()
                    proc.terminate()
                if "finished" in octave_output:
                    logfile.close()
                    ProcessFinished().start()
                    proc.terminate()
        else:
            octave_output = proc.communicate()[0]
            logfile.write(str(octave_output, 'utf-8'))
            if b"most likely position:" in octave_output:
                tdoa_position = octave_output
            if b"exluding" in octave_output:
                APP.gui.status_window.insert('end -1 lines', octave_output)
                APP.gui.status_window.see('end')
            if any(x in octave_output for x in octave_errors):
                ProcessFailed(octave_output).start()
                proc.terminate()
            if b"finished" in octave_output:
                logfile.close()
                ProcessFinished().start()
                proc.terminate()
        proc.wait()


class ProcessFailed(threading.Thread):
    """ The actions to perform when a TDoA run has failed. """

    def __init__(self, returned_error):
        super(ProcessFailed, self).__init__()
        self.Returned_error = returned_error

    def run(self):
        global tdoa_in_progress  # TDoA process status
        r_dir = os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(FREQUENCY) + os.sep
        if platform.system() == "Windows":
            webbrowser.open(r_dir)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", r_dir])
        else:
            subprocess.Popen(["xdg-open", r_dir])
        APP.gui.start_rec_button.configure(state="normal", text="Start recording")
        APP.gui.start_tdoa_button.configure(state="disabled")
        APP.gui.update_button.configure(state="normal")
        APP.gui.purge_button.configure(state="normal")
        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            os.remove(wavfiles)
        tdoa_in_progress = 0
        APP.gui.status_window.insert('end -1 lines', self.Returned_error)
        APP.gui.status_window.insert('end -1 lines', "Octave Process Failed. Retry")
        APP.gui.status_window.see('end')
        # subprocess.call(["xdg-open", 'TDoA_' + str(FREQUENCY) + '_log.txt'])


class ProcessFinished(threading.Thread):
    """ The actions to perform when a TDoA run has finished. """

    def __init__(self):
        super(ProcessFinished, self).__init__()

    def run(self):
        global tdoa_in_progress  # TDoA process status
        r_dir = os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(FREQUENCY) + os.sep
        if auto_run_tdoa.get() == 0:
            if platform.system() == "Windows":
                webbrowser.open(r_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", r_dir])
            else:
                subprocess.Popen(["xdg-open", r_dir])
        APP.gui.start_rec_button.configure(state="normal", text="Start recording")
        APP.gui.start_tdoa_button.configure(state="disabled")
        APP.gui.update_button.configure(state="normal")
        APP.gui.purge_button.configure(state="normal")
        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            os.remove(wavfiles)
        # for pdffiles in glob.glob(os.path.join('TDoA', 'pdf') + os.sep + "*.pdf"):
        #     os.remove(pdffiles)
        for mfiles in glob.glob(os.path.join('TDoA') + os.sep + "proc*.m"):
            if mfiles != "TDoA/proc_tdoa_kiwi.m":
                os.remove(mfiles)
        tdoa_in_progress = 0
        with open(r_dir + "proc_tdoa_" + KHZ_FREQ + ".m", 'r') as read_file:
            content = read_file.readlines()
        with open(r_dir + "proc_tdoa_" + KHZ_FREQ + ".m", 'w') as write_file:
            for line in content:
                write_file.write(line.replace("initial", "recomputed"))
        APP.gui.writelog("TDoA process finished successfully.")


class CheckSnr(threading.Thread):
    """ SNR check process. """

    def __init__(self, serverport):
        threading.Thread.__init__(self)
        self.s_host = serverport.rsplit(":")[0]
        self.s_port = serverport.rsplit(":")[1]

    def run(self):
        """ SNR check process. """
        try:
            socket2_connect = subprocess.Popen(
                [sys.executable, 'kiwiclient' + os.sep + 'microkiwi_waterfall.py', '-s', self.s_host, '-p',
                 self.s_port], stdout=PIPE, shell=False)
            APP.gui.writelog("Retrieving " + self.s_host + " waterfall, please wait")
            while True:
                snr_output = socket2_connect.stdout.readline()
                # if b"received sample" in snr_output:
                #     APP.gui.console_window.insert('end -1c', '.')
                if b"SNR" in snr_output:
                    APP.gui.console_window.delete('end -1c linestart', END)
                    APP.gui.console_window.insert('end', '\n')
                    APP.gui.writelog(snr_output.decode().replace("\n", ""))
                    break
        except ValueError:
            print ("Error: unable to retrieve datas from this node")


class StartDemodulation(threading.Thread):
    """ Demodulation process. """

    def __init__(self, server, port, frequency, modulation):
        threading.Thread.__init__(self)
        self.s_host = server
        self.s_port = port
        self.s_freq = frequency
        self.s_mod = modulation

    def run(self):
        global LISTENMODE, kiwisdrclient_pid
        if self.s_mod == "USB":
            low_cut = "0"
            hi_cut = "3600"
        elif self.s_mod == "LSB":
            low_cut = "-3600"
            hi_cut = "0"
        elif self.s_mod == "CW":
            low_cut = "-500"
            hi_cut = "500"
            self.s_freq = str(float(self.s_freq) - 0.5)
        elif self.s_mod == "AM":
            low_cut = "-5000"
            hi_cut = "5000"
        else:
            self.s_mod = "USB"
            low_cut = "300"
            hi_cut = "3300"
        try:
            if platform.system() == "Windows":
                client_type = VERSION + ' [win/listen]'
            elif platform.system() == "Darwin":
                client_type = VERSION + ' [macOS/listen]'
            else:
                client_type = VERSION + ' [linux/listen]'
            proc8 = subprocess.Popen(
                [sys.executable, 'kiwiclient' + os.sep + 'kiwirecorder.py', '-s', self.s_host, '-p', self.s_port, '-f',
                 self.s_freq, '-m', self.s_mod, '-L', low_cut, '-H', hi_cut, '-u', client_type.replace(' ', '_'), '-q',
                 '-a'], stdout=PIPE, shell=False)
            kiwisdrclient_pid = proc8.pid
            LISTENMODE = "1"
            APP.gui.writelog(
                "Starting Listen mode   [ " + self.s_host + " / " + self.s_freq + " kHz / " + self.s_mod.upper() + " ] - to stop: use same command from any node popup menu.")
        except Exception as demodulation_Error:
            print ("Unable to demodulate this node - Error: " + str(demodulation_Error))
            LISTENMODE = "0"


class FillMapWithNodes(object):
    """ process to display the nodes on the World Map. """

    def __init__(self, parent):
        self.parent = parent

    def run(self):
        """ DirectTDoA process to display the nodes on the World Map. """
        global NODE_COUNT, NODE_COUNT_FILTER, tag_list
        tag_list = []
        NODE_COUNT = 0
        NODE_COUNT_FILTER = 0
        server_lists = ["directTDoA_server_list.db", "directTDoA_static_server_list.db"]
        for server_list in server_lists:
            with open(server_list) as node_db:
                db_data = json.load(node_db)
                for node_index in range(len(db_data)):
                    NODE_COUNT += 1
                    # Change icon color of fav, black and standards nodes and apply a gradient // SNR
                    perc = (int(db_data[node_index]["snr"]) - 40) * GRAD
                    if db_data[node_index]["mac"] in WHITELIST:
                        node_color = (self.color_variant(FAVCOLOR, perc))
                    elif db_data[node_index]["mac"] in BLACKLIST:
                        node_color = (self.color_variant(BLKCOLOR, perc))
                    else:
                        node_color = (self.color_variant(STDCOLOR, perc))
                    # Apply the map filtering
                    if MAPFL == 1 and db_data[node_index]["mac"] not in BLACKLIST:
                        NODE_COUNT_FILTER += 1
                        self.add_point(node_index, node_color, db_data)
                    elif MAPFL == 2 and db_data[node_index]["mac"] in WHITELIST:
                        NODE_COUNT_FILTER += 1
                        self.add_point(node_index, node_color, db_data)
                    elif MAPFL == 3 and db_data[node_index]["mac"] in BLACKLIST:
                        NODE_COUNT_FILTER += 1
                        self.add_point(node_index, node_color, db_data)
                    elif MAPFL == 0:
                        NODE_COUNT_FILTER += 1
                        self.add_point(node_index, node_color, db_data)
        if 'APP' in globals():
            APP.gui.label04.configure(text="█ Visible: " + str(NODE_COUNT_FILTER) + "/" + str(NODE_COUNT))
        self.parent.show_image()

    @staticmethod
    def convert_lat(lat):
        """ Convert the real node latitude coordinates to adapt to GUI window map geometry. """
        # nodes are between LATITUDE 0 and 90N
        if float(lat) > 0:
            return 990 - (float(lat) * 11)
        # nodes are between LATITUDE 0 and 60S
        return 990 + (float(0 - float(lat)) * 11)

    @staticmethod
    def convert_lon(lon):
        """ Convert the real node longitude coordinates to adapt to GUI window map geometry. """
        return 1910 + ((float(lon) * 1910) / 180)

    @staticmethod
    def color_variant(hex_color, brightness_offset=1):
        """ Process that changes the brightness (only) of a specific RGB color.
        chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html """
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join(["0" + hex(i)[2:] if len(hex(i)[2:]) < 2 else hex(i)[2:] for i in new_rgb_int])

    def add_point(self, node_index_data, node_color, node_db_data):
        """ Process that add node icons over the World map. """
        global tag_list
        mykeys = ['mac', 'url', 'id', 'snr', 'lat', 'lon']
        node_lat = self.convert_lat(node_db_data[node_index_data]["lat"])
        node_lon = self.convert_lon(node_db_data[node_index_data]["lon"])
        if not any(node_db_data[node_index_data]["mac"] in s for s in tag_list):
            node_tag = str('$'.join([node_db_data[node_index_data][x] for x in mykeys]))
            ic_size = int(ICONSIZE)
            try:
                if ICONTYPE == 0:
                    self.parent.canvas.create_oval(node_lon - ic_size, node_lat - ic_size, node_lon + ic_size,
                                                   node_lat + ic_size, fill=node_color, tag=node_tag)
                else:
                    self.parent.canvas.create_rectangle(node_lon - ic_size, node_lat - ic_size, node_lon + ic_size,
                                                        node_lat + ic_size, fill=node_color, tag=node_tag)
                self.parent.canvas.tag_bind(node_tag, "<Button-1>", self.parent.onclickleft)
                tag_list.append(node_tag)
            except NameError:
                print ("OOPS - Error in adding the point to the map")

    def delete_point(self, map_definition):
        """ Map presets deletion process. """
        self.parent.canvas.delete(map_definition)

    def redraw_map(self):
        """ Redraw all icons on the World Map. """
        for node_tag_item in tag_list:
            self.parent.canvas.delete(node_tag_item)
        ReadCfg().read_cfg()
        FillMapWithNodes.run(self)

    def node_sel_active(self, node_mac):
        """ Adding additionnal highlight on node icon. """
        for node_tag_item in tag_list:
            if node_mac in node_tag_item:
                tmp_latlon = node_tag_item.rsplit("$", 6)
                tmp_lat = self.convert_lat(tmp_latlon[4])
                tmp_lon = self.convert_lon(tmp_latlon[5])
                is_delta = int(ICONSIZE) + 1
                if ICONTYPE == 0:
                    self.parent.canvas.create_oval(tmp_lon - is_delta, tmp_lat - is_delta, tmp_lon + is_delta,
                                                   tmp_lat + is_delta, fill='', outline=HIGHLIGHT,
                                                   tag=node_tag_item + "$#")
                else:
                    self.parent.canvas.create_rectangle(tmp_lon - is_delta, tmp_lat - is_delta, tmp_lon + is_delta,
                                                        tmp_lat + is_delta, fill='', outline=HIGHLIGHT,
                                                        tag=node_tag_item + "$#")
                self.parent.canvas.tag_bind(node_tag_item + "$#", "<Button-1>", self.parent.onclickleft)

    def node_selection_inactive(self, node_mac):
        """ Removing additionnal highlight on selected node icon. """
        for node_tag_item in tag_list:
            if node_mac in node_tag_item:
                self.parent.canvas.tag_unbind(node_tag_item + "$#", "<Button-1>")
                self.parent.canvas.delete(node_tag_item + "$#")

    def node_selection_inactiveall(self):
        """ Removing ALL additionnal highlights on selected nodes icons. """
        for node_tag_item in tag_list:
            self.parent.canvas.tag_unbind(node_tag_item + "$#", "<Button-1>")
            self.parent.canvas.delete(node_tag_item + "$#")

    def after_update(self):
        ReadCfg().read_cfg()
        FillMapWithNodes.run(self)


class TcpClient(threading.Thread):
    def __init__(self, trigger):
        threading.Thread.__init__(self)
        self.trigger = trigger

    def run(self):
        global TCPHOST, TCPPORT, IQDURATION

        try:
            s = socket.socket()
            s.settimeout(1.0)
            s.connect((TCPHOST, TCPPORT))
            s.setblocking(False)
            APP.gui.writelog("TCP client connected to " + TCPHOST + ":" + str(TCPPORT) + " | trigger word : " + str(
                TCPTRIGGER) + " | duration : " + str(IQDURATION) + "s")
            if self.trigger == "":
                APP.gui.writelog(
                    "Warning, with blank trigger word the recording will start on any event appearing on TCP server side and the recordings will follow each other in a loop if TCP data flow is continuous")
        except (socket.error, socket.gaierror, socket.timeout) as e:
            APP.gui.writelog("TCP client connection to " + TCPHOST + ":" + str(TCPPORT) + " failed - " + str(e))
            tcpclient.set(0)
            return

        data = b""
        while True:
            if not tcpclient.get():
                APP.gui.writelog("TCP client disconnected from " + TCPHOST + ":" + str(TCPPORT))
                break

            try:
                data += s.recv(2048)
            except:
                pass

            if not rec_in_progress and data and (not self.trigger or re.search(self.trigger, data.decode('utf-8'))):
                start_time = time.time()
                APP.gui.writelog("### TCP data received ###")
                APP.gui.start_stop_rec()

            if rec_in_progress and time.time() - start_time >= IQDURATION:
                try:
                    if "[NORMAL MODE]" in data.decode('utf-8'):
                        PrintALE(data, reset=0).start()
                except UnicodeDecodeError:
                    PrintALE(data, reset=1).start()
                data = b""
                APP.gui.start_stop_rec()
                if auto_run_tdoa.get() == 1:
                    APP.gui.start_stop_tdoa()

            time.sleep(0.001)


class PrintALE(threading.Thread):
    """ 2G ALE WORDS management. """

    def __init__(self, data, reset):
        threading.Thread.__init__(self)
        self.ale_data = data
        self.reset = reset

    def run(self):
        """ Get 2G ALE words or reset the buffer in case of other decoded digimodes. """
        global ale_file_name, ale_file_data
        if self.reset == 1:
            ale_file_data = ""
        else:
            to_addr = tis_addr = tws_addr = ""
            ale_file_name = "ALE [partial decode].txt"
            ale_file_data = self.ale_data
            for addr in re.findall(r'\[TO\]\[(.*?)\]', self.ale_data.decode('utf-8')):
                if len(addr) > len(to_addr):
                    to_addr = addr
            for addr in re.findall(r'\[TIS\]\[(.*?)\]', self.ale_data.decode('utf-8')):
                if len(addr) > len(tis_addr):
                    tis_addr = addr
            for addr in re.findall(r'\[TWS\]\[(.*?)\]', self.ale_data.decode('utf-8')):
                if len(addr) > len(tws_addr):
                    tws_addr = addr
            if to_addr and tis_addr and not tws_addr:
                APP.gui.writelog(" ### ALE CALL ### [TO]" + to_addr + " [TIS]" + tis_addr)
                ale_file_name = "ALE CALL [TO]" + to_addr + " [TIS]" + tis_addr + ".txt"
                return
            if to_addr and tws_addr and not tis_addr:
                APP.gui.writelog(" ### ALE CLOSING ### [TO]" + to_addr + " [TWS]" + tws_addr)
                ale_file_name = "ALE CLOSE [TO]" + to_addr + " [TWS]" + tws_addr + ".txt"
                return
            if tws_addr and not to_addr and not tis_addr:
                APP.gui.writelog(" ### ALE SOUNDING ### [TWS]" + tws_addr)
                ale_file_name = "ALE SOUNDING [TWS]" + tws_addr + ".txt"


class GuiCanvas(Frame):
    """ Process that creates the GUI map canvas, enabling move & zoom on a picture.
    source: stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 """

    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        # tip: GuiCanvas is member1

        img = PhotoImage(file='icon.gif')
        parent.after(50, parent.call('wm', 'iconphoto', parent, img))
        global fulllist, LISTENMODE, mapboundaries_set
        fulllist = []
        LISTENMODE = "0"
        mapboundaries_set = None
        ReadCfg().read_cfg()
        parent.geometry(GUI)
        self.x = self.y = 0
        # Create canvas and put image on it
        self.canvas = Canvas(self.master, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)  # map move
        self.canvas.bind('<B1-Motion>', self.move_to)  # map move
        # self.canvas.bind_all('<MouseWheel>', self.wheel)  # Windows Zoom
        # self.canvas.bind('<Button-5>', self.wheel)  # Linux Zoom
        # self.canvas.bind('<Button-4>', self.wheel)  # Linux Zoom
        self.canvas.bind("<ButtonPress-3>", self.on_button_press)  # red rectangle selection
        self.canvas.bind("<B3-Motion>", self.on_move_press)  # red rectangle selection
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release)  # red rectangle selection
        self.image = Image.open(DMAP)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the image
        self.delta = 2.0  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.canvas.scan_dragto(-int(DX0.split('.')[0]), -int(DY0.split('.')[0]), gain=1)
        self.show_image()
        time.sleep(0.2)
        FillMapWithNodes(self).run()

    def on_button_press(self, event):
        """ Red rectangle selection drawing on the World map. """
        global map_preset  # map_manual
        if image_scale == 1:
            if map_preset == 1:
                self.delete_point("mappreset")
                self.rect = None
                map_preset = 0
            self.start_x = self.canvas.canvasx(event.x)
            self.start_y = self.canvas.canvasy(event.y)
            # create rectangle if not yet exist
            if not self.rect:
                self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red', tag="mapmanual")
        else:
            APP.gui.writelog("ERROR : The boundaries selection is forbidden unless map un-zoomed.")

    def on_move_press(self, event):
        """ Get the Map boundaries red rectangle selection coordinates. """
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        if image_scale == 1:
            if map_preset == 1:
                pass
            else:
                cur_x = self.canvas.canvasx(event.x)
                cur_y = self.canvas.canvasy(event.y)
                lonmin = round(((self.start_x - 1910) * 180) / 1910, 1)
                lonmax = round(((cur_x - 1910) * 180) / 1910, 1)
                latmax = round(0 - ((cur_y - 990) / 11), 1)
                latmin = round((self.start_y - 990) / 11, 1)

                if cur_x > self.start_x and cur_y > self.start_y:
                    lat_max_map = 0 - latmin
                    lat_min_map = latmax
                    lon_max_map = lonmax
                    lon_min_map = lonmin

                if cur_x < self.start_x and cur_y > self.start_y:
                    lat_max_map = 0 - latmin
                    lat_min_map = latmax
                    lon_max_map = lonmin
                    lon_min_map = lonmax

                if cur_x > self.start_x and cur_y < self.start_y:
                    lat_max_map = latmax
                    lat_min_map = 0 - latmin
                    lon_max_map = lonmax
                    lon_min_map = lonmin

                if cur_x < self.start_x and cur_y < self.start_y:
                    lat_max_map = latmax
                    lat_min_map = 0 - latmin
                    lon_max_map = lonmin
                    lon_min_map = lonmax

                w_canva, h_canva = self.canvas.winfo_width(), self.canvas.winfo_height()
                if event.x > 0.98 * w_canva:
                    self.canvas.xview_scroll(1, 'units')
                elif event.x < 0.02 * w_canva:
                    self.canvas.xview_scroll(-1, 'units')
                if event.y > 0.98 * h_canva:
                    self.canvas.yview_scroll(1, 'units')
                elif event.y < 0.02 * h_canva:
                    self.canvas.yview_scroll(-1, 'units')
                self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
                self.show_image()
        else:
            pass

    def on_button_release(self, event):
        """ When Mouse right button is released (map boundaries set or ultimateTDoA set). """
        global mapboundaries_set, map_preset  # lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global map_manual, fulllist, LISTENMODE
        if LISTENMODE == "1":
            return
        if (ultimate.get()) == 1:  # ultimateTDoA mode
            APP.gui.purgenode()
            mapboundaries_set = 1
            map_manual = 1
            server_lists = ["directTDoA_server_list.db", "directTDoA_static_server_list.db"]
            for server_list in server_lists:
                with open(server_list) as node_db2:
                    db_data2 = json.load(node_db2)
                    nodecount2 = len(db_data2)
                    for y in range(nodecount2):
                        FillMapWithNodes(self).node_selection_inactive(node_mac=db_data2[y]["mac"])
                        if (lat_min_map < float(db_data2[y]["lat"]) < lat_max_map) and (
                                lon_min_map < float(db_data2[y]["lon"]) < lon_max_map):
                            if ultimatefav.get() == 1 and db_data2[y]["mac"] in WHITELIST:
                                fulllist.append(
                                    db_data2[y]["url"].rsplit(':')[0] + "$" + db_data2[y]["url"].rsplit(':')[1] + "$" +
                                    db_data2[y]["mac"] + "$" + db_data2[y]["id"].replace("/", ""))
                                FillMapWithNodes(self).node_sel_active(node_mac=db_data2[y]["mac"])
                            else:
                                if ultimatefav.get() == 0 and db_data2[y]["mac"] not in BLACKLIST:
                                    fulllist.append(
                                        db_data2[y]["url"].rsplit(':')[0] + "$" + db_data2[y]["url"].rsplit(':')[
                                            1] + "$" + db_data2[y]["mac"] + "$" + db_data2[y]["id"].replace("/", ""))
                                    FillMapWithNodes(self).node_sel_active(node_mac=db_data2[y]["mac"])
            if fulllist:
                APP.gui.writelog(str(len(fulllist)) + " KiwiSDR(s) found within this area.")
                APP.title(VERSION + " - ultimateTDoA nodes [" + str(len(fulllist)) + "] : " + '/'.join(
                    str(p).rsplit('$')[3] for p in fulllist))
            else:
                APP.gui.writelog("No KiwiSDR found within this area.")
                APP.title(VERSION)
                fulllist = []

        else:
            if map_preset == 1 and map_manual == 0:
                pass
            else:
                mapboundaries_set = 1
                map_manual = 1
        if len(fulllist) >= 3 and APP.gui.freq_input.get() != "" and 5 < float(
                APP.gui.freq_input.get()) < 30000:
            APP.gui.tcpclient_checkbox.configure(state="normal")
            if (ultimate.get()) == 0:
                APP.gui.autorun_checkbox.configure(state="normal")
        else:
            APP.gui.tcpclient_checkbox.configure(state="disabled")

    def create_known_point(self, y_kwn, x_kwn, n):
        """ Map known place creation process, works only when self.imscale = 1.0 """
        #  city coordinates y & x (degrees) converted to pixels
        ic_size = int(ICONSIZE)
        xx0 = (1910 + ((float(x_kwn) * 1910) / 180)) - ic_size
        xx1 = (1910 + ((float(x_kwn) * 1910) / 180)) + ic_size
        if float(y_kwn) > 0:  # point is located in North Hemisphere
            yy0 = (990 - (float(y_kwn) * 11)) - ic_size
            yy1 = (990 - (float(y_kwn) * 11)) + ic_size
        else:  # point is located in South Hemisphere
            yy0 = (990 + (float(0 - float(y_kwn)) * 11)) - ic_size
            yy1 = (990 + (float(0 - float(y_kwn)) * 11)) + ic_size
        self.canvas.create_rectangle(xx0, yy0, xx1, yy1, fill=POICOLOR, outline="black", activefill=POICOLOR,
                                     tag="#POI")
        self.canvas.create_text(xx0, yy0 - 10, text=selectedcity.rsplit(' (')[0].replace("_", " "), justify='center',
                                fill=POICOLOR, tag="#POI")

    def unselect_allpoint(self):
        """ Calling process that remove additionnal highlight on all selected nodes. """
        FillMapWithNodes(self).node_selection_inactiveall()

    def redraw_map_cmd(self):
        """ Calling process that redraw all icons on the World map. """
        FillMapWithNodes(self).redraw_map()

    def delete_point(self, n):
        """ KnownPoint deletion process. """
        FillMapWithNodes(self).delete_point(n.rsplit(' (')[0])

    def onclickleft(self, event):
        """ Left Mouse Click bind on the World map. """
        global HOST
        menu0 = Menu(self, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')  # node overlap list menu
        menu1 = Menu(self, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')  # main node menu
        menu2 = Menu(menu1, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')  # enforce menu
        # search for overlapping nodes
        overlap_range = ICONSIZE * 4
        overlap_rect = (self.canvas.canvasx(event.x) - overlap_range), (self.canvas.canvasy(event.y) - overlap_range), (
                    self.canvas.canvasx(event.x) + overlap_range), (self.canvas.canvasy(event.y) + overlap_range)
        node_overlap_match = self.canvas.find_enclosed(*overlap_rect)
        overlap_list = []
        for item_o in list(node_overlap_match):
            if "$#" not in self.canvas.gettags(self.canvas.find_withtag(item_o))[0]:
                overlap_list.append(item_o)
        if len(node_overlap_match) > 1 and len(overlap_list) != 1:  # node icon overlap found, displays menu0
            for el1, el2 in enumerate(node_overlap_match):
                if "$#" not in str(self.canvas.gettags(el2)):  # dont display node highlight tags
                    HOST = self.canvas.gettags(self.canvas.find_withtag(el2))[0]
                    # mykeys = ['mac', 'url', 'id', 'snr', 'lat', 'lon']
                    # n_field    0      1      2     3      4     5
                    n_field = HOST.rsplit("$", 6)
                    # Color gradient proportionnal to SNR value
                    snr_gradient = (int(n_field[3]) - 40) * GRAD
                    # rbg = self.color_variant("#FF0000", snr_gradient)
                    # Dynamic foreground (adapting font to white or black depending on luminosity)
                    dfg = self.get_font_color((self.color_variant("#FFFF00", snr_gradient)))
                    nodec = BLKCOLOR if n_field[0] in BLACKLIST else FAVCOLOR if n_field[0] in WHITELIST else STDCOLOR
                    cbg = self.color_variant(nodec, snr_gradient)
                    # check if node is already in the TDoA node listing
                    if len([el for el in fulllist if n_field[0] in el]) != 1:
                        name = n_field[2]
                    else:
                        name = "✔ " + n_field[2]
                    menu0.add_command(label=name, background=cbg, foreground=dfg,
                                      command=lambda x=HOST: self.create_node_menu(x, event.x_root, event.y_root, menu1,
                                                                                   menu2))
                else:
                    pass
            menu0.tk_popup(event.x_root, event.y_root)
        else:
            HOST = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
            self.create_node_menu(HOST, event.x_root, event.y_root, menu1, menu2)

    def create_node_menu(self, kiwinodetag, popx, popy, menu, menu2):
        n_field = kiwinodetag.rsplit("$", 6)
        matches = [el for el in fulllist if n_field[0] in el]
        snr_gradient = (int(n_field[3]) - 40) * GRAD
        nodec = BLKCOLOR if n_field[0] in BLACKLIST else FAVCOLOR if n_field[0] in WHITELIST else STDCOLOR
        # Red background
        rbg = self.color_variant("#FF0000", snr_gradient)
        # Dynamic foreground (adapting font to white or black depending on luminosity)
        dfg = self.get_font_color(self.color_variant("#FFFF00", snr_gradient))
        # Colorized background (depending on Standard/Favorite/Blacklist)
        cbg = self.color_variant(nodec, snr_gradient)
        try:  # check if the node is answering
            chktimeout = 2  # timeout of the node check
            checkthenode = requests.get("http://" + n_field[1] + "/status", timeout=chktimeout)
            i_node = {}
            try:
                for line in checkthenode.text.splitlines():
                    i_node[line.rsplit("=", 1)[0]] = line.rsplit("=", 1)[1]
                permit_web = False
                gps_ready = False
                n_stat = " [" + i_node['users'] + "/" + i_node['users_max'] + " users]"
                g_stat = " [GNSS: " + i_node['fixes_min'] + " fixes/min] [GPS: " + i_node['gps_good'] + "/12]"
                s_stat = " [SNR: " + n_field[3] + " dB]"
                # If no socket slots are available on this node :
                if i_node['users'] == i_node['users_max']:
                    menu.add_command(label=n_field[2] + " is full" + g_stat + n_stat + s_stat, background=rbg,
                                     foreground=dfg, command=None)
                # If node is offline :
                elif i_node['offline'] == "yes":
                    menu.add_command(label=n_field[2] + " is offline", background=rbg, foreground=dfg, command=None)
                # If node had no GPS fix in the last minute :
                elif i_node['fixes_min'] == "0":
                    if len(matches) != 1:
                        menu.add_cascade(label=n_field[2] + " is not useful for TDoA" + g_stat + n_stat + s_stat,
                                         background=rbg, foreground=dfg, menu=menu2)
                        menu2.add_command(label="add anyway", background=cbg, foreground=dfg,
                                          command=lambda *args: self.populate("add", "no", n_field))
                    else:
                        menu.add_command(label=n_field[2] + " is not useful for TDoA" + g_stat + n_stat + s_stat,
                                         background=rbg, foreground=dfg, command=None)
                    permit_web = True
                else:  # All is ok for this node and then, permit extra commands
                    permit_web = True
                    gps_ready = True
                # matches = [el for el in fulllist if n_field[0] in el]
                # if node is NOT already listed in the TDoA node group, allow the ADD command
                if len(matches) != 1 and int(i_node['fixes_min']) > 0 and gps_ready:
                    menu.add_command(label="Add " + n_field[2] + " for TDoA process" + g_stat + n_stat + s_stat,
                                     background=cbg, foreground=dfg, font="TkFixedFont 7 bold",
                                     command=lambda *args: self.populate("add", "no", n_field))
                # if node IS already in the TDoA node group, allow the REMOVE command
                elif len(matches) == 1:
                    menu.add_command(label="Remove " + n_field[2] + " from TDoA process" + g_stat + n_stat + s_stat,
                                     background=cbg, foreground=dfg, font="TkFixedFont 7 bold",
                                     command=lambda: self.populate("del", "no", n_field))
            except IndexError as wrong_status:
                menu.add_command(label=n_field[2] + " is not available. (proxy.kiwisdr.com error)", background=rbg,
                                 foreground=dfg, command=None)
                permit_web = False
        except requests.exceptions.ConnectionError as req_conn_error:
            menu.add_command(label=n_field[2] + " node is not available. " + str(req_conn_error).split('\'')[1::2][1],
                             background=rbg, foreground=dfg, command=None)
            if len(matches) == 1:
                menu.add_command(label="Remove " + n_field[2] + " from TDoA process", background=cbg, foreground=dfg,
                                 font="TkFixedFont 7 bold", command=lambda: self.populate("del", "no", n_field))
            permit_web = False
        except requests.exceptions.RequestException as req_various_error:
            menu.add_command(label=n_field[2] + " node is not available. " + str(req_various_error), background=rbg,
                             foreground=dfg, command=None)
            if len(matches) == 1:
                menu.add_command(label="Remove " + n_field[2] + " from TDoA process", background=cbg, foreground=dfg,
                                 font="TkFixedFont 7 bold", command=lambda: self.populate("del", "no", n_field))
            permit_web = False

        # Always try to print out KiwiSDR's full name line
        try:
            menu.add_command(label=i_node['name'], state=NORMAL, background=cbg, foreground=dfg, command=None)
        except (UnboundLocalError, IndexError):
            pass

        # EXTRA commands and lines
        if permit_web and APP.gui.freq_input.get() != "" and 5 < float(APP.gui.freq_input.get()) < 30000:
            # Add Open in Web browser lines
            menu.add_separator()
            menu.add_command(label="Open " + n_field[2] + " in Web browser", state=NORMAL, background=cbg,
                             foreground=dfg,
                             command=lambda: self.openinbrowser(n_field, 0, APP.gui.freq_input.get(), mode))
            menu.add_command(label="Open " + n_field[2] + " in Web browser with pre-set TDoA extension loaded",
                             state=NORMAL, background=cbg, foreground=dfg,
                             command=lambda: self.openinbrowser(n_field, 1, APP.gui.freq_input.get(), mode))
            menu.add_command(label="Open " + n_field[1] + "/status", background=cbg, foreground=dfg,
                             command=lambda: self.openinbrowser(n_field, 2, None, None))
            if LISTENMODE == "0":
                # Add demodulation process line
                menu.add_command(label="Listen to that frequency using " + n_field[2], state=NORMAL, background=cbg,
                                 foreground=dfg,
                                 command=lambda *args: [self.listenmode(n_field, APP.gui.modulation_box.get()),
                                                        self.populate("add", "yes", n_field)])
            else:
                menu.add_command(label="Stop Listen Mode", state=NORMAL, background=cbg, foreground=dfg,
                                 command=lambda *args: [self.stoplistenmode(), self.populate("del", "yes", n_field)])
        if permit_web:
            menu.add_command(label="Get Waterfall & SNR from " + n_field[2], background=cbg, foreground=dfg,
                             command=CheckSnr(n_field[1]).start)
        menu.add_separator()
        if n_field[0] in WHITELIST:  # if node is a favorite
            menu.add_command(label="remove from favorites", background=cbg, foreground=dfg,
                             command=lambda x=n_field[0]: self.remfavorite(x))
        elif n_field[0] not in BLACKLIST:
            menu.add_command(label="add to favorites", background=cbg, foreground=dfg,
                             command=lambda x=n_field[0]: self.addfavorite(x))
        if n_field[0] in BLACKLIST:  # if node is blacklisted
            menu.add_command(label="remove from blacklist", background=cbg, foreground=dfg,
                             command=lambda x=n_field[0]: self.remblacklist(x))
        elif n_field[0] not in WHITELIST:
            menu.add_command(label="add to blacklist", background=cbg, foreground=dfg,
                             command=lambda x=n_field[0]: self.addblacklist(x))
        menu.tk_popup(int(popx), int(popy))  # popup placement // node icon

    @staticmethod
    def addfavorite(node):
        """ Add Favorite node submenu entry. """
        WHITELIST.append(node)
        SaveCfg().save_cfg("nodes", "whitelist", WHITELIST)
        APP.gui.redraw()

    @staticmethod
    def remfavorite(node):
        """ Remove Favorite node submenu entry. """
        WHITELIST.remove(node)
        SaveCfg().save_cfg("nodes", "whitelist", WHITELIST)
        APP.gui.redraw()

    @staticmethod
    def addblacklist(node):
        """ Add Blacklist node submenu entry. """
        BLACKLIST.append(node)
        SaveCfg().save_cfg("nodes", "blacklist", BLACKLIST)
        APP.gui.redraw()

    @staticmethod
    def remblacklist(node):
        """ Remove Blacklist node submenu entry. """
        BLACKLIST.remove(node)
        SaveCfg().save_cfg("nodes", "blacklist", BLACKLIST)
        APP.gui.redraw()

    @staticmethod
    def get_font_color(font_color):
        """ Adapting the foreground font color regarding background luminosity.
        stackoverflow questions/946544/good-text-foreground-color-for-a-given-background-color """
        rgb_hex = [font_color[x:x + 2] for x in [1, 3, 5]]
        threshold = THRES  # default = 186
        if int(rgb_hex[0], 16) * 0.299 + int(rgb_hex[1], 16) * 0.587 + int(rgb_hex[2], 16) * 0.114 > threshold:
            return "#000000"
        # else:
        return "#ffffff"
        # if (red*0.299 + green*0.587 + blue*0.114) > 186 use #000000 else use #ffffff

    @staticmethod
    def color_variant(hex_color, brightness_offset=1):
        """ Routine used to change color brightness according to SNR scaled value.
        chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html """
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join(["0" + hex(i)[2:] if len(hex(i)[2:]) < 2 else hex(i)[2:] for i in new_rgb_int])

    @staticmethod
    def openinbrowser(node_id, extension, freq, modul):
        """ Web browser call to connect on the node. """
        if extension == 0:
            webbrowser.open_new("http://" + node_id[1] + "/?f=" + freq + modul)
        elif extension == 2:
            webbrowser.open_new("http://" + node_id[1] + "/status")
        else:
            webbrowser.open_new(
                "http://" + node_id[1] + "/?f=" + freq + modul + "&ext=tdoa,lat:" + node_id[4] + ",lon:" + node_id[
                    5] + ",z:5," + node_id[2])

    @staticmethod
    def listenmode(node_id, modulation):
        """ Start listen mode process. """
        server_host = node_id[1].rsplit(":", 2)[0]
        server_port = node_id[1].rsplit(":", 2)[1]
        server_frequency = APP.gui.freq_input.get()
        demod_thread = StartDemodulation(server_host, server_port, server_frequency, modulation)
        APP.gui.start_rec_button.configure(state="disabled")
        APP.gui.purge_button.configure(state="disabled")
        APP.gui.update_button.configure(state="disabled")
        if LISTENMODE == "0":
            demod_thread.start()
        else:
            os.kill(kiwisdrclient_pid, signal.SIGTERM)
            demod_thread.start()

    @staticmethod
    def stoplistenmode():
        """ Stop listen mode process. """
        global LISTENMODE
        os.kill(kiwisdrclient_pid, signal.SIGTERM)
        LISTENMODE = "0"
        APP.gui.writelog("Stopping Listen mode")
        APP.gui.start_rec_button.configure(state="normal")
        APP.gui.purge_button.configure(state="normal")
        APP.gui.update_button.configure(state="normal")

    def populate(self, action, listenmode, sel_node_tag):
        """ TDoA mode / Listen mode listing populate/depopulate process. """
        if action == "add" and listenmode == "no":
            if len(fulllist) < 6 and (ultimate.get()) == 0:
                fulllist.append(
                    sel_node_tag[1].rsplit(':')[0] + "$" + sel_node_tag[1].rsplit(':')[1] + "$" + sel_node_tag[
                        0] + "$" + sel_node_tag[2].replace("/", ""))
                FillMapWithNodes(self).node_sel_active(sel_node_tag[0])
            elif (ultimate.get()) == 1:
                fulllist.append(
                    sel_node_tag[1].rsplit(':')[0] + "$" + sel_node_tag[1].rsplit(':')[1] + "$" + sel_node_tag[
                        0] + "$" + sel_node_tag[2].replace("/", ""))
                FillMapWithNodes(self).node_sel_active(sel_node_tag[0])
            else:
                tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="6 nodes Maximum !")
        elif action == "del" and listenmode == "no":
            fulllist.remove(
                sel_node_tag[1].rsplit(':')[0] + "$" + sel_node_tag[1].rsplit(':')[1] + "$" + sel_node_tag[0] + "$" +
                sel_node_tag[2].replace("/", ""))
            FillMapWithNodes(self).node_selection_inactive(sel_node_tag[0])
        elif action == "add" and listenmode == "yes":
            FillMapWithNodes(self).node_sel_active(sel_node_tag[0])
        elif action == "del" and listenmode == "yes":
            FillMapWithNodes(self).node_selection_inactiveall()
        if fulllist:
            APP.title(VERSION + " - Selected nodes [" + str(len(fulllist)) + "] : " + '/'.join(
                str(p).rsplit('$')[3] for p in fulllist))
        else:
            APP.title(VERSION)

    def move_from(self, event):
        """ Move from. """
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        """ Move to. """
        if 'HOST' in globals() and "current" not in self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]:
            pass
        elif "current" in self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.show_image()  # redraw the image

    def wheel(self, event):
        """ Routine for mouse wheel actions. """
        x_eve = self.canvas.canvasx(event.x)
        y_eve = self.canvas.canvasy(event.y)
        global image_scale
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x_eve < bbox[2] and bbox[1] < y_eve < bbox[3]:
            pass  # Ok! Inside the image
        else:
            return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 2000:
                return  # block zoom if image is less than 2000 pixels
            self.imscale /= self.delta
            scale /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale *= self.delta
        # rescale all canvas objects
        # scale = 2.0 or 0.5
        image_scale = self.imscale
        # APP.gui.label04.configure(text="Map Zoom : " + str(int(image_scale)))
        self.canvas.scale('all', x_eve, y_eve, scale, scale)
        # self.canvas.scale('')
        self.show_image()

    def show_image(self, event=None):
        """ Creating the canvas with the picture. """
        global b_box2
        b_box1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        b_box1 = (b_box1[0] + 1, b_box1[1] + 1, b_box1[2] - 1, b_box1[3] - 1)
        b_box2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                  self.canvas.canvasy(0),
                  self.canvas.canvasx(self.canvas.winfo_width()),
                  self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(b_box1[0], b_box2[0]), min(b_box1[1], b_box2[1]),  # get scroll region box
                max(b_box1[2], b_box2[2]), max(b_box1[3], b_box2[3])]
        if bbox[0] == b_box2[0] and bbox[2] == b_box2[2]:  # whole image in the visible area
            bbox[0] = b_box1[0]
            bbox[2] = b_box1[2]
        if bbox[1] == b_box2[1] and bbox[3] == b_box2[3]:  # whole image in the visible area
            bbox[1] = b_box1[1]
            bbox[3] = b_box1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x_1 = max(b_box2[0] - b_box1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y_1 = max(b_box2[1] - b_box1[1], 0)
        x_2 = min(b_box2[2], b_box1[2]) - b_box1[0]
        y_2 = min(b_box2[3], b_box1[3]) - b_box1[1]
        if int(x_2 - x_1) > 0 and int(y_2 - y_1) > 0:  # show image if it in the visible area
            x = min(int(x_2 / self.imscale), self.width)  # sometimes it is larger on 1 pixel...
            y = min(int(y_2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x_1 / self.imscale), int(y_1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x_2 - x_1), int(y_2 - y_1))))
            imageid = self.canvas.create_image(max(b_box2[0], b_box1[0]), max(b_box2[1], b_box1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


class MainWindow(Frame):
    """ GUI design definitions. """

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.member1 = GuiCanvas(parent)
        ReadKnownPointFile().run()
        global image_scale, selectedcity, selectedlat, selectedlon
        global lpcut, hpcut, tcpclient, auto_run_tdoa, tdoa_mode, mode
        global ultimate, ultimatefav, runultimateintf, map_preset, rec_in_progress, tdoa_in_progress
        ultimate = IntVar(self)
        ultimatefav = IntVar(self)
        runultimateintf = IntVar(self)
        tcpclient = IntVar(self)
        auto_run_tdoa = IntVar(self)
        tdoa_mode = "_S_F"
        dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        la_f = "TkFixedFont 7 bold"
        mode = "USB"
        lpcut = 0
        hpcut = 3600
        image_scale = 1
        selectedlat = ""
        selectedlon = ""
        selectedcity = ""
        map_preset = 0
        rec_in_progress = 0
        tdoa_in_progress = 0

        # Control panel background
        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.69, relheight=0.4, relwidth=1)
        self.label0.configure(bg=BGC, fg=FGC, width=214)

        # Map Legend
        self.label01 = Label(parent)
        self.label01.place(x=0, y=0, height=14, width=105)
        self.label01.configure(bg="black", font=la_f, anchor="w", fg=STDCOLOR, text="█ Standard")
        self.label02 = Label(parent)
        self.label02.place(x=0, y=14, height=14, width=105)
        self.label02.configure(bg="black", font=la_f, anchor="w", fg=FAVCOLOR, text="█ Favorite")
        self.label03 = Label(parent)
        self.label03.place(x=0, y=28, height=14, width=105)
        self.label03.configure(bg="black", font=la_f, anchor="w", fg=BLKCOLOR, text="█ Blacklisted")
        self.label04 = Label(parent)
        self.label04.place(x=0, y=42, height=14, width=105)
        self.label04.configure(bg="black", font=la_f, anchor="w", fg="white",
                               text="█ Visible: " + str(NODE_COUNT_FILTER) + "/" + str(NODE_COUNT))
        self.label05 = Label(parent)
        self.label05.place(x=0, y=56, height=14, width=105)
        self.label05.configure(bg="black", font=la_f, anchor="w", fg="white", text="█ USB BW: 3.6 kHz")

        # Frequency entry field
        self.freq_input = Entry(parent)
        self.freq_input.place(x=105, rely=0.892, height=24, width=Font(family="TkFixedFont").measure("30000.0"))
        self.freq_input.configure(bg="#ffffff", disabledforeground=dfgc, fg="#000000", font="TkFixedFont",
                                  insertbackground="#000000")
        self.freq_input.bind('<Control-a>', self.ctrla)
        self.freq_input.bind('<Return>', self.return_key)
        self.freq_input.bind('<KP_Enter>', self.return_key)
        self.freq_input.bind('<Key>', lambda x: self.freqbox())
        self.freq_input.bind('<FocusIn>', self.ctrla)
        self.freq_input.focus_set()

        # Frequency entry legend
        self.label1 = Label(parent)
        self.label1.place(relx=0.01, rely=0.895)
        self.label1.configure(bg=BGC, font="TkFixedFont", fg=FGC, text="Freq (kHz)")

        # Modulation Combobox
        self.modulation_box = ttk.Combobox(parent, state="readonly")
        self.modulation_box.place(x=180, rely=0.892, height=24, width=Font(family="TkFixedFont").measure("abcdefg"))
        self.modulation_box.configure(font="TkTextFont",
                                      values=["USB", "LSB", "CW", "AM", "IQ 2kHz", "IQ 4kHz", "IQ 6kHz", "IQ 8kHz"])
        self.modulation_box.current(0)
        self.modulation_box.bind("<<ComboboxSelected>>", self.modechoice)

        # Start/Stop recording button
        self.start_rec_button = Button(parent)
        self.start_rec_button.place(relx=0.77, rely=0.89, height=24, relwidth=0.10)
        self.start_rec_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="#d9d9d9",
                                        disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                        highlightcolor="#000000", pady="0", text="Start recording",
                                        command=self.start_stop_rec, state="normal")

        # Start & Stop TDoA button
        self.start_tdoa_button = Button(parent)
        self.start_tdoa_button.place(relx=0.88, rely=0.89, height=24, relwidth=0.1)
        self.start_tdoa_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg='#d9d9d9',
                                         disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                         highlightcolor="#000000", pady="0", text="Start TDoA proc",
                                         command=self.start_stop_tdoa, state="disabled")

        # Known places search textbox
        self.choice = Entry(parent)
        self.choice.place(relx=0.01, rely=0.95, height=21, relwidth=0.1)
        self.choice.insert(0, "POI Search")
        self.listbox = Listbox(parent)
        self.listbox.place(relx=0.12, rely=0.95, height=21, relwidth=0.38)

        # UltimateTDoA checkbox
        self.ultimate_checkbox = Checkbutton(parent)
        self.ultimate_checkbox.place(relx=0.507, rely=0.89, height=21, relwidth=0.108)
        self.ultimate_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                         font="TkFixedFont 8", width=214, selectcolor=BGC, text="ultimateTDoA mode",
                                         anchor="w", highlightthickness=0, variable=ultimate,
                                         command=self.checkboxcheck)

        # UltimateTDoA (favorites) checkbox
        self.ultimate_fav_checkbox = Checkbutton(parent)
        self.ultimate_fav_checkbox.place(relx=0.617, rely=0.89, height=21, relwidth=0.06)
        self.ultimate_fav_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                             font="TkFixedFont 8", width=214, selectcolor=BGC, text="fav. only",
                                             anchor="w", state="disabled", highlightthickness=0, variable=ultimatefav)

        # UltimateTDoA (run interface) checkbox
        self.run_ultimate_intf_checkbox = Checkbutton(parent)
        self.run_ultimate_intf_checkbox.place(relx=0.678, rely=0.89, height=21, relwidth=0.077)
        self.run_ultimate_intf_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                                  font="TkFixedFont 8", width=214, selectcolor=BGC,
                                                  text="run interface", anchor="w", state="disabled",
                                                  highlightthickness=0, variable=runultimateintf)

        # TCP Client checkbox
        self.tcpclient_checkbox = Checkbutton(parent)
        self.tcpclient_checkbox.place(relx=0.507, rely=0.922, height=21, relwidth=0.108)
        self.tcpclient_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                          font="TkFixedFont 8", width=214, selectcolor=BGC, text="TCP client",
                                          anchor="w", state="disabled", highlightthickness=0, variable=tcpclient,
                                          command=self.tcpclientcheck)

        # TCP Client TDoA autorun checkbox (use with standard TDoA mode 3-6 nodes only)
        self.autorun_checkbox = Checkbutton(parent)
        self.autorun_checkbox.place(relx=0.617, rely=0.922, height=21, relwidth=0.055)
        self.autorun_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                        font="TkFixedFont 8", width=214, selectcolor=BGC, text="autorun",
                                        anchor="w", highlightthickness=0, state="disabled", variable=auto_run_tdoa,
                                        command=self.autorunchoice)

        # Update button
        self.update_button = Button(parent)
        self.update_button.place(relx=0.90, rely=0.94, height=24, relwidth=0.08)
        self.update_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="#d9d9d9",
                                     disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                     highlightcolor="#000000", pady="0", text="update map", command=self.runupdate,
                                     state="normal")

        # Purge node listing button
        self.purge_button = Button(parent)
        self.purge_button.place(relx=0.81, rely=0.94, height=24, relwidth=0.08)
        self.purge_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="orange",
                                    disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                    highlightcolor="#000000", pady="0", text="Purge Nodes", command=self.purgenode,
                                    state="normal")

        # Console window
        self.console_window = Text(parent)
        self.console_window.place(relx=0.005, rely=0.7, relheight=0.18, relwidth=0.615)
        self.console_window.configure(bg=CONS_B, font="TkTextFont", fg=CONS_F, highlightbackground=BGC,
                                      highlightcolor=FGC, insertbackground=FGC, selectbackground="#c4c4c4",
                                      selectforeground=FGC, undo="1", width=970, wrap="word")

        # Adding some texts to console window at program start
        self.writelog("This is " + VERSION + ", a GUI written for python 2/3 with Tk")
        self.writelog("All credits to Christoph Mayer for his excellent TDoA work (http://hcab14.blogspot.com)")
        self.writelog(
            "Already computed TDoA runs : " + str([len(d) for r, d, folder in os.walk(os.path.join('TDoA', 'iq'))][0]))
        self.writelog("There are " + str(NODE_COUNT) + " KiwiSDRs in the db. Have fun !")
        self.writelog("TDoA default settings : plot_kiwi_json=" + PKJ + " | use_constraints=" + UC + " | " + (
            "former TDoA algorithm" if TDOAVERSION == "false" else "new TDoA algorithm (2020)"))

        # Status window
        self.status_window = Text(parent)
        self.status_window.place(relx=0.624, rely=0.7, relheight=0.18, relwidth=0.37)
        self.status_window.configure(bg=STAT_B, font="TkTextFont", fg=STAT_F, highlightbackground=BGC,
                                     highlightcolor=FGC, insertbackground=FGC, selectbackground="#c4c4c4",
                                     selectforeground=FGC, undo="1", width=970, wrap="word")

        # GUI topbar menus
        menubar = Menu(self)
        parent.config(menu=menubar)

        # Map Settings menu
        menu_1 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Map Settings", menu=menu_1)
        sm1 = Menu(menu_1, tearoff=0)
        sm2 = Menu(menu_1, tearoff=0)
        sm3 = Menu(menu_1, tearoff=0)
        sm4 = Menu(menu_1, tearoff=0)
        sm5 = Menu(menu_1, tearoff=0)
        menu_1.add_cascade(label='Default map', menu=sm1, underline=0)
        menu_1.add_command(label="Save map position", command=self.set_map_position)
        menu_1.add_cascade(label='Map Filters', menu=sm2, underline=0)
        menu_1.add_cascade(label='Set Colors', menu=sm3, underline=0)
        menu_1.add_cascade(label='Set Icon type', menu=sm4, underline=0)
        menu_1.add_command(label='Set Icon size', command=lambda *args: self.default_icon_size())
        menu_1.add_cascade(label='Set Mapbox style (pdf output)', menu=sm5, underline=0)
        sm1.add_command(label="Browse maps folder", command=self.choose_map)
        sm2.add_command(label="All", command=lambda *args: [SaveCfg().save_cfg("map", "mapfl", 0), self.redraw()])
        sm2.add_command(label="Std+Fav", command=lambda *args: [SaveCfg().save_cfg("map", "mapfl", 1), self.redraw()])
        sm2.add_command(label="Fav", command=lambda *args: [SaveCfg().save_cfg("map", "mapfl", 2), self.redraw()])
        sm2.add_command(label="Black", command=lambda *args: [SaveCfg().save_cfg("map", "mapfl", 3), self.redraw()])
        sm3.add_command(label="Standard node color", command=lambda *args: self.color_change(0))
        sm3.add_command(label="Favorite node color", command=lambda *args: self.color_change(1))
        sm3.add_command(label="Blacklisted node color", command=lambda *args: self.color_change(2))
        sm3.add_command(label="Known map point color", command=lambda *args: self.color_change(3))
        sm3.add_command(label="Icon highlight color", command=lambda *args: self.color_change(4))
        sm4.add_command(label="⚫", command=lambda *args: [SaveCfg().save_cfg("map", "icontype", 0), self.redraw()])
        sm4.add_command(label="■", command=lambda *args: [SaveCfg().save_cfg("map", "icontype", 1), self.redraw()])
        sm5.add_command(label="streets",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "streets-v11"), ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])
        sm5.add_command(label="outdoors",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "outdoors-v11"),
                                               ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])
        sm5.add_command(label="light",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "light-v10"), ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])
        sm5.add_command(label="dark",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "dark-v10"), ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])
        sm5.add_command(label="satellite",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "satellite-v9"),
                                               ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])
        sm5.add_command(label="satellite-streets",
                        command=lambda *args: [SaveCfg().save_cfg("map", "mapbox", "satellite-streets-v11"),
                                               ReadCfg().read_cfg(),
                                               self.writelog("Mapbox style is now set to " + MAP_BOX)])

        # Map Presets menu
        menu_2 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Map Presets", menu=menu_2)
        menu_2.add_command(label="Europe", command=lambda *args: self.map_preset("EU"))
        menu_2.add_command(label="Africa", command=lambda *args: self.map_preset("AF"))
        menu_2.add_command(label="Middle-East", command=lambda *args: self.map_preset("ME"))
        menu_2.add_command(label="South Asia", command=lambda *args: self.map_preset("SAS"))
        menu_2.add_command(label="South-East Asia", command=lambda *args: self.map_preset("SEAS"))
        menu_2.add_command(label="East Asia", command=lambda *args: self.map_preset("EAS"))
        menu_2.add_command(label="North America", command=lambda *args: self.map_preset("NAM"))
        menu_2.add_command(label="Central America", command=lambda *args: self.map_preset("CAM"))
        menu_2.add_command(label="South America", command=lambda *args: self.map_preset("SAM"))
        menu_2.add_command(label="Oceania", command=lambda *args: self.map_preset("O"))
        menu_2.add_command(label="West Russia", command=lambda *args: self.map_preset("WR"))
        menu_2.add_command(label="East Russia", command=lambda *args: self.map_preset("ER"))
        menu_2.add_command(label="USA", command=lambda *args: self.map_preset("US"))
        menu_2.add_command(label="World (use with caution)", command=lambda *args: self.map_preset("W"))

        # TDoA settings menu
        menu_3 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="TDoA settings", menu=menu_3)
        sm8 = Menu(menu_3, tearoff=0)
        sm9 = Menu(menu_3, tearoff=0)
        sm10 = Menu(menu_3, tearoff=0)

        menu_3.add_cascade(label='plot_kiwi_json', menu=sm8, underline=0)
        menu_3.add_cascade(label='algorithm', menu=sm10, underline=0)
        sm8.add_command(label="yes",
                        command=lambda *args: [SaveCfg().save_cfg("iq", "pkj", "true"), ReadCfg().read_cfg()])
        sm8.add_command(label="no",
                        command=lambda *args: [SaveCfg().save_cfg("iq", "pkj", "false"), ReadCfg().read_cfg()])
        sm9.add_command(label="option: use_constraints = 1",
                        command=lambda *args: [SaveCfg().save_cfg("iq", "uc", "true"),
                                               SaveCfg().save_cfg("iq", "mode", "false"),
                                               ReadCfg().read_cfg()])
        sm9.add_command(label="option: use_constraints = 0",
                        command=lambda *args: [SaveCfg().save_cfg("iq", "uc", "false"),
                                               SaveCfg().save_cfg("iq", "mode", "false"),
                                               ReadCfg().read_cfg()])
        sm10.add_cascade(label='former (2018)', menu=sm9, underline=0)
        sm10.add_command(label="new (2020)", command=lambda *args: [SaveCfg().save_cfg("iq", "mode", "true"),
                                                                    SaveCfg().save_cfg("iq", "uc", "false"),
                                                                    ReadCfg().read_cfg()])

        # GUI design
        menu_4 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="GUI design", menu=menu_4)
        sm5 = Menu(menu_4, tearoff=0)
        sm6 = Menu(menu_4, tearoff=0)
        menu_4.add_command(label="GUI background color", command=lambda *args: self.color_change(5))
        menu_4.add_cascade(label='Console', menu=sm5, underline=0)
        sm5.add_command(label="background color", command=lambda *args: self.color_change(6))
        sm5.add_command(label="foreground color", command=lambda *args: self.color_change(7))
        menu_4.add_cascade(label='Status window', menu=sm6, underline=0)
        sm6.add_command(label="background color", command=lambda *args: self.color_change(8))
        sm6.add_command(label="foreground color", command=lambda *args: self.color_change(9))
        menu_4.add_command(label="SNR gradient ratio", command=lambda *args: self.gradient_change())
        menu_4.add_command(label="White/Black font color threshold", command=lambda *args: self.threshold_change())

        # TCP client settings
        menu_5 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="TCP settings", menu=menu_5)
        menu_5.add_command(label="TCP server IP address", command=lambda *args: self.tcp_settings(0))
        menu_5.add_command(label="TCP server port number", command=lambda *args: self.tcp_settings(1))
        menu_5.add_command(label="Set trigger word", command=lambda *args: self.tcp_settings(3))
        menu_5.add_command(label="IQ auto-recording duration", command=lambda *args: self.tcp_settings(2))

        # About menu
        menu_6 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="?", menu=menu_6)
        menu_6.add_command(label="Help", command=self.help)
        menu_6.add_command(label="About", command=self.about)
        menu_6.add_command(label="Update check", command=lambda *args: self.checkversion(source="from_menu"))

        # Various GUI binds
        self.listbox_update(my_info1)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.choice.bind('<FocusIn>', self.resetcity)
        self.choice.bind('<KeyRelease>', self.on_keyrelease)

        # Purge all IQ.wav from iq/ directory every time GUI is started
        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            os.remove(wavfiles)

        # Check if new version is available at program start
        self.checkversion(source="at_start")

    def modechoice(self, event=None):
        """ Selection of modulation and adjust the IQ recording LP & HP values accordingly.
        USB = 0..3600 Hz, LSB = -3600..0 Hz, AM = -5000..5000 Hz, CW = -500..500 Hz etc... """
        global lpcut, hpcut, mode
        modulations = {'USB': [0, 3600, '█ USB BW: 3.6 kHz', 'USB'],
                       'LSB': [-3600, 0, '█ LSB BW: 3.6 kHz', 'LSB'],
                       'CW': [-500, 500, '█ CW BW: 1 kHz', 'CW'],
                       'AM': [-5000, 5000, '█ AM BW: 10 kHz', 'AM'],
                       'IQ 2kHz': [-1000, 1000, '█ IQ BW: 2 kHz', 'AM'],
                       'IQ 4kHz': [-2000, 2000, '█ IQ BW: 4 kHz', 'AM'],
                       'IQ 6kHz': [-3000, 3000, '█ IQ BW: 6 kHz', 'AM'],
                       'IQ 8kHz': [-4000, 4000, '█ IQ BW: 8 kHz', 'AM']}
        lpcut = modulations[self.modulation_box.get()][0]
        hpcut = modulations[self.modulation_box.get()][1]
        self.label05.configure(text=modulations[self.modulation_box.get()][2])
        mode = modulations[self.modulation_box.get()][3]

    def redraw(self):
        self.member1.redraw_map_cmd()

    @staticmethod
    def ctrla(event):
        """ Allow ctrl+A in frequency input textbox. """
        event.widget.select_range(0, 'end')
        event.widget.icursor('end')
        return 'break'

    @staticmethod
    def return_key(event):
        """ Allow Return key in frequency input textbox to start recording. """
        if rec_in_progress == 0:
            APP.gui.start_stop_rec()
        elif (ultimate.get()) == 1:
            APP.gui.start_stop_rec()
        else:
            APP.gui.start_stop_tdoa()
        return 'break'

    @staticmethod
    def freq_focus(event):
        """ Adding Ctrl+F shortcut to focus the frequency input box. """
        APP.gui.freq_input.focus_set()
        APP.gui.freq_input.select_range(0, 'end')
        return 'break'

    def checkboxcheck(self):
        """ UltimateTDoA favorites checkbox management. """
        if ultimate.get() == 1:
            self.ultimate_fav_checkbox.configure(state="normal")
            self.run_ultimate_intf_checkbox.configure(state="normal")
        if ultimate.get() == 0:
            self.ultimate_fav_checkbox.configure(state="disabled")
            self.run_ultimate_intf_checkbox.configure(state="disabled")

    @staticmethod
    def tcpclientcheck():
        """ TCP Client checkbox management. """
        if tcpclient.get() == 1:
            TcpClient(TCPTRIGGER).start()
            runultimateintf.set(0)
            APP.gui.start_rec_button.configure(state="disabled")
            if ultimate.get() == 0:
                APP.gui.autorun_checkbox.configure(state="normal")
        elif rec_in_progress == 1:
            APP.gui.writelog("Disconnected from the TCP server. IQ recording discontinued.")
            APP.gui.start_stop_rec()

        else:
            APP.gui.autorun_checkbox.configure(state="disabled")
            APP.gui.start_rec_button.configure(state="normal")
            auto_run_tdoa.set(0)

    @staticmethod
    def autorunchoice():
        """ Auto-start TDoA process after recordings timeout. """
        if auto_run_tdoa.get() == 1:
            APP.gui.writelog("TDoA process will be started automatically after IQ recordings timeout.")

    def freqbox(self):
        """ freq input box. """
        try:
            if self.freq_input.get() != "" and len(fulllist) >= 3 and 5 < float(APP.gui.freq_input.get()) < 30000:
                APP.gui.tcpclient_checkbox.configure(state="normal")
                if (ultimate.get()) == 0 and mapboundaries_set == 1:
                    APP.gui.autorun_checkbox.configure(state="normal")
            else:
                APP.gui.tcpclient_checkbox.configure(state="disabled")
        except ValueError:
            APP.gui.tcpclient_checkbox.configure(state="disabled")
            APP.gui.autorun_checkbox.configure(state="disabled")

    def on_keyrelease(self, event):
        """ Known place location listing search management. """
        value = event.widget.get()
        value = value.strip().lower()
        if value == '':
            data = my_info1
        else:
            data = []
            for item in my_info1:
                if value in item.lower():
                    data.append(item + " | " + my_info2[my_info1.index(item)] + " " + my_info3[my_info1.index(item)])
        self.listbox_update(data)

    def listbox_update(self, data):
        """ Known place location listing search management. """
        self.listbox.delete(0, 'end')
        data = sorted(data, key=str.lower)
        for item in data:
            self.listbox.insert('end', item)

    def on_select(self, event):
        """ Known place location selection process. """
        global selectedlat, selectedlon, selectedcity
        try:
            if event.widget.get(event.widget.curselection()) == " ":
                tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="Type something in the POI Search box first !")
            else:
                selectedcity = event.widget.get(event.widget.curselection()).rsplit(" |", 1)[0]
                selectedlat = str(my_info2[my_info1.index(selectedcity)])
                selectedlon = str(my_info3[my_info1.index(selectedcity)])
                self.member1.delete_point(n="#POI")
                self.member1.create_known_point(selectedlat, selectedlon, selectedcity)
        except:
            pass

    def resetcity(self, event):
        """ Erase previous known location choice from both textbox input and World map icon and name. """
        global selectedcity, selectedlat, selectedlon
        self.choice.delete(0, 'end')
        if selectedcity:
            self.member1.delete_point(n="#POI")
            selectedcity = " "
            selectedlat = "-90"
            selectedlon = "180"

    def writelog(self, msg):
        """ The main console log text feed. """
        self.console_window.insert('end -1 lines',
                                   "[" + str(time.strftime('%H:%M.%S', time.gmtime())) + "] - " + msg + "\n")
        time.sleep(0.01)
        self.console_window.see('end')

    @staticmethod
    def help():
        """ Get Help web page """
        webbrowser.open('https://github.com/llinkz/directTDoA/wiki/Help')

    @staticmethod
    def about():
        """ Get About web page """
        webbrowser.open('https://github.com/llinkz/directTDoA/wiki')

    def map_preset(self, pmap):
        """ Map boundaries static presets. """
        global mapboundaries_set, lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global sx0, sy0
        global map_preset, map_manual
        if image_scale == 1:
            p_map = []
            if map_preset == 1:
                # if already preset choosed, delete previous one
                self.member1.delete_point("mappreset")
            for i in range(0, 4):
                p_map.append(CFG["presets(x0/y1/x1/y0)"][pmap][i])
            sx0 = (1911 + ((float(p_map[0]) * 1911) / 180))
            sx1 = (1911 + ((float(p_map[2]) * 1911) / 180))
            if float(p_map[1]) > 0:  # point is located in North Hemisphere
                sy0 = (990 - (float(p_map[1]) * 11))
                sy1 = (990 - (float(p_map[3]) * 11))
            else:                     # point is located in South Hemisphere
                sy0 = (990 + (float(0 - (float(p_map[1]) * 11))))
                sy1 = (990 + (float(0 - float(p_map[3])) * 11))
            self.member1.canvas.create_rectangle(sx0, sy0, sx1, sy1, tag="mappreset", outline='yellow')
            self.member1.delete_point("mapmanual")
            lon_min_map = p_map[0]
            lat_max_map = p_map[1]
            lon_max_map = p_map[2]
            lat_min_map = p_map[3]
            mapboundaries_set = 1
            map_preset = 1
            map_manual = 0
        else:
            self.writelog("ERROR : The boundaries selection is forbidden unless map un-zoomed.")

    def default_icon_size(self):
        """ Change map icon size config window. """
        global ICON_CFG
        ICON_CFG = Tk()
        ICON_CFG.geometry("280x50+50+50")
        ICON_CFG.title('Default Icon size')
        icon_slider = Scale(ICON_CFG, from_=1, to=5)
        icon_slider.place(x=10, y=0, width=200, height=100)
        icon_slider.configure(orient="horizontal", showvalue="1", resolution=1, label="")
        icon_slider.set(ICONSIZE)
        icon_save_button = Button(ICON_CFG, command=lambda *args: self.set_default_icon_size(icon_slider.get()))
        icon_save_button.place(x=220, y=20, height=20)
        icon_save_button.configure(text="Save")

    @staticmethod
    def set_default_icon_size(isize):
        """ Save choosed icon size to config file. """
        APP.gui.writelog("Icon size set to " + str(isize))
        SaveCfg().save_cfg("map", "iconsize", isize)
        ICON_CFG.destroy()
        APP.gui.redraw()

    def gradient_change(self):
        """ Change SNR gradient ratio window. """
        global GRAD_CFG
        GRAD_CFG = Tk()
        GRAD_CFG.geometry("280x50+50+50")
        GRAD_CFG.title('Default SNR gradient ratio')
        icon_slider2 = Scale(GRAD_CFG, from_=1, to=30)
        icon_slider2.place(x=10, y=0, width=200, height=100)
        icon_slider2.configure(orient="horizontal", showvalue="1", resolution=1, label="")
        icon_slider2.set(GRAD)
        icon_save_button2 = Button(GRAD_CFG, command=lambda *args: self.set_default_gradient(icon_slider2.get()))
        icon_save_button2.place(x=220, y=20, height=20)
        icon_save_button2.configure(text="Save")

    @staticmethod
    def set_default_gradient(grad_val):
        """ Save choosed icon size to config file. """
        APP.gui.writelog("SNR gradient set to " + str(grad_val))
        SaveCfg().save_cfg("guicolors", "grad", grad_val)
        GRAD_CFG.destroy()
        APP.gui.redraw()

    def threshold_change(self):
        """ Change SNR gradient ratio window. """
        global THRES_CFG
        THRES_CFG = Tk()
        THRES_CFG.geometry("280x50+50+50")
        THRES_CFG.title('Black/White font color threshold')
        icon_slider3 = Scale(THRES_CFG, from_=1, to=255)
        icon_slider3.place(x=10, y=0, width=200, height=100)
        icon_slider3.configure(orient="horizontal", showvalue="1", resolution=1, label="")
        icon_slider3.set(THRES)
        icon_save_button2 = Button(THRES_CFG, command=lambda *args: self.set_font_threshold(icon_slider3.get()))
        icon_save_button2.place(x=220, y=20, height=20)
        icon_save_button2.configure(text="Save")

    @staticmethod
    def set_font_threshold(thres_val):
        """ Save Black/White font color threshold (in node menus) to config file. """
        APP.gui.writelog("Black/White font color threshold set to " + str(thres_val))
        SaveCfg().save_cfg("guicolors", "thres", thres_val)
        THRES_CFG.destroy()
        APP.gui.redraw()

    @staticmethod
    def color_change(value):
        """ Ask for a color and save to config file. """
        color_n = askcolor()
        color_n = color_n[1]
        if color_n:
            if value == 0:
                SaveCfg().save_cfg("map", "std", color_n)
                APP.gui.label01.configure(fg=color_n)
            if value == 1:
                SaveCfg().save_cfg("map", "fav", color_n)
                APP.gui.label02.configure(fg=color_n)
            if value == 2:
                SaveCfg().save_cfg("map", "blk", color_n)
                APP.gui.label03.configure(fg=color_n)
            if value == 3:
                SaveCfg().save_cfg("map", "poi", color_n)
                APP.gui.writelog("Known places color is now " + color_n)
            if value == 4:
                SaveCfg().save_cfg("map", "hlt", color_n)
                APP.gui.writelog("Icon highlight color is now " + color_n)
            if value == 5:
                SaveCfg().save_cfg("guicolors", "main_b", color_n)
                APP.gui.writelog("GUI background color is now " + color_n)
                nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                chg_list = [APP.gui.label0, APP.gui.label1, APP.gui.ultimate_checkbox, APP.gui.ultimate_fav_checkbox,
                            APP.gui.run_ultimate_intf_checkbox, APP.gui.tcpclient_checkbox, APP.gui.autorun_checkbox]
                APP.gui.ultimate_checkbox.configure(activebackground=color_n,
                                                    activeforeground=GuiCanvas.get_font_color(color_n),
                                                    selectcolor=color_n)
                APP.gui.ultimate_fav_checkbox.configure(activebackground=color_n,
                                                        activeforeground=GuiCanvas.get_font_color(color_n),
                                                        selectcolor=color_n)
                APP.gui.run_ultimate_intf_checkbox.configure(activebackground=color_n,
                                                             activeforeground=GuiCanvas.get_font_color(color_n),
                                                             selectcolor=color_n)
                APP.gui.tcpclient_checkbox.configure(activebackground=color_n,
                                                     activeforeground=GuiCanvas.get_font_color(color_n),
                                                     selectcolor=color_n)
                APP.gui.autorun_checkbox.configure(activebackground=color_n,
                                                   activeforeground=GuiCanvas.get_font_color(color_n),
                                                   selectcolor=color_n)
                for x, l in zip(nums, chg_list):
                    l.configure(background=color_n)
                    l.configure(foreground=GuiCanvas.get_font_color(color_n))
                    SaveCfg().save_cfg("guicolors", "main_f", GuiCanvas.get_font_color(color_n))
            if value == 6:
                SaveCfg().save_cfg("guicolors", "cons_b", color_n)
                APP.gui.writelog("Console background color is now " + color_n)
                APP.gui.console_window.configure(bg=color_n)
            if value == 7:
                SaveCfg().save_cfg("guicolors", "cons_f", color_n)
                APP.gui.writelog("Console foreground color is now " + color_n)
                APP.gui.console_window.configure(fg=color_n)
            if value == 8:
                SaveCfg().save_cfg("guicolors", "stat_b", color_n)
                APP.gui.writelog("Status window background color is now " + color_n)
                APP.gui.status_window.configure(bg=color_n)
            if value == 9:
                SaveCfg().save_cfg("guicolors", "stat_f", color_n)
                APP.gui.writelog("Status window foreground color is now " + color_n)
                APP.gui.status_window.configure(fg=color_n)
        else:
            pass
        APP.gui.redraw()

    @staticmethod
    def choose_map():
        """ Change map menu and save to config file. """
        mapname = tkFileDialog.askopenfilename(initialdir="maps")
        if not mapname or not mapname.lower().endswith(('.png', '.jpg', '.jpeg')):
            tkMessageBox.showinfo("", message="Error, select png/jpg/jpeg files only.")
            mapname = "maps/directTDoA_map_grayscale_with_sea.jpg"
        SaveCfg().save_cfg("map", "file", "maps/" + os.path.split(mapname)[1])
        SaveCfg().save_cfg("map", "x0", str(b_box2[0]))
        SaveCfg().save_cfg("map", "y0", str(b_box2[1]))
        SaveCfg().save_cfg("map", "x1", str(b_box2[2]))
        SaveCfg().save_cfg("map", "y1", str(b_box2[3]))
        APP.gui.writelog("Restart the application to take into account the change of the world map")

    @staticmethod
    def tcp_settings(value):
        global TCPHOST, TCPPORT, IQDURATION, TCPTRIGGER
        if value == 0:
            tcp_ip_address = askstring("Enter TCP server IP address", "current=" + TCPHOST)
            if tcp_ip_address:
                SaveCfg().save_cfg("tcp", "host", tcp_ip_address)
                ReadCfg().read_cfg()
                APP.gui.writelog("TCP server IP address has been set to " + str(tcp_ip_address))
            else:
                APP.gui.writelog("Sorry, the server host IP address is incorrect. retry.")
        if value == 1:
            tcp_port_number = askinteger("Enter TCP server port number", "(49152-65535) - current=" + str(TCPPORT))
            if 49151 < tcp_port_number < 65536:
                SaveCfg().save_cfg("tcp", "port", tcp_port_number)
                ReadCfg().read_cfg()
                APP.gui.writelog("TCP server port number has been set to " + str(tcp_port_number))
            else:
                APP.gui.writelog("Sorry, that port number is incorrect. retry.")
        if value == 2:
            auto_iq_duration = askinteger("Enter auto-recording duration (3-120s)", "current=" + str(IQDURATION) + "s")
            if 2 < auto_iq_duration < 121:
                SaveCfg().save_cfg("tcp", "duration", auto_iq_duration)
                ReadCfg().read_cfg()
                APP.gui.writelog("Auto-recording IQ duration has been set to " + str(auto_iq_duration) + "s")
            else:
                APP.gui.writelog("Sorry, auto-recording IQ duration is out of limits. retry")
        if value == 3:
            trigger = askstring("Enter trigger word", "simple or regexp accepted - current= " + str(TCPTRIGGER))
            if trigger:
                SaveCfg().save_cfg("tcp", "word", trigger)
                ReadCfg().read_cfg()
                APP.gui.writelog("Trigger word has been set to " + str(trigger))
            else:
                SaveCfg().save_cfg("tcp", "word", "")
                ReadCfg().read_cfg()
                APP.gui.writelog(
                    "Warning, with blank word the recording will start on any event appearing on TCP server side.")

    @staticmethod
    def set_map_position():
        """ Remember the map position and save to config file. """
        SaveCfg().save_cfg("map", "x0", str(b_box2[0]))
        SaveCfg().save_cfg("map", "y0", str(b_box2[1]))
        SaveCfg().save_cfg("map", "x1", str(b_box2[2]))
        SaveCfg().save_cfg("map", "y1", str(b_box2[3]))
        APP.gui.writelog("Default map position has been saved in config file")

    def runupdate(self):
        """ Run Web source availability check. """
        self.start_rec_button.configure(state="disabled")
        self.start_tdoa_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self.purge_button.configure(state="disabled")
        self.purgenode()
        # start the Check update thread
        CheckUpdate().start()

    def purgenode(self):
        """ Purge KiwiSDR node list process. """
        global fulllist
        fulllist = []
        APP.title(VERSION)
        self.member1.unselect_allpoint()
        # self.writelog("Node listing has been cleared.")
        tcpclient.set(0)
        auto_run_tdoa.set(0)
        APP.gui.tcpclient_checkbox.configure(state="disabled")
        APP.gui.autorun_checkbox.configure(state="disabled")

    @staticmethod
    def checkversion(source):
        """ Watch on github if a new version has been released (1st line of README.md parsed). """
        try:
            checkver = requests.get('https://raw.githubusercontent.com/llinkz/directTDoA/master/README.md', timeout=2)
            gitsrctext = checkver.text.split("\n")
            if float(gitsrctext[0][2:].split("v", 1)[1]) > float(VERSION.split("v", 1)[1][:4]):
                tkMessageBox.showinfo(title="", message=str(gitsrctext[0][2:]) + " released !")
            else:
                if source == "from_menu":
                    tkMessageBox.showinfo(title="", message="No update found.")
        except (ImportError, requests.RequestException):
            print ("Unable to verify version information. Sorry.")

    def start_stop_rec(self):
        """ Actions to perform when Record button is clicked. """
        global FREQUENCY
        global starttime, rec_in_progress, tdoa_mode
        tdoa_mode = "_" + ("U" if ultimate.get() == 1 else "S") + ("A" if tcpclient.get() == 1 else "") + "_F"
        try:
            if rec_in_progress == 1:  # stop rec process
                os.kill(PROC2_PID, signal.SIGTERM)  # kills the kiwirecorder.py process
                time.sleep(0.5)
                rec_in_progress = 0
                self.start_rec_button.configure(text="Start recording")
                self.purge_button.configure(state="normal")
                self.create_m_file()
                self.writelog("IQ Recordings stopped... files have been saved in " + str(
                    os.sep + os.path.join('TDoA', 'iq') + os.sep + starttime) + tdoa_mode + str(FREQUENCY) + str(
                    os.sep))
                r_dir = os.path.join('TDoA', 'iq') + os.sep + starttime + tdoa_mode + str(FREQUENCY)
                try:
                    if platform.system() == "Windows":
                        webbrowser.open(r_dir)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", r_dir])
                    else:
                        subprocess.Popen(["xdg-open", r_dir])
                except ValueError:
                    pass
                for GNSSfile in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.txt"):
                    shutil.move(GNSSfile, os.path.join('TDoA', 'gnss_pos') + os.sep + GNSSfile.rsplit(os.sep, 2)[2])
                if (ultimate.get()) == 1:
                    self.start_tdoa_button.configure(text="", state="disabled")
                    if tcpclient.get() != 1 and runultimateintf.get() == 1:
                        ComputeUltimate().start()

            else:  # start rec process
                if (ultimate.get()) == 0 and mapboundaries_set is None:
                    self.writelog("ERROR : set map geographical boundaries !")
                else:
                    starttime = str(time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
                    if self.freq_input.get() == '' or float(self.freq_input.get()) < 0 or float(
                            self.freq_input.get()) > 30000:
                        self.writelog("ERROR : Please check the frequency !")
                    elif (ultimate.get()) == 0 and len(fulllist) < 3:  # debug
                        self.writelog("ERROR : Select at least 3 nodes for TDoA processing !")
                    elif (ultimate.get()) == 0 and len(fulllist) > 6:  # debug
                        self.writelog("ERROR : Too much nodes selected for a standard TDoA processing, remove " + str(
                            len(fulllist) - 6) + " nodes please !")
                    elif (ultimate.get()) == 1 and len(fulllist) < 3:
                        self.writelog("ERROR : Select at least 3 nodes for an ultimateTDoA recording !")
                    else:
                        if (ultimate.get()) == 1:
                            self.start_tdoa_button.configure(text="", state="disabled")
                        FREQUENCY = str(float(self.freq_input.get()))
                        self.start_rec_button.configure(text="Stop recording")
                        if (ultimate.get()) == 0:
                            self.start_tdoa_button.configure(text="Start TDoA proc", state="normal")
                        for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                            os.remove(wavfiles)
                        time.sleep(0.2)
                        self.status_window.delete("0.0", END)
                        StartRecording(self).start()
                        rec_in_progress = 1
        except ValueError:
            self.writelog("ERROR : Please check the frequency !")

    def start_stop_tdoa(self):
        """ Actions to perform when TDoA button is clicked. """
        global PROC_PID, PROC2_PID, rec_in_progress, tdoa_in_progress
        if tdoa_in_progress == 1:  # Abort TDoA process
            self.start_rec_button.configure(text="Start recording", state="normal")
            self.start_tdoa_button.configure(text="", state="disabled")
            self.purge_button.configure(state="normal")
            try:  # kills the octave process
                os.kill(PROC_PID, signal.SIGTERM)
            except (NameError, OSError):
                pass
            try:  # and ghostscript
                if platform.system() == "Windows":
                    if "gs.exe" in os.popen("tasklist").read():
                        os.system("taskkill /F /IM gs.exe")
                else:
                    os.system("killall -9 gs")
            except (NameError, OSError):
                pass
            self.writelog("Octave process has been aborted...")
            for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
                os.remove(wavfiles)
            tdoa_in_progress = 0

        else:  # Start TDoA process
            tdoa_in_progress = 1
            try:  # to kill kiwirecorder.py
                os.kill(PROC2_PID, signal.SIGTERM)
            except (NameError, OSError):
                pass
            self.start_rec_button.configure(text="", state="disabled")
            self.start_tdoa_button.configure(text="Abort TDoA proc")
            if rec_in_progress == 1:
                for GNSSfile in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.txt"):
                    shutil.move(GNSSfile, os.path.join('TDoA', 'gnss_pos') + os.sep + GNSSfile.rsplit(os.sep, 2)[2])
                self.create_m_file()
            PlotIQ().start()
            self.writelog("Now running Octave process... please wait...")
            time.sleep(0.5)
            rec_in_progress = 0
            OctaveProcessing().start()

    def create_m_file(self):
        """ Octave .m files creation processes. """
        global KHZ_FREQ, ale_file_name, ale_file_data, tdoa_mode
        if platform.system() == "Windows":
            os_sep = "\\\\"
        else:
            os_sep = os.sep
        iq_files = []
        run_dir = os.path.join('TDoA', 'iq') + os_sep + starttime + tdoa_mode + str(FREQUENCY) + os_sep
        os.makedirs(run_dir)
        run_type = ""
        for iq_file in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            copyfile(iq_file, run_dir + iq_file.rsplit(os.sep, 1)[1])
            iq_files.append(os.path.split(iq_file)[1])
        try:
            if tcpclient.get() == 1:
                with open(run_dir + ale_file_name, "w") as ale_file_desc:
                    ale_file_desc.write(ale_file_data.decode('utf-8'))
                ale_file_desc.close()
                try:
                    for ale_file in glob.glob(run_dir + "ALE*.txt"):
                        a = open(ale_file, 'r')
                        aledata = a.read()
                        a.close()
                        try:
                            run_type = " - [ALE ID: " + str(
                                re.search(r".+\[(TWS|TIS)\]\[(.*)\]\[", aledata).group(2)) + "]"
                        except AttributeError:
                            run_type = " - [ALE]"
                except NameError:
                    pass
        except NameError:
            pass
        firstfile = iq_files[0]
        KHZ_FREQ = str(firstfile.split("_", 2)[1].split("_", 1)[0])
        proc_m_name = os.path.join('TDoA') + os.sep + "proc_tdoa_" + str(firstfile.split("_", 2)[1].split("_", 1)[0])
        with open(proc_m_name + ".m", "w") as m_file:
            m_file.write("""## -*- octave -*-
## This file was auto-generated by """ + VERSION + """
## """ + str(b_box2[0]) + """,""" + str(b_box2[1]) + """
\nfunction [tdoa,input]=proc_tdoa_""" + KHZ_FREQ + """
  exitcode = 0;
  status   = struct;\n
  try
    status.version = tdoa_get_version();

""")
            if (ultimate.get()) == 1:
                m_file.write("  # nodes\n")
            else:
                for i in range(len(iq_files)):
                    m_file.write("    input(" + str(i + 1) + ").fn = fullfile('iq', '" + str(iq_files[i]) + "');\n")
            m_file.write("""
    config = struct('lat_range', [""" + str(lat_min_map) + """ """ + str(lat_max_map) + """],
                    'lon_range', [""" + str(lon_min_map) + """ """ + str(lon_max_map) + """],""")
            if selectedlat == "" or selectedlon == "":
                m_file.write("""
                    'known_location', struct('coord', [-90 180],
                                              'name',  ' '),""")
            else:
                m_file.write("""
                    'known_location', struct('coord', [""" + str(selectedlat) + """ """ + str(selectedlon) + """],
                                             'name',  '""" + str(selectedcity.rsplit(' (')[0].replace('_', ' ')) + """'),""")
            m_file.write("""
                    'dir', 'png',
                    'plot_kiwi', false,
                    'plot_kiwi_json', """ + str(PKJ) + """,
                    'use_constraints', """ + str(UC) + """,
                    'new', """ + str(TDOAVERSION) + """
                   );

    ## determine map resolution and create config.lat and config.lon fields
    config = tdoa_autoresolution(config);

    [input,status.input] = tdoa_read_data(config, input, 'gnss_pos');

    config.plotname = sprintf('TDoA_""" + KHZ_FREQ + """');
    config.title    = sprintf('""" + FREQUENCY + """ """ + mode + """ [BW=""" + str(abs(lpcut - hpcut))
                         + """] - REC on """ + str(datetime.utcnow().strftime('%d %b %Y %H%M.%Sz'))
                         + run_type + """');
    
    if config.new
      [tdoa, status.cross_correlations] = tdoa_compute_lags_new(input);
    else
      [tdoa, status.cross_correlations] = tdoa_compute_lags(input, ...
                                                            struct('dt',     12000,            # 1-second cross-correlation intervals
                                                                   'range',  0.005,            # peak search range is +-5 ms
                                                                   'dk',    [-2:2],            # use 5 points for peak fitting
                                                                   'fn', @tdoa_peak_fn_pol2fit,# fit a pol2 to the peak
                                                                   'remove_outliers', ~config.use_constraints
                                                                  ));
    end

    if config.use_constraints
      [tdoa,status.cross_correlations] = tdoa_cluster_lags(config, tdoa, input, status.cross_correlations);
      [tdoa,input,status.constraints]  = tdoa_verify_lags (config, tdoa, input);
    end
    [tdoa,status.position] = tdoa_plot_map(input, tdoa, config);
    # if config.new
    #   tdoa = tdoa_plot_dt_new(input, tdoa, config, 1e-2);
    # else
    #   tdoa = tdoa_plot_dt (input, tdoa, config, 2.5e-3);
    # end
  catch err
    json_save_cc(stderr, err);
    status.octave_error = err;
    exitcode            = 1;
  end_try_catch

  try
    fid = fopen(fullfile('png', 'status.json'), 'w');
    json_save_cc(fid, status);
    fclose(fid);
  catch err
    json_save_cc(stderr, err);
    exitcode += 2;
  end_try_catch

  if exitcode != 0
    exit(exitcode);
  end
""")
            m_file.write("""
# Set T time for filenames
[tdoatime] = strftime (\"%d%b%Y_%H%M%Sz\", gmtime (time ()));
\n# Get coordinates from the current TDoA computing
global mlp;
[lat,lon] = deal(strsplit(mlp, \" \"){4}, strsplit(strsplit(mlp, \" \"){6}, \"]\"){1});
\n# Get Mapbox with the most_likely coordinates of the current TDoA computing""")

            # Adapt the getmap.py arguments if a known place has been set or not
            if platform.system() == "Windows":
                python_path = '..\\\python\\\pythonw.exe'
            else:
                python_path = 'python'
            if selectedlat == "" or selectedlon == "":
                m_file.write("""
[curlcmd] = [\"""" + python_path + """ ", "..""" + os_sep + """getmap.py ", lat, " ", lon, " -90", " 180", " """
                             + MAP_BOX + """ ", \"""" + run_dir[5:] + """TDoA_Map.png", " proc_tdoa_"""
                             + KHZ_FREQ + """.m"];""")
            else:
                m_file.write("""
[curlcmd] = [\"""" + python_path + """ ", "..""" + os_sep + """getmap.py ", lat, " ", lon, " """
                             + str(selectedlat) + """", " """ + str(selectedlon) + """", " """
                             + MAP_BOX + """ ", \"""" + run_dir[5:] + """TDoA_Map.png", " proc_tdoa_"""
                             + KHZ_FREQ + """.m"];""")

            m_file.write("""
system(curlcmd);
\n# Merge TDoA result (pdf) + Mapbox (pdf) + plot_iq (pdf) into a single .pdf file
[gscmd] = ["gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=""" + run_dir[5:] + """TDoA_"""
                         + str(KHZ_FREQ) + """_", tdoatime, ".pdf pdf""" + os_sep + """TDoA_""" + str(KHZ_FREQ) + """.pdf """
                         + run_dir[5:] + """TDoA_Map.pdf """ + run_dir[5:] + """TDoA_"""
                         + str(KHZ_FREQ) + """_spec.pdf -c \\\"[ /Title (TDoA_"""
                         + str(KHZ_FREQ) + """_", tdoatime, ".pdf) /DOCINFO pdfmark\\\" -f\"];
system(gscmd);
\n# Delete some files
delete(\"""" + run_dir[5:] + """TDoA_Map.pdf")
disp("finished");
endfunction
""")
        m_file.close()
        time.sleep(0.2)
        if (ultimate.get()) == 1:
            copyfile(proc_m_name + ".m", run_dir + "proc_tdoa_" + KHZ_FREQ + ".empty")
            if platform.system() == "Windows":
                copyfile("compute_ultimate.bat", run_dir + "compute_ultimate.bat")
            copyfile("compute_ultimate.py", run_dir + "compute_ultimate.py")
            copyfile('plot_iq.py', run_dir + "plot_iq.py")
            copyfile('trim_iq.py', run_dir + "trim_iq.py")
            os.chmod(run_dir + "compute_ultimate.py", 0o777)
            os.chmod(run_dir + "plot_iq.py", 0o777)
            os.chmod(run_dir + "trim_iq.py", 0o777)
            # PlotIQ().start()
        else:
            copyfile(proc_m_name + ".m", run_dir + "proc_tdoa_" + KHZ_FREQ + ".m")
            if platform.system() == "Windows":
                with open(run_dir + "recompute.bat", "w") as recompute:
                    recompute.write(""":: """ + VERSION + """ - Windows recompute TDoA batch file
:: This script moves *.wav back to iq directory and proc_tdoa_""" + KHZ_FREQ + """.m to
:: TDoA directory then opens a file editor so you can modify .m file parameters.
@echo off
set PATH=%CD%\..\..\..\octave\\bin;%CD%\..\..\..\python;%PATH%
if not exist *spec.pdf pythonw.exe plot_iq.py
copy *.wav ..\\
copy proc_tdoa_""" + KHZ_FREQ + """.m ..\..\\
cd ..\..
start /W notepad "proc_tdoa_""" + KHZ_FREQ + """.m"
octave-cli.exe proc_tdoa_""" + KHZ_FREQ + """.m
del proc_tdoa_""" + KHZ_FREQ + """.m""")
                recompute.close()
                copyfile('plot_iq.py', run_dir + "plot_iq.py")
                copyfile('trim_iq.py', run_dir + "trim_iq.py")
            else:
                with open(run_dir + "recompute.sh", "w") as recompute:
                    recompute.write("""#!/bin/bash
## This script moves *.wav back to iq directory and proc_tdoa_""" + KHZ_FREQ + """.m to
## TDoA directory then opens a file editor so you can modify .m file parameters.
[ ! -f ./TDoA_""" + KHZ_FREQ + """_spec.pdf ] && python plot_iq.py
cp ./*.wav ../
cp proc_tdoa_""" + KHZ_FREQ + """.m ../../
cd ../..
$EDITOR proc_tdoa_""" + KHZ_FREQ + """.m
octave-cli proc_tdoa_""" + KHZ_FREQ + """.m
rm -f proc_tdoa_""" + KHZ_FREQ + """.m""")
                # octave-cli """ + ("--eval " if sys.version_info[0] == 3 else "") + """proc_tdoa_""" + KHZ_FREQ
                # + (".m" if sys.version_info[0] == 2 else "") + """
                recompute.close()
                os.chmod(run_dir + "recompute.sh", 0o777)
                copyfile('plot_iq.py', run_dir + "plot_iq.py")
                copyfile('trim_iq.py', run_dir + "trim_iq.py")
                os.chmod(run_dir + "plot_iq.py", 0o777)
                os.chmod(run_dir + "trim_iq.py", 0o777)


class MainW(Tk, object):
    """ Creating the Tk GUI design. """

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.gui = MainWindow(self)


def on_closing():
    """ Actions to perform when software is closed using the top-right check button. """
    if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
        try:  # to kill octave
            os.kill(PROC_PID, signal.SIGTERM)
        except (NameError, OSError):
            pass
        try:  # to kill kiwirecorder.py
            os.kill(PROC2_PID, signal.SIGTERM)
        except (NameError, OSError):
            pass
        try:  # to kill kiwirecorder.py in LISTENING MODE
            os.kill(kiwisdrclient_pid, signal.SIGTERM)
        except (NameError, OSError):
            pass
        APP.update_idletasks()
        SaveCfg().save_cfg("map", "gui", APP.geometry())
        os.kill(os.getpid(), signal.SIGTERM)
        APP.destroy()


if __name__ == '__main__':
    APP = MainW()
    APP.title(VERSION)
    APP.protocol("WM_DELETE_WINDOW", on_closing)
    APP.bind("<Control-f>", MainWindow.freq_focus)
    APP.mainloop()
