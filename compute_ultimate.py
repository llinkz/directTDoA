#!/usr/bin/python
# -*- coding: utf-8 -*-
""" compute_ultimate python code. """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import glob
import sys
import json
import os
from os.path import dirname as up
import re
import signal
import subprocess
import threading
import time
import math
import platform
import webbrowser
from io import BytesIO
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageTk

# python 2/3 compatibility
if sys.version_info[0] == 2:
    import tkMessageBox
    from Tkinter import Checkbutton, CURRENT, IntVar, Listbox
    from Tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas
    from tkFont import Font

else:
    import tkinter.messagebox as tkMessageBox
    from tkinter import Checkbutton, CURRENT, IntVar, Listbox
    from tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas
    from tkinter.font import Font

VERSION = "ultimateTDoA interface v2.00 "
for mfi_le in glob.glob('*.*m*'):
    ff = open(mfi_le, 'r')
    fi_le_d = ff.read()
    ff.close()
    FREQUENCY = re.search(r".+title.+\'(.+)\s-\sR.+\'", fi_le_d).group(1)
ALEID = ""
CLICKEDNODE = ""
if str(os.getcwd().rsplit("_", 2)[1]) == "UA":
    for ale_file in glob.glob(os.getcwd() + os.sep + "ALE*.txt"):
        a = open(ale_file, 'r')
        aledata = a.read()
        a.close()
        try:
            ALEID = " [ALE ID: " + str(re.search(r".+\[(TWS|TIS)\]\[(.*)\]\[", aledata).group(2)) + "]"
        except AttributeError:
            ALEID = " [ALE]"

cdict1 = {
    'red': ((0.0, 0.0, 0.0),
            (0.077, 0.0, 0.0),
            (0.16, 0.0, 0.0),
            (0.265, 1.0, 1.0),
            (0.403, 1.0, 1.0),
            (0.604, 1.0, 1.0),
            (1.0, 1.0, 1.0)),

    'green': ((0.0, 0.0, 0.0),
              (0.077, 0.0, 0.0),
              (0.16, 1.0, 1.0),
              (0.265, 1.0, 1.0),
              (0.403, 0.0, 0.0),
              (0.604, 0.0, 0.0),
              (1.0, 0.764, 0.764)),

    'blue': ((0.0, 0.117, 0.117),
             (0.077, 1.0, 1.0),
             (0.16, 1.0, 1.0),
             (0.265, 0.0, 0.0),
             (0.403, 0.0, 0.0),
             (0.604, 1.0, 1.0),
             (1.0, 1.0, 1.0)),
}

COLORMAP = LinearSegmentedColormap('SAColorMap', cdict1, 1024)


class Restart(object):
    """ GUI Restart routine. """

    def __init__(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def run():
        """ GUI Restart routine. """
        try:  # to kill octave-cli process if exists
            os.kill(PROC_PID, signal.SIGTERM)
        except (NameError, OSError):
            pass
        if platform.system() == "Windows":
            os.execlp("pythonw.exe", "pythonw.exe", "compute_ultimate.py")
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)


class ReadKnownPointFile(threading.Thread):
    """ Read known location list routine (see directTDoA_knownpoints.db file). """

    def __init__(self):
        super(ReadKnownPointFile, self).__init__()

    def run(self):
        """ Read known location list routine (see directTDoA_knownpoints.db file). """
        with open(up(up(up(os.getcwd()))) + os.sep + "directTDoA_knownpoints.db") as h:
            global my_info1, my_info2, my_info3
            i = 3  # skip the 3x comment lines at start of the text file database
            lines = h.readlines()
            my_info1 = []
            my_info2 = []
            my_info3 = []
            while i < sum(1 for _ in open(up(up(up(os.getcwd()))) + os.sep + "directTDoA_knownpoints.db")):
                inforegexp = re.search(r"(.*),(.*),(.*)", lines[i])
                my_info1.append(inforegexp.group(1))
                my_info2.append(inforegexp.group(2))
                my_info3.append(inforegexp.group(3))
                i += 1
        h.close()


