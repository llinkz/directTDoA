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
import struct
import platform
from io import BytesIO
from collections import OrderedDict
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageTk

# python 2/3 compatibility
if sys.version_info[0] == 2:
    import tkMessageBox
    from Tkinter import Checkbutton, CURRENT, NORMAL, IntVar, Listbox
    from Tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas

else:
    import tkinter.messagebox as tkMessageBox
    from tkinter import Checkbutton, CURRENT, NORMAL, IntVar, Listbox
    from tkinter import Entry, Text, Menu, Label, Button, Frame, Tk, Canvas

VERSION = "ultimateTDoA interface"

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
        global PROC_PID
        try:  # to kill octave-cli process if exists
            os.kill(PROC_PID, signal.SIGTERM)
        except (NameError, OSError):
            pass
        if platform.system() == "Windows":
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            APP.destroy()
            subprocess.call([sys.executable, os.path.abspath(__file__)])


class ReadKnownPointFile(object):
    """ Read known location list routine (see directTDoA_knownpoints.db file). """

    def __init__(self):
        pass

    @staticmethod
    def run():
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
        """ DirectTDoA configuration file read process. """
        global CFG, DX0, DY0, DX1, DY1, DMAP, WHITELIST, BLACKLIST
        global STDCOLOR, FAVCOLOR, BLKCOLOR, POICOLOR, ICONSIZE, ICONTYPE, HIGHLIGHT
        global BGC, FGC, GRAD, THRES, CONS_B, CONS_F, MAP_BOX
        try:
            # Read the config file v5.0 format and declare variables
            with open(up(up(up(os.getcwd()))) + os.sep + 'directTDoA.cfg', 'r') as config_file:
                CFG = json.load(config_file, object_pairs_hook=OrderedDict)
            DX0, DX1 = CFG["map"]["x0"], CFG["map"]["x1"]
            DY0, DY1 = CFG["map"]["y0"], CFG["map"]["y1"]
            DMAP, ICONSIZE = CFG["map"]["file"], CFG["map"]["iconsize"]
            STDCOLOR, FAVCOLOR, BLKCOLOR = CFG["map"]["std"], CFG["map"]["fav"], CFG["map"]["blk"]
            POICOLOR, ICONTYPE = CFG["map"]["poi"], CFG["map"]["icontype"]
            WHITELIST, BLACKLIST = CFG["nodes"]["whitelist"], CFG["nodes"]["blacklist"]
            HIGHLIGHT = CFG["map"]["hlt"]
            BGC, FGC, GRAD = CFG["guicolors"]["main_b"], CFG["guicolors"]["main_f"], CFG["guicolors"]["grad"]
            CONS_B, CONS_F = CFG["guicolors"]["cons_b"], CFG["guicolors"]["cons_f"]
            THRES, MAP_BOX = CFG["guicolors"]["thres"], CFG["map"]["mapbox"]
        except (ImportError, ValueError):
            sys.exit("config file not found")


class TrimIQ(threading.Thread):
    """ trim_iq.py processing routine """

    def __init__(self, tdoa_rootdir):
        super(TrimIQ, self).__init__()
        self.tdoa_rootdir = tdoa_rootdir

    def run(self):
        APP.gui.writelog("trim_iq.py script started.")
        APP.gui.writelog("Usage:")
        APP.gui.writelog("Click and Drag : Select a time portion of the IQ record that you want to keep.")
        APP.gui.writelog("Click to close window : No changes on the entire IQ recording.")
        APP.gui.writelog("One click on the spectrogram OR less than 2 seconds selected : Deletes the IQ recording.")
        subprocess.call(['python', 'trim_iq.py'], cwd=self.tdoa_rootdir, shell=False)
        Restart().run()