class ReadCfg(object):
    """ DirectKiwi configuration file read process. """

    def __init__(self):
        pass

    @staticmethod
    def read_cfg():
        """ compute_ultimate.py configuration file read process. """
        global CFG, DX0, DY0, DX1, DY1, DMAP
        global POICOLOR, ICONSIZE, ICONTYPE, HIGHLIGHT
        global BGC, FGC, CONS_B, CONS_F, MAP_BOX
        try:
            # Read the config file v5.0 format and declare variables
            with open(up(up(up(os.getcwd()))) + os.sep + 'directTDoA.cfg', 'r') as config_file:
                CFG = json.load(config_file, object_pairs_hook=OrderedDict)
            DX0, DX1 = CFG["map"]["x0"], CFG["map"]["x1"]
            DY0, DY1 = CFG["map"]["y0"], CFG["map"]["y1"]
            DMAP, ICONSIZE = CFG["map"]["file"], CFG["map"]["iconsize"]
            POICOLOR, ICONTYPE = CFG["map"]["poi"], CFG["map"]["icontype"]
            HIGHLIGHT = CFG["map"]["hlt"]
            BGC, FGC = CFG["guicolors"]["main_b"], CFG["guicolors"]["main_f"]
            CONS_B, CONS_F = CFG["guicolors"]["cons_b"], CFG["guicolors"]["cons_f"]
            MAP_BOX = CFG["map"]["mapbox"]
        except (ImportError, ValueError):
            sys.exit("config file not found")


class TrimIQ(threading.Thread):
    """ trim_iq.py processing routine """

    def __init__(self, tdoa_rootdir):
        super(TrimIQ, self).__init__()
        self.tdoa_rootdir = tdoa_rootdir

    def run(self):
        APP.gui.writelog("trim_iq.py script started.")
        APP.gui.writelog("Click & drag : Select the time portion of the IQ record that you want to keep.")
        APP.gui.writelog("Close window : No change made to the IQ.")
        APP.gui.writelog("Single click : Deletes IQ.")
        APP.gui.writelog("< 2 seconds  : Deletes IQ.")
        subprocess.call([sys.executable, 'trim_iq.py'], cwd=self.tdoa_rootdir, shell=False)
        Restart().run()


class PlotIQ(threading.Thread):
    """ Plot_iq, enhanced version with SNR ranking. """

    def __init__(self, iqfile, mode, filelist):
        super(PlotIQ, self).__init__()
        self.iqfile = iqfile
        self.plot_mode = mode
        self.filelist = filelist

    def run(self):
        global scores
        plt.rcParams.update({'figure.max_open_warning': 0})
        # mode 0 = GUI display preview
        # mode 1 = temp.pdf (for a run with 3 < nodes < 6)
        if self.plot_mode == 1:
            files = {path: self.load(path) for path in self.filelist}
            scores = sorted([(path, self.score(data)) for path, data in files.items()], key=lambda item: item[1],
                            reverse=True)
            self.plot(files, scores, cols=3, iqfile=files)
        else:
            self.plot(self.load(self.iqfile), order=None, cols=1, iqfile=self.iqfile)

    @staticmethod
    def load(path):
        """ Remove GNSS from IQ recordings. """
        buf = BytesIO()
        with open(path, 'rb') as f:
            size = os.path.getsize(path)
            for i in range(62, size, 2074):
                f.seek(i)
                buf.write(f.read(2048))
        data = np.frombuffer(buf.getvalue(), dtype='int16')
        data = data[0::2] + 1j * data[1::2]
        return data

    @staticmethod
    def score(data):
        """ IQ SNR calculation. """
        max_snr = 0.0
        for offset in range(12000, len(data), 512):
            snr = np.std(np.fft.fft(data[offset:], n=1024))
            if snr > max_snr:
                max_snr = snr
        return max_snr

    @staticmethod
    def has_gps(path):
        """ Detect if IQ file has GPS GNSS data (in test). """
        gpslast = 0
        f_wav = open(path, 'rb')
        for i in range(2118, os.path.getsize(path), 2074):
            f_wav.seek(i)
            if sys.version_info[0] < 3:
                gpslast = max(gpslast, ord(f_wav.read(1)[0]))
            else:
                gpslast = max(gpslast, f_wav.read(1)[0])
        return 0 < gpslast < 254

    @staticmethod
    def plot(files, order, cols, iqfile):
        if not order:
            # mode 0
            global CLICKEDNODE
            CLICKEDNODE = iqfile.rsplit('_', 3)[2]
            buf = BytesIO()
            fig, a_x = plt.subplots()
            a_x.specgram(files, NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)), noverlap=512,
                         vmin=10, vmax=200, cmap=COLORMAP)
            a_x.set_title(iqfile.rsplit('_', 3)[2])
            a_x.axes.get_yaxis().set_visible(False)
            plt.savefig(buf, bbox_inches='tight')
            img = ImageTk.PhotoImage(Image.open(buf).resize((320, 240), Image.ANTIALIAS))
            APP.gui.plot_iq_button.configure(image=img)
            APP.gui.plot_iq_button.image = img
        else:
            # mode 1
            rows = int(math.ceil(len(files) / cols))
            fig, axs = plt.subplots(ncols=cols, nrows=rows)
            fig.set_figwidth(cols * 5.27)
            fig.set_figheight(rows * 3)
            for i, (path, _) in enumerate(order):
                a_x = axs.flat[i]
                a_x.specgram(files[path], NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)),
                             noverlap=512, vmin=10, vmax=200, cmap=COLORMAP)
                a_x.set_title(path.rsplit('_', 3)[2])
                a_x.axes.get_yaxis().set_visible(False)
            for i in range(len(scores), len(axs.flat)):
                fig.delaxes(axs.flat[i])
            fig.savefig('TDoA_' + str(path.rsplit("_", 3)[1]) + '_temp.pdf', bbox_inches='tight')