class PlotIQ(threading.Thread):
    """ plot_iq.py processing routine """

    def __init__(self, iqfile, mode, filelist):
        super(PlotIQ, self).__init__()
        self.iqfile = iqfile
        self.plot_mode = mode
        self.filelist = filelist

    def run(self):
        plt.rcParams.update({'figure.max_open_warning': 0})
        if self.plot_mode == 1:
            for wavfiles in self.filelist:
                self.plotspectrogram(wavfiles)
            images = [Image.open(x) for x in glob.glob("*.png")]
            finalname = 'TDoA_' + str(wavfiles.rsplit("_", 3)[1]) + '_temp.pdf'
            self.pil_grid(images, finalname, 3)  # last parameter = the number of images displayed horizontally
            for imgfiles in glob.glob("*.wav.png"):
                os.remove(imgfiles)
        else:
            self.plotspectrogram(self.iqfile)

    def plotspectrogram(self, source):
        global gps_status
        old_f = open(source, 'rb')
        new_f = open(source + '.nogps', 'wb')
        old_size = os.path.getsize(source)
        data_size = 2048 * ((old_size - 36) // 2074)
        new_f = BytesIO()
        new_f.write(old_f.read(36))
        new_f.write(b'data')
        new_f.write(struct.pack('<i', data_size))
        for i in range(62, old_size, 2074):
            old_f.seek(i)
            new_f.write(old_f.read(2048))
        old_f.close()
        new_f.seek(0, 0)
        data = np.frombuffer(new_f.getvalue(), dtype='int16')
        data = data[0::2] + 1j * data[1::2]
        fig, ax = plt.subplots()
        plt.specgram(data, NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)), noverlap=512, vmin=10,
                     vmax=200, cmap=COLORMAP)
        gps_status = self.has_gps(source)
        plt.title(source.rsplit("_", 3)[2] + " - [CF=" + str(
            (float(source.rsplit("_", 3)[1]) / 1000)) + " kHz] - GPS:" + str(gps_status))
        plt.xlabel("time (s)")
        plt.ylabel("frequency offset (kHz)")
        ticks = matplotlib.ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x // 1e3))
        ax.yaxis.set_major_formatter(ticks)
        plt.savefig(source + '.png')
        os.remove(source + '.nogps')
        if self.plot_mode == 0:
            im_temp = Image.open(source + '.png')
            im_temp = im_temp.resize((320, 240), Image.ANTIALIAS)
            img = ImageTk.PhotoImage(im_temp)
            APP.gui.plot_iq_button.configure(image=img)
            APP.gui.plot_iq_button.image = img
            os.remove(source + '.png')

    def pil_grid(self, images, filename, max_horiz=np.iinfo(int).max):
        """ Make a poster of png files. """
        n_images = len(images)
        n_horiz = min(n_images, max_horiz)
        h_sizes, v_sizes = [0] * n_horiz, [0] * ((n_images // n_horiz) + (1 if n_images % n_horiz > 0 else 0))
        for i, im in enumerate(images):
            h, v = i % n_horiz, i // n_horiz
            h_sizes[h] = max(h_sizes[h], im.size[0])
            v_sizes[v] = max(v_sizes[v], im.size[1])
        h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
        im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
        for i, im in enumerate(images):
            im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
        im_grid.save(filename, resolution=153.5)  # adjust res to ~900x600
        return im_grid

    def has_gps(self, source):
        """ Detect if IQ file has GPS GNSS data (in test). """
        gpslast = 0
        f_wav = open(source, 'rb')
        for i in range(2118, os.path.getsize(source), 2074):
            f_wav.seek(i)
            if sys.version_info[0] < 3:
                gpslast = max(gpslast, ord(f_wav.read(1)[0]))
            else:
                gpslast = max(gpslast, f_wav.read(1)[0])
        return 0 < gpslast < 254


class OctaveProcessing(threading.Thread):
    """ Octave processing routine """

    def __init__(self, input_file, tdoa_rootdir, log_file):
        super(OctaveProcessing, self).__init__()
        self.m_file_to_process = input_file
        self.tdoa_rootdir = tdoa_rootdir
        self.log_file = log_file

    def run(self):
        global PROC_PID  # stdout
        octave_errors = [b'index-out-of-bounds', b'< 2 good stations found', b'Octave:nonconformant - args',
                         b'n_stn=2 is not supported', b'resample.m: p and q must be positive integers',
                         b'Octave:invalid-index', b'incomplete \'data\' chunk']
        if sys.version_info[0] == 2:
            tdoa_filename = self.m_file_to_process
            proc = subprocess.Popen(['octave-cli', tdoa_filename], cwd=self.tdoa_rootdir, stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE, shell=False)
        else:
            tdoa_filename = self.m_file_to_process.replace(".m", "")
            proc = subprocess.Popen(['octave-cli', '--eval', tdoa_filename], cwd=self.tdoa_rootdir,
                                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=False)
        PROC_PID = proc.pid
        if PROC_PID:
            APP.gui.writelog("ultimateTDoA process started.")
        logfile = open(self.log_file, 'w')
        if sys.version_info[0] == 2:
            for octave_output in proc.stdout:
                logfile.write(octave_output)
                if any(x in octave_output for x in octave_errors):
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
        APP.gui.writelog("TDoA process error.")
        APP.gui.writelog(self.Returned_error.decode())
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


class FillMapWithNodes(object):
    """ process to display the nodes on the World Map. """

    def __init__(self, parent):
        self.parent = parent

    def run(self):
        """ ultimate interface process to display the nodes on the World Map. """
        global tag_list, node_list, node_file
        tag_list = []
        server_lists = [up(up(up(os.getcwd()))) + os.sep + "directTDoA_server_list.db",
                        up(up(up(os.getcwd()))) + os.sep + "directTDoA_static_server_list.db"]
        node_list = []
        node_file = []
        for wavfiles in glob.glob(os.getcwd() + os.sep + "*.wav"):
            tdoa_id = re.search(r'(.*)_(.*)_iq.wav', wavfiles)
            node_list.append(tdoa_id.group(2))
            node_file.append(wavfiles)
        for server_list in server_lists:
            with open(server_list) as node_db:
                db_data = json.load(node_db)
                for node_index in range(len(db_data)):
                    if db_data[node_index]["id"].replace("/", "") in node_list:
                        # Change icon color of fav, black and standards nodes and apply a gradiant // SNR
                        perc = (int(db_data[node_index]["snr"]) - 30) * GRAD
                        if db_data[node_index]["mac"] in WHITELIST:
                            node_color = (self.color_variant(FAVCOLOR, perc))
                        elif db_data[node_index]["mac"] in BLACKLIST:
                            node_color = (self.color_variant(BLKCOLOR, perc))
                        else:
                            node_color = (self.color_variant(STDCOLOR, perc))
                        self.add_point(node_index, node_color, db_data)
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
            print("OOPS - Error in adding the point to the map")

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

    def node_selection_inactive(self, node_mac):
        """ Removing additionnal highlight on selected node icon. """
        for node_tag_item in tag_list:
            if node_mac in node_tag_item:
                self.parent.canvas.delete(node_tag_item + "$#")

    def node_selection_inactiveall(self):
        """ Removing ALL additionnal highlights on selected nodes icons. """
        for node_tag_item in tag_list:
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
        self.canvas.scan_dragto(-int(DX0.split('.')[0]), -int(DY0.split('.')[0]), gain=1)
        self.show_image()
        time.sleep(0.2)
        FillMapWithNodes(self).run()
        for mfile in glob.glob(os.getcwd() + os.sep + "proc*.empty"):
            f = open(mfile, 'r')
            filedata = f.read()
            f.close()
            lat = re.search(r"lat_range', \[([-]?[0-9]{1,2}(\.[0-9]*)?) ?([-]?[0-9]{1,2}(\.[0-9]*|))?\]", filedata)
            lon = re.search(r"lon_range', \[([-]?[0-9]{1,3}(\.[0-9]*)?) ?([-]?[0-9]{1,3}(\.[0-9]*|))?\]", filedata)
            lat_min_map = lat.group(1)
            lat_max_map = lat.group(3)
            lon_min_map = lon.group(1)
            lon_max_map = lon.group(3)
            place_regexp_coords = re.search(r"('known_location', struct\('coord', \[([-]?[0-9]{1,2}(\.[0-9]*)?|0) ?([-]?[0-9]{1,3}(\.[0-9]*)?|0)\],)", filedata)
            selectedlat = place_regexp_coords.group(2)
            selectedlon = place_regexp_coords.group(4)
            place_regexp_name = re.search(r"('name',\s '(.+)'\),)", filedata)
            selectedcity = place_regexp_name.group(2)
            self.canvas.create_rectangle(self.convert_lon(lon_min_map), self.convert_lat(lat_max_map),
                                         self.convert_lon(lon_max_map), self.convert_lat(lat_min_map), outline='red',
                                         tag="mappreset")
            self.create_known_point(selectedlat, selectedlon, selectedcity)

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
                try:
                    APP.gui.label4.configure(text="[LAT] range: " + str(lat_min_map) + "° " + str(
                        lat_max_map) + "°  [LON] range: " + str(lon_min_map) + "° " + str(lon_max_map) + "°")
                except NameError:
                    pass
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
                                     tag=selectedcity.rsplit(' (')[0])
        self.canvas.create_text(xx0, yy0 - 10, text=selectedcity.rsplit(' (')[0].replace("_", " "), justify='center',
                                fill=POICOLOR, tag=selectedcity.rsplit(' (')[0])

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
        global HOST, node_file, node_list, gps_status
        HOST = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        menu = Menu(self, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')
        # menu2 = Menu(menu, tearoff=0, fg="black", bg=BGC, font='TkFixedFont 7')  # demodulation menu
        # mykeys = ['mac', 'url', 'id', 'snr', 'lat', 'lon']
        # n_field    0      1      2     3      4      5
        n_field = HOST.rsplit("$", 6)
        # Color gradiant proportionnal to SNR value
        snr_gradiant = (int(n_field[3]) - 30) * GRAD
        if n_field[0] in WHITELIST:
            nodecolor = FAVCOLOR
        else:
            nodecolor = STDCOLOR
        # Dynamic foreground (adapting font to white or black depending on luminosity)
        dfg = self.get_font_color((self.color_variant("#FFFF00", snr_gradiant)))
        # Colorized background (depending on Favorite node or not)
        cbg = self.color_variant(nodecolor, snr_gradiant)
        # Get spectrogram of the node recorded IQ file
        PlotIQ(node_file[node_list.index(n_field[2].replace("/", ""))], 0, 1).run()
        matches = [el for el in fulllist if n_field[0] in el]
        if gps_status:
            if len(matches) != 1:
                menu.add_command(label="Add " + n_field[2] + " for TDoA process", background=cbg, foreground=dfg,
                                 font="TkFixedFont 7 bold", command=lambda *args: self.populate("add", n_field))
            elif len(matches) == 1:
                menu.add_command(label="Remove " + n_field[2] + " from TDoA process", background=cbg, foreground=dfg,
                                 font="TkFixedFont 7 bold", command=lambda: self.populate("del", n_field))
        else:
            menu.add_command(label=n_field[2] + " is not usable for this run (no recent GPS timestamps in the IQ)",
                             background="red", foreground=dfg, font="TkFixedFont 7 bold", command=None)
        menu.add_command(label="SNR: " + n_field[3] + " dB", state=NORMAL, background=cbg, foreground=dfg, command=None)
        menu.post(event.x_root, event.y_root)  # popup placement // node icon

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

    def populate(self, action, sel_node_tag):
        """ TDoA listing node populate/depopulate process. """
        if action == "add":
            if len(fulllist) < 6:
                fulllist.append(
                    sel_node_tag[1].rsplit(':')[0] + "$" + sel_node_tag[1].rsplit(':')[1] + "$" + sel_node_tag[
                        0] + "$" + sel_node_tag[2].replace("/", ""))
                FillMapWithNodes(self).node_sel_active(sel_node_tag[0])
            else:
                tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="6 nodes Maximum !")
        elif action == "del":
            fulllist.remove(
                sel_node_tag[1].rsplit(':')[0] + "$" + sel_node_tag[1].rsplit(':')[1] + "$" + sel_node_tag[0] + "$" +
                sel_node_tag[2].replace("/", ""))
            FillMapWithNodes(self).node_selection_inactive(sel_node_tag[0])
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
        global image_scale, node_file
        global map_preset, tdoa_in_progress, open_pdf
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
        # bgc = '#d9d9d9'  # GUI background color
        # fgc = '#000000'  # GUI foreground color
        dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        image_scale = 1
        # selectedlat = ""
        # selectedlon = ""
        # selectedcity = ""
        map_preset = 0
        tdoa_in_progress = 0
        open_pdf = IntVar(self, value=1)
        # Control panel background
        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.64, relheight=0.4, relwidth=1)
        self.label0.configure(bg=BGC, fg=FGC, width=214)

        # Map boundaries information text
        self.label4 = Label(parent)
        self.label4.place(relx=0.005, rely=0.895, height=21, relwidth=0.55)
        self.label4.configure(bg=BGC, font="TkFixedFont", fg=FGC, width=214, text="", anchor="w")

        # Compute button
        self.compute_button = Button(parent)
        self.compute_button.place(relx=0.61, rely=0.65, height=64, relwidth=0.115)
        self.compute_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg='#d9d9d9',
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Compute",
                                      command=self.start_stop_tdoa)

        # Purge node listing button
        self.purge_button = Button(parent)
        self.purge_button.place(relx=0.61, rely=0.75, height=24, relwidth=0.115)
        self.purge_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="orange",
                                    disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                    highlightcolor="#000000", pady="0", text="Purge Nodes", command=self.purgenode,
                                    state="normal")

        # Trim_iq button
        self.trim_iq_button = Button(parent)
        self.trim_iq_button.place(relx=0.61, rely=0.80, height=24, relwidth=0.115)
        self.trim_iq_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="lightblue",
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Run trim_iq.py",
                                      command=TrimIQ(os.getcwd()).start, state="normal")

        # Restart button
        self.restart_button = Button(parent)
        self.restart_button.place(relx=0.61, rely=0.85, height=24, relwidth=0.115)
        self.restart_button.configure(activebackground="#d9d9d9", activeforeground="#000000", bg="red",
                                      disabledforeground=dfgc, fg="#000000", highlightbackground="#d9d9d9",
                                      highlightcolor="#000000", pady="0", text="Restart GUI", command=Restart().run,
                                      state="normal")

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
        self.console_window.place(relx=0.005, rely=0.65, relheight=0.23, relwidth=0.6)
        self.console_window.configure(bg=CONS_B, font="TkTextFont", fg=CONS_F, highlightbackground=BGC,
                                      highlightcolor=FGC, insertbackground=FGC, selectbackground="#c4c4c4",
                                      selectforeground=FGC, undo="1", width=970, wrap="word")

        # Auto open TDoA PDF result file
        self.open_pdf_checkbox = Checkbutton(parent)
        self.open_pdf_checkbox.place(relx=0.62, rely=0.9, height=21, relwidth=0.11)
        self.open_pdf_checkbox.configure(bg=BGC, fg=FGC, activebackground=BGC, activeforeground=FGC,
                                         font="TkFixedFont 8", width=214, selectcolor=BGC, text="auto-open result",
                                         anchor="w", variable=open_pdf, command=None)

        # plot IQ preview
        self.plot_iq_button = Button(parent)
        self.plot_iq_button.place(relx=0.73, rely=0.65, height=240, width=320)
        self.plot_iq_button.configure(command=None, state="normal")

        # Adding some texts to console window at program start
        self.writelog("This is " + VERSION + ", a GUI written for python 2/3 with Tk")
        self.writelog(str(len(node_file)) + " nodes are available for this run.")

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
        sm8.add_command(label="yes", command=lambda *args: self.tdoa_settings(0))
        sm8.add_command(label="no", command=lambda *args: self.tdoa_settings(1))
        menu_3.add_cascade(label='use_constraints', menu=sm9, underline=0)
        sm9.add_command(label="yes", command=lambda *args: self.tdoa_settings(2))
        sm9.add_command(label="no", command=lambda *args: self.tdoa_settings(3))
        menu_3.add_cascade(label='tdoa calculation mode', menu=sm10, underline=0)
        sm10.add_command(label="standard", command=lambda *args: self.tdoa_settings(4))
        sm10.add_command(label="new (2020)", command=lambda *args: self.tdoa_settings(5))

        # Various GUI binds
        self.listbox_update(my_info1)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.choice.bind('<FocusIn>', self.resetcity)
        self.choice.bind('<KeyRelease>', self.on_keyrelease)

        try:
            self.label4.configure(text="[LAT] range: " + str(lat_min_map) + "° " + str(
                lat_max_map) + "°  [LON] range: " + str(lon_min_map) + "° " + str(lon_max_map) + "°")
        except NameError:
            pass

    def mapbox_style(self, value):
        global MAP_BOX
        self.writelog("OPTION: Mapbox output style set to " + value)
        MAP_BOX = value

    def tdoa_settings(self, value):
        global plot_kiwi_json_new, use_constraints_new, algo_new
        if value == 0:
            self.writelog("OPTION: plot_kiwi_json set to YES")
            plot_kiwi_json_new = "true"
        if value == 1:
            self.writelog("OPTION: plot_kiwi_json set to NO")
            plot_kiwi_json_new = "false"
        if value == 2:
            self.writelog("OPTION: use_constraints set to YES")
            use_constraints_new = "true"
        if value == 3:
            self.writelog("OPTION: use_constraints set to NO")
            use_constraints_new = "false"
        if value == 4:
            self.writelog("OPTION: former TDoA algorithm selected")
            algo_new = "false"
        if value == 5:
            self.writelog("OPTION: new TDoA algorithm selected")
            self.writelog("OPTION: use_constraints automaticaly set to NO")
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
            self.label4.configure(
                text="[LAT] range: " + str(lat_min_map) + "° " + str(lat_max_map) + "°  [LON] range: " + str(
                    lon_min_map) + "° " + str(lon_max_map) + "°")
        else:
            self.writelog("ERROR : The boundaries selection is forbidden unless map un-zoomed.")

    def redraw(self):
        self.member1.redraw_map_cmd()

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
                tkMessageBox.showinfo(title="  ¯\\_(ツ)_/¯", message="Type something in the left box first !")
            else:
                self.label3.configure(text="LAT: " + str(
                    my_info2[my_info1.index(event.widget.get(event.widget.curselection()))]) + " LON: " + str(
                        my_info3[my_info1.index(event.widget.get(event.widget.curselection()))]))
                selectedlat = str(my_info2[my_info1.index(event.widget.get(event.widget.curselection()))])
                selectedlon = str(my_info3[my_info1.index(event.widget.get(event.widget.curselection()))])
                selectedcity = event.widget.get(event.widget.curselection())
                self.member1.create_known_point(selectedlat, selectedlon, selectedcity)
        except:
            pass

    def resetcity(self, event):
        """ Erase previous known location choice from both textbox input and World map icon and name. """
        global selectedcity, selectedlat, selectedlon
        self.choice.delete(0, 'end')
        self.label3.configure(text="")
        if selectedcity:
            self.member1.delete_point(selectedcity)
            selectedcity = " "
            selectedlat = "0"
            selectedlon = "0"

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
        APP.title(VERSION)
        self.member1.unselect_allpoint()
        self.writelog("ultimateTDoA node listing has been cleared.")

    def start_stop_tdoa(self):
        """ Actions to perform when Compute button is clicked. """
        global tdoa_in_progress
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
                    set_plot_kiwi = re.search(r"(\s{16}'plot_kiwi_json', (.+),)", file_d)
                    plot_kiwi_json_origin = set_plot_kiwi.group(2)
                    set_usec = re.search(r"(\s{16}'use_constraints', (.+),)", file_d)
                    use_constraints_origin = set_usec.group(2)
                    set_algo = re.search(r"(\s{16}'new', (.+))", file_d)
                    algo_origin = set_algo.group(2)
                    # Fill the .m file with selected node listing
                    i = 1
                    for node in fulllist:
                        new_nodes.append("    input(" + str(i) + ").fn    = fullfile('iq', '" + os.path.basename(
                            os.path.dirname(mfile)) + "', '" + os.path.basename(
                            "".join(node_file[node_list.index(node.rsplit("$", 3)[3])].split(os.sep, 1)[1:])) + "\');")
                        file_list.append(node_file[node_list.index(node.rsplit("$", 3)[3])])
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
                                             'name',  '""" + selectedcity.rsplit(' (')[0] + """'),
                    'dir', 'png',
                    'plot_kiwi', false,
                    'plot_kiwi_json', """ + pkjn + """,
                    'use_constraints', """ + uc + """,
                    'new', """ + al + """
                   );"""
                    new_mapbox = "lon, \" " + selectedlat + "\", \" " + selectedlon + "\", \" " + MAP_BOX + " \", \"iq"
                    # replace old config block by the new one
                    file_d = re.sub('(\n    config = struct(.*)(\n(.*)){9})', new_config, file_d, flags=re.M)
                    file_d = re.sub(r'lon(.*)iq', new_mapbox, file_d)
                    file_d = file_d.replace("spec.pdf", "temp.pdf")
                    # get some file names and directory
                    logfile = os.path.basename(mfile).replace("empty", "txt")
                    tdoa_rootdir = up(up(up(mfile)))
                    newfile = tdoa_rootdir + os.sep + os.path.basename(mfile).replace("empty", "m")
                    # create the new proc_tdoa file
                    f = open(newfile, 'w')
                    f.write(file_d)
                    f.close()
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
    global PROC_PID
    try:  # to kill octave
        os.kill(PROC_PID, signal.SIGTERM)
    except (NameError, OSError):
        pass
    os.kill(os.getpid(), signal.SIGTERM)
    APP.destroy()


if __name__ == '__main__':
    APP = MainW()
    APP.title(VERSION)
    APP.protocol("WM_DELETE_WINDOW", on_closing)
    APP.mainloop()