class OctaveProcessing(threading.Thread):
    """ Octave processing routine """

    def __init__(self, input_file, tdoa_rootdir, log_file):
        super(OctaveProcessing, self).__init__()
        self.m_file_to_process = input_file
        self.tdoa_rootdir = tdoa_rootdir
        self.log_file = log_file

    def run(self):
        global PROC_PID  # stdout
        APP.gui.console_window.configure(bg=CONS_B, fg=CONS_F)
        octave_errors = [b'index-out-of-bounds', b'< 2 good stations found', b'Octave:nonconformant - args',
                         b'n_stn=2 is not supported', b'resample.m: p and q must be positive integers',
                         b'Octave:invalid-index', b'incomplete \'data\' chunk',
                         b'reshape: can\'t reshape 0x0 array to 242x258 array', b'malformed filename:',
                         b'element number 1 undefined in return list']
        proc = subprocess.Popen(['octave-cli', self.m_file_to_process], cwd=self.tdoa_rootdir, stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, shell=False)
        PROC_PID = proc.pid
        if PROC_PID:
            APP.gui.writelog("ultimateTDoA process started.")
        logfile = open(self.log_file, 'w')
        if sys.version_info[0] == 2:
            for octave_output in proc.stdout:
                logfile.write(octave_output)
                if any(x in octave_output for x in octave_errors):
                    APP.gui.console_window.configure(bg='#800000', fg='white')
                    ProcessFailed(octave_output).start()
                    proc.terminate()
                if b"finished" in octave_output:
                    logfile.close()
                    ProcessFinished(self.log_file).start()
                    proc.terminate()
        else:
            octave_output = proc.communicate()[0]
            logfile.write(str(octave_output, 'utf-8'))
            if any(x in octave_output for x in octave_errors):
                APP.gui.console_window.configure(bg='#800000', fg='white')
                ProcessFailed(octave_output).start()
                proc.terminate()
            if b"finished" in octave_output:
                logfile.close()
                ProcessFinished(self.log_file).start()
                proc.terminate()
        proc.wait()


class ProcessFailed(threading.Thread):
    """ The actions to perform when a TDoA run has failed. """

    def __init__(self, returned_error):
        super(ProcessFailed, self).__init__()
        self.Returned_error = returned_error

    def run(self):
        global tdoa_in_progress  # TDoA process status
        APP.gui.writelog(
            "TDoA process error.\n" + bytes.decode(self.Returned_error).rsplit(",\n\t\"stack", 1)[0].replace(
                "{\n\t\"identifier\": \"\",\n\t", ""))
        APP.gui.compute_button.configure(text="Compute")
        tdoa_in_progress = 0


class ProcessFinished(threading.Thread):
    """ The actions to perform when a TDoA run has finished. """

    def __init__(self, log_file):
        super(ProcessFinished, self).__init__()
        self.log_file = log_file

    def run(self):
        global tdoa_in_progress  # TDoA process status
        APP.gui.compute_button.configure(text="Compute")
        tdoa_in_progress = 0
        with open(os.getcwd() + os.sep + self.log_file, 'r') as read_file:
            content = read_file.readlines()
            for line in content:
                if "last_gnss_fix" in line:
                    APP.gui.writelog("  " + " ".join(line.rstrip().rsplit(" ", 5)[2:]))
                if "position" in line:
                    APP.gui.writelog("  " + line.rstrip())
                if "tdoa_plot_map_combined" in line:
                    APP.gui.writelog("  " + line.rstrip())
        APP.gui.writelog("TDoA process finished successfully.")
        if open_pdf.get() == 1:
            if platform.system() == "Windows":
                os.system('start ' + sorted(glob.iglob('*.pdf'), key=os.path.getctime)[-1])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", os.getcwd() + os.sep + sorted(glob.iglob('*.pdf'), key=os.path.getctime)[-1]])
            else:
                subprocess.Popen(["xdg-open", os.getcwd() + os.sep + sorted(glob.iglob('*.pdf'), key=os.path.getctime)[-1]])
        for spec_file in glob.glob(os.getcwd() + os.sep + "*temp.pdf"):
            os.remove(spec_file)


class FillMapWithNodes(threading.Thread):
    """ process to display the nodes on the World Map. """

    def __init__(self, parent):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
        """ ultimate interface process to display the nodes on the World Map. """
        global tag_list, node_file, node_list, deleted_file, ranking_scale
        tag_list = []
        node_list = []
        node_file = []
        deleted_file = 0
        ranking_scale = []
        point_list = []
        for wavfiles in glob.glob('*.wav'):
            if PlotIQ.has_gps(wavfiles):
                node_snr_rank = PlotIQ.score(PlotIQ.load(wavfiles))
                ranking_scale.append(node_snr_rank)
                tdoa_id = re.search(r'(.*)_(.*)_iq.wav', wavfiles)
                node_list.append(tdoa_id.group(2))
                node_file.append(wavfiles)
                with open(up(up(os.getcwd())) + os.sep + "gnss_pos" + os.sep + tdoa_id.group(2) + ".txt", "rt") as gnss:
                    contents = gnss.read()
                    info = re.search(r'd\.(.+?)\s.+\W.\[(.*),(.*)\], \'host\', \'(.+?)\', \'port\', (.+?)\);', contents)
                nodeinfo = dict(
                    url=(info.group(4) + ":" + info.group(5)),
                    lat=info.group(2),
                    lon=info.group(3),
                    id=info.group(1),
                    snr=str(node_snr_rank)
                )
                point_list.append([nodeinfo, node_snr_rank])
            else:
                os.rename(wavfiles, wavfiles + ".nogps")
                deleted_file += 1
        if 'APP' in globals():
            APP.gui.writelog(str(len(node_file)) + " nodes are available for this run.")
        if deleted_file > 0:
            APP.gui.writelog(str(deleted_file) + " node(s) excluded because of missing GPS data.")
        for it in point_list:
            self.add_point(it[0], (it[1] - min(ranking_scale)) * (1/(max(ranking_scale) - min(ranking_scale)) * 255))

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

    def add_point(self, node_db_data, snr_rank):
        """ Process that add node icons over the World map. """
        global tag_list
        mykeys = ['url', 'id', 'lat', 'lon', 'snr']
        node_lat = self.convert_lat(node_db_data["lat"])
        node_lon = self.convert_lon(node_db_data["lon"])
        node_tag = str('$'.join([node_db_data[x] for x in mykeys]))
        node_tag = node_tag.rsplit('$', 1)[0] + "$%g" % round(snr_rank, 0)
        ic_size = int(ICONSIZE)
        try:
            if ICONTYPE == 0:
                self.parent.canvas.create_oval(node_lon - ic_size, node_lat - ic_size, node_lon + ic_size,
                                               node_lat + ic_size, fill=self.color_variant(snr=snr_rank), tag=node_tag)
            else:
                self.parent.canvas.create_rectangle(node_lon - ic_size, node_lat - ic_size, node_lon + ic_size,
                                                    node_lat + ic_size, fill=self.color_variant(snr=snr_rank),
                                                    tag=node_tag)
            self.parent.canvas.tag_bind(node_tag, "<Button-1>", self.parent.onclickleft)
            tag_list.append(node_tag)
        except NameError:
            print("OOPS - Error in adding the point to the map")

    def delete_point(self, map_definition):
        """ Map presets deletion process. """
        self.parent.canvas.delete(map_definition)

    @staticmethod
    def color_variant(snr):
        green_val = min([255, max([0, int(snr)])])
        return "#00" + "".join("0" + hex(green_val)[2:] if len(hex(green_val)[2:]) < 2 else hex(green_val)[2:]) + "00"

    @staticmethod
    def get_font_color(font_color):
        """ Adapting the foreground font color regarding background luminosity.
        stackoverflow questions/946544/good-text-foreground-color-for-a-given-background-color """
        rgb_hex = [font_color[x:x + 2] for x in [1, 3, 5]]
        threshold = 120  # default = 120
        if int(rgb_hex[0], 16) * 0.299 + int(rgb_hex[1], 16) * 0.587 + int(rgb_hex[2], 16) * 0.114 > threshold:
            return "#000000"
        # else:
        return "#ffffff"
        # if (red*0.299 + green*0.587 + blue*0.114) > 186 use #000000 else use #ffffff

    def node_sel_active(self, node_mac):
        """ Adding additionnal highlight on node icon. """
        for node_tag_item in tag_list:
            if node_mac in node_tag_item:
                tmp_latlon = node_tag_item.rsplit("$", 4)
                tmp_lat = self.convert_lat(tmp_latlon[2])
                tmp_lon = self.convert_lon(tmp_latlon[3])
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


class GuiCanvas(Frame):
    """ Process that creates the GUI map canvas, enabling move & zoom on a picture.
    source: stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 """

    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        # tip: GuiCanvas is member1
        parent.geometry("1200x700+150+10")
        global fulllist, mapboundaries_set, map_preset, selectedcity
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map, selectedlat, selectedlon
        fulllist = []
        mapboundaries_set = None
        map_preset = 1
        ReadCfg().read_cfg()
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
        self.image = Image.open(up(up(up(os.getcwd()))) + os.sep + DMAP)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the image
        self.delta = 2.0  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.rect = None
        self.start_x = None
        self.start_y = None
        for mfil_e in glob.glob(os.getcwd() + os.sep + "proc*.empty"):
            m = open(mfil_e, 'r')
            filedata = m.read()
            m.close()
            try:
                mapposx = re.search(r"##\s(.*),(.*)", filedata)
                tdoa_x0 = mapposx.group(1)
                tdoa_y0 = mapposx.group(2)
            except AttributeError:
                tdoa_x0 = DX0
                tdoa_y0 = DY0
            lat = re.search(r"lat_range', \[([-]?[0-9]{1,2}(\.[0-9]*)?) ?([-]?[0-9]{1,2}(\.[0-9]*|))?\]", filedata)
            lon = re.search(r"lon_range', \[([-]?[0-9]{1,3}(\.[0-9]*)?) ?([-]?[0-9]{1,3}(\.[0-9]*|))?\]", filedata)
            lat_min_map = lat.group(1)
            lat_max_map = lat.group(3)
            lon_min_map = lon.group(1)
            lon_max_map = lon.group(3)
            place_regexp_coords = re.search(r"('known_location', struct\('coord', \[([-]?[0-9]{1,2}(\.[0-9]*)?|0) ?([-]?[0-9]{1,3}(\.[0-9]*)?|0)\],)", filedata)
            selectedlat = place_regexp_coords.group(2)
            selectedlon = place_regexp_coords.group(4)
            selectedcity = re.search(r"('name',\s '(.+)'\),)", filedata).group(2)
            self.canvas.create_rectangle(self.convert_lon(lon_min_map), self.convert_lat(lat_max_map),
                                         self.convert_lon(lon_max_map), self.convert_lat(lat_min_map), outline='red',
                                         tag="mappreset")
            self.create_known_point(selectedlat, selectedlon, selectedcity)
        self.canvas.scan_dragto(-int(tdoa_x0.split('.')[0]), -int(tdoa_y0.split('.')[0]), gain=1)
        FillMapWithNodes(self).start()

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

    def on_button_press(self, event):
        """ Red rectangle selection drawing on the World map. """
        global map_preset
        self.delete_point("mappreset")
        if map_preset == 1:
            self.rect = None
            map_preset = 0
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red', tag="mapmanual")

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
                # expand rectangle as you drag the mouse
                self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
                self.show_image()
        else:
            pass

    @staticmethod
    def on_button_release(event):
        """ When Mouse right button is released (map boundaries set or ultimateTDoA set). """

        global mapboundaries_set, map_preset  # lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global map_manual
        if map_preset == 1 and map_manual == 0:
            pass
        else:
            try:
                mapboundaries_set = 1
                map_manual = 1
            except NameError:
                pass

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

    def delete_point(self, n):
        """ KnownPoint deletion process. """
        FillMapWithNodes(self).delete_point(n.rsplit(' (')[0])

    def onclickleft(self, event):
        """ Left Mouse Click bind on the World map. """
        global HOST, node_file, node_list
        menu0 = Menu(self, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')  # node overlap list menu
        menu1 = Menu(self, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')
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
                    # mykeys = ['url', 'id', 'lat', 'lon', 'snr']
                    # n_field    0      1      2     3     4
                    n_field = HOST.rsplit("$", 4)
                    cbg = FillMapWithNodes.color_variant(snr=n_field[4])
                    dfg = FillMapWithNodes.get_font_color(cbg)
                    # check if node is already in the TDoA node listing
                    if len([el for el in fulllist if n_field[1] == el.rsplit("$", 3)[2]]) != 1:
                        name = n_field[1]
                    else:
                        name = "✔ " + n_field[1]
                    menu0.add_command(label=name, background=cbg, foreground=dfg,
                                      command=lambda x=HOST: self.create_node_menu(x, event.x_root, event.y_root,
                                                                                   menu1))
                else:
                    pass
            menu0.tk_popup(event.x_root, event.y_root)
        else:
            HOST = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
            self.create_node_menu(HOST, event.x_root, event.y_root, menu1)

    def create_node_menu(self, kiwinodetag, popx, popy, menu):
        n_field = kiwinodetag.rsplit("$", 5)
        matches = [el for el in fulllist if n_field[1] == el.rsplit("$", 3)[2]]
        cbg = FillMapWithNodes.color_variant(snr=n_field[4])
        dfg = FillMapWithNodes.get_font_color(cbg)
        # show IQ spectrogram in GUI (PlotIQ mode 0)
        PlotIQ(node_file[node_list.index(n_field[1].replace("/", ""))], 0, 0).run()
        if len(matches) != 1:
            menu.add_command(label="Add " + n_field[1] + " for TDoA process", background=cbg, foreground=dfg,
                             font="TkFixedFont 7 bold", command=lambda *args: self.populate("add", n_field))
        elif len(matches) == 1:
            menu.add_command(label="Remove " + n_field[1] + " from TDoA process]", background=cbg, foreground=dfg,
                             font="TkFixedFont 7 bold", command=lambda: self.populate("del", n_field))
        menu.tk_popup(int(popx), int(popy))  # popup placement // node icon

    def populate(self, action, sel_node_tag):
        """ TDoA listing node populate/depopulate process. """
        if action == "add":
            if len(fulllist) < 6:
                fulllist.append(
                    sel_node_tag[0].rsplit(':')[0] + "$" + sel_node_tag[0].rsplit(':')[1] + "$" + sel_node_tag[
                        1].replace("/", ""))
                FillMapWithNodes(self).node_sel_active(sel_node_tag[0])
            else:
                tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="6 nodes Maximum !")
        elif action == "del":
            fulllist.remove(
                sel_node_tag[0].rsplit(':')[0] + "$" + sel_node_tag[0].rsplit(':')[1] + "$" + sel_node_tag[1].replace(
                    "/", ""))
            FillMapWithNodes(self).node_selection_inactive(sel_node_tag[0])
        if fulllist:
            APP.title(VERSION + "| " + FREQUENCY + ALEID + " - Selected nodes [" + str(
                len(fulllist)) + "] : " + '/'.join(str(p).rsplit('$')[2] for p in fulllist))
        else:
            APP.title(VERSION + "| " + FREQUENCY + ALEID)

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
        ReadKnownPointFile().start()
        global image_scale, node_file
        global map_preset, tdoa_in_progress, open_pdf
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        image_scale = 1
        la_f = Font(family="TkFixedFont", size=7, weight="bold")
        map_preset = 0
        tdoa_in_progress = 0
        open_pdf = IntVar(self, value=1)
        # Control panel background
        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.64, relheight=0.4, relwidth=1)
        self.label0.configure(bg=BGC, fg=FGC, width=214)

        # Compute button
        self.compute_button = Button(parent)
        self.compute_button.place(relx=0.61, rely=0.65, height=64, relwidth=0.115)
        self.compute_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg='#d9d9d9',
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Compute",
                                      command=self.start_stop_tdoa)

        # Trim_iq button
        self.trim_iq_button = Button(parent)
        self.trim_iq_button.place(relx=0.61, rely=0.75, height=24, relwidth=0.115)
        self.trim_iq_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="lightblue",
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Run trim_iq.py",
                                      command=TrimIQ(os.getcwd()).start, state="normal")

        # Purge node listing button
        self.purge_button = Button(parent)
        self.purge_button.place(relx=0.61, rely=0.8, height=24, relwidth=0.115)
        self.purge_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="orange",
                                    disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                    highlightcolor="#000000", pady="0", text="Purge Nodes", command=self.purgenode,
                                    state="normal")

        # Restart button
        self.restart_button = Button(parent)
        self.restart_button.place(relx=0.61, rely=0.85, height=24, relwidth=0.115)
        self.restart_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="red",
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Restart GUI", command=Restart().run,
                                      state="normal")

        # Auto open TDoA PDF result file
        self.open_pdf_checkbox = Checkbutton(parent)
        self.open_pdf_checkbox.place(relx=0.62, rely=0.9, height=21, relwidth=0.11)
        self.open_pdf_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                         font="TkFixedFont 8", width=214, selectcolor=BGC, text="auto-open result",
                                         anchor="w", variable=open_pdf, command=None)

        # Known places search textbox
        self.choice = Entry(parent)
        self.choice.place(relx=0.01, rely=0.95, height=21, relwidth=0.18)
        self.choice.insert(0, "TDoA map city/site search here")
        self.listbox = Listbox(parent)
        self.listbox.place(relx=0.2, rely=0.95, height=21, relwidth=0.3)

        # Known places found text label
        self.label3 = Label(parent)
        self.label3.place(relx=0.54, rely=0.95, height=21, relwidth=0.3)
        self.label3.configure(bg=BGC, font="TkFixedFont", fg=FGC, width=214, text="", anchor="w")

        # Console window
        self.console_window = Text(parent)
        self.console_window.place(relx=0.005, rely=0.65, relheight=0.285, relwidth=0.6)
        self.console_window.configure(bg=CONS_B, font="TkTextFont", fg=CONS_F, highlightbackground=BGC,
                                      highlightcolor=FGC, insertbackground=FGC, selectbackground="#c4c4c4",
                                      selectforeground=FGC, undo="1", width=970, wrap="word")

        # plot IQ preview window
        self.plot_iq_button = Button(parent, command=lambda: APP.gui.openinbrowser(
            [tag_list[tag_list.index(x)].rsplit("$", 4)[0] for x in tag_list if CLICKEDNODE in x],
            ''.join(re.match(r"(\d+.\d+)", FREQUENCY).group(1))))
        self.plot_iq_button.place(relx=0.73, rely=0.65, height=240, width=320)

        # Adding some texts to console window at program start
        self.writelog("This is " + VERSION + ", a GUI written for python 2/3 with Tk")

        # GUI topbar menus
        menubar = Menu(self)
        parent.config(menu=menubar)
        menu_1 = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mapbox style", menu=menu_1)
        menu_1.add_command(label="streets", command=lambda *args: self.mapbox_style("streets-v11"))
        menu_1.add_command(label="outdoors", command=lambda *args: self.mapbox_style("outdoors-v11"))
        menu_1.add_command(label="light", command=lambda *args: self.mapbox_style("light-v10"))
        menu_1.add_command(label="dark", command=lambda *args: self.mapbox_style("dark-v10"))
        menu_1.add_command(label="satellite", command=lambda *args: self.mapbox_style("satellite-v9"))
        menu_1.add_command(label="satellite-streets", command=lambda *args: self.mapbox_style("satellite-streets-v11"))
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
        sm8.add_command(label="yes", command=lambda *args: self.tdoa_settings(0))
        sm8.add_command(label="no", command=lambda *args: self.tdoa_settings(1))
        sm9.add_command(label="option: use_constraints = 1", command=lambda *args: self.tdoa_settings(2))
        sm9.add_command(label="option: use_constraints = 0", command=lambda *args: self.tdoa_settings(3))
        sm10.add_cascade(label='former (2018)', menu=sm9, underline=0)
        sm10.add_command(label="new (2020)", command=lambda *args: self.tdoa_settings(4))

        # Various GUI binds
        self.listbox_update(my_info1)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.choice.bind('<FocusIn>', self.resetcity)
        self.choice.bind('<KeyRelease>', self.on_keyrelease)

    @staticmethod
    def openinbrowser(host_port, freq_and_mode):
        """ Web browser call to connect on the node (default = IQ mode & fixed zoom level at 8). """
        if len(host_port) == 1:
            webbrowser.open_new("http://" + str("".join(host_port)) + "/?f=" + freq_and_mode)

    def mapbox_style(self, value):
        global MAP_BOX
        self.writelog("OPTION: Mapbox output style set to " + value)
        MAP_BOX = value

    def tdoa_settings(self, value):
        global plot_kiwi_json_new, use_constraints_new, algo_new
        if value == 0:
            self.writelog("OPTION: plot_kiwi_json set to YES.")
            plot_kiwi_json_new = "true"
        if value == 1:
            self.writelog("OPTION: plot_kiwi_json set to NO.")
            plot_kiwi_json_new = "false"
        if value == 2:
            self.writelog("OPTION: former TDoA algorithm selected w/ option \'use_constraints\' set to YES.")
            algo_new = "false"
            use_constraints_new = "true"
        if value == 3:
            self.writelog("OPTION: former TDoA algorithm selected w/ option \'use_constraints\' set to NO.")
            algo_new = "false"
            use_constraints_new = "false"
        if value == 4:
            self.writelog("OPTION: new TDoA algorithm selected.")
            algo_new = "true"
            use_constraints_new = "false"

    def map_preset(self, pmap):
        """ Map boundaries static presets. """
        global mapboundaries_set, lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global sx0, sy0
        global map_preset, map_manual
        if image_scale == 1:
            p_map = []
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
                    data.append(item)
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

    def purgenode(self):
        """ Purge ultimateTDoA list process. """
        global fulllist
        fulllist = []
        APP.title(VERSION + "| " + FREQUENCY + ALEID)
        self.member1.unselect_allpoint()

    def start_stop_tdoa(self):
        """ Actions to perform when Compute button is clicked. """
        global tdoa_in_progress, PROC_PID
        global plot_kiwi_json_new, use_constraints_new, algo_new
        global lon_min_map, lon_max_map, lat_min_map, lat_max_map
        global plot_kiwi_json_origin, use_constraints_origin, algo_origin
        global selectedlat, selectedlon, selectedcity
        if tdoa_in_progress == 1:  # Abort TDoA process
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
            tdoa_in_progress = 0
            self.compute_button.configure(text="Compute")
        else:
            if len(fulllist) < 3:  # debug
                self.writelog("ERROR : Select at least 3 nodes for TDoA processing !")
            else:
                new_nodes = []
                file_list = []
                # Open the proc.empty file and read the lines
                for mfile in glob.glob(os.getcwd() + os.sep + "proc*.empty"):
                    f = open(mfile, 'r')
                    file_d = f.read()
                    f.close()
                    # get values from the original .empty proc file
                    plot_kiwi_json_origin = re.search(r"(\s{16}'plot_kiwi_json', (.+),)", file_d).group(2)
                    use_constraints_origin = re.search(r"(\s{16}'use_constraints', (.+),)", file_d).group(2)
                    algo_origin = re.search(r"(\s{16}'new', (.+))", file_d).group(2)
                    dir_origin = re.search(r".+/(.+)/", file_d).group(1)
                    # Fill the .m file with selected node listing
                    i = 1
                    for node in fulllist:
                        new_nodes.append("    input(" + str(i) + ").fn    = fullfile('iq', '" + os.path.basename(
                            os.path.dirname(mfile)) + "', '" + node_file[
                                             node_list.index(node.rsplit("$", 4)[2])] + "\');")
                        file_list.append(node_file[node_list.index(node.rsplit("$", 4)[2])])
                        i += 1
                    file_d = file_d.replace("  # nodes", "\n".join(new_nodes))
                    # Create new config block
                    pkjn = plot_kiwi_json_new if 'plot_kiwi_json_new' in globals() and plot_kiwi_json_origin != plot_kiwi_json_new else plot_kiwi_json_origin
                    uc = use_constraints_new if 'use_constraints_new' in globals() and use_constraints_origin != use_constraints_new else use_constraints_origin
                    al = algo_new if 'algo_new' in globals() and algo_origin != algo_new else algo_origin
                    new_config = """
    config = struct('lat_range', [""" + str(lat_min_map) + " " + str(lat_max_map) + """],
                    'lon_range', [""" + str(lon_min_map) + " " + str(lon_max_map) + """],
                    'known_location', struct('coord', [""" + selectedlat + " " + selectedlon + """],
                                             'name',  '""" + selectedcity.rsplit(' (')[0].replace('_', ' ') + """'),
                    'dir', 'png',
                    'plot_kiwi', false,
                    'plot_kiwi_json', """ + pkjn + """,
                    'use_constraints', """ + uc + """,
                    'new', """ + al + """
                   );"""
                    new_mapbox = "lon, \" " + selectedlat + "\", \" " + selectedlon + "\", \" " + MAP_BOX + " \", \"iq"
                    dir_new = os.path.basename(os.path.dirname(mfile)) if os.path.basename(os.path.dirname(mfile)) != dir_origin else dir_origin
                    # replace old config block by the new one
                    file_d = re.sub('(\n    config = struct(.*)(\n(.*)){9})', new_config, file_d, flags=re.M)
                    file_d = re.sub(r'lon(.*)iq', new_mapbox, file_d)
                    file_d = file_d.replace("spec.pdf", "temp.pdf")
                    file_d = file_d.replace(os.sep + dir_origin, os.sep + dir_new)
                    # get some file names and directory
                    logfile = os.path.basename(mfile).replace("empty", "txt")
                    tdoa_rootdir = up(up(up(mfile)))
                    newfile = tdoa_rootdir + os.sep + os.path.basename(mfile).replace("empty", "m")
                    # create the new proc_tdoa file
                    f = open(newfile, 'w')
                    f.write(file_d)
                    f.close()
                    # get only selected nodes for a TDoA run (PlotIQ mode 1)
                    PlotIQ(None, 1, file_list).run()
                    OctaveProcessing(os.path.basename(mfile).replace("empty", "m"), tdoa_rootdir, logfile).start()
                    self.compute_button.configure(text="Abort TDoA")
                    tdoa_in_progress = 1


class MainW(Tk, object):
    """ Creating the Tk GUI design. """

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.gui = MainWindow(self)


def on_closing():
    """ Actions to perform when software is closed using the top-right check button. """
    try:  # to kill octave
        os.kill(PROC_PID, signal.SIGTERM)
    except (NameError, OSError):
        pass
    os.kill(os.getpid(), signal.SIGTERM)
    APP.destroy()


if __name__ == '__main__':
    APP = MainW()
    APP.title(VERSION + "| " + FREQUENCY + ALEID)
    APP.protocol("WM_DELETE_WINDOW", on_closing)
    APP.mainloop()
