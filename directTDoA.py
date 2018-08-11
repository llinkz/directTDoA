#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
import tkSimpleDialog
import threading, os, signal, subprocess, platform, tkMessageBox, time, re, glob, webbrowser, json, requests
from subprocess import PIPE
from PIL import Image, ImageTk
from shutil import copyfile
from tkColorChooser import askcolor

VERSION = "directTDoA v2.71 by linkz"


class Restart:
    def __init__(self):
        pass

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


class ReadKnownPointFile:
    def __init__(self):
        pass

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
    def __init__(self, parent=None):
        super(CheckFileSize, self).__init__()
        self.parent = parent

    def run(self):
        global t, checkfilesize
        checkfilesize = 1
        while t == 0:
            time.sleep(0.5)  # file size refresh time
            if platform.system() == "Windows":
                for wavfiles in glob.glob("TDoA\\iq\\*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("TDoA\\iq\\", "")
                    self.parent.writelog2(str(filename) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0
            if platform.system() == "Linux" or platform.system() == "Darwin":
                for wavfiles in glob.glob("./TDoA/iq/*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("./TDoA/iq/", "")
                    self.parent.writelog2(str(filename) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0


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
        if platform.system() == "Windows":
            copyfile("TDoA\\pdf\\TDoA_" + varfile + ".pdf",
                     "TDoA\\iq\\" + starttime + "_F" + str(frequency) + "\\TDoA_" + varfile + ".pdf")
            with open("./TDoA/iq/" + starttime + "_F" + str(
                    frequency) + "/TDoA_" + varfile + "_found " + llat + sign1 + " " + llon + sign2, 'w') as tdoa_file:
                tdoa_file.write('')

        if platform.system() == "Linux" or platform.system() == "Darwin":
            copyfile("./TDoA/pdf/TDoA_" + varfile + ".pdf",
                     "./TDoA/iq/" + starttime + "_F" + str(frequency) + "/TDoA_" + varfile + ".pdf")
            with open("./TDoA/iq/" + starttime + "_F" + str(
                    frequency) + "/TDoA_" + varfile + "_found " + llat + sign1 + " " + llon + sign2, 'w') as tdoa_file:
                tdoa_file.write('')

        # last popup window shown at end of process
        finish = tkMessageBox.askyesno(title="TDoA process just finished.",
                                       message="Most likely location coords are " + llat + "°" + sign1 + " " + llon + "°" + sign2 + "\n\nClick Yes to open \"Geohack\" webpage centered on most likely point found by the process\nClick No to open files directory and restart GUI")
        if finish:  # opens a web browser with geohack url containing most likely point coordinates & restart GUI
            webbrowser.open_new("https://tools.wmflabs.org/geohack/geohack.php?params=" + latstring + "_" + lonstring)
        elif finish is False:  # opens directory that containing TDoA files & restart GUI
            webbrowser.open("./TDoA/iq/" + starttime + "_F" + str(frequency))
        Restart().run()


class ReadConfigFile:

    def __init__(self):
        pass

    def read_cfg(self):
        global dx0, dy0, dx1, dy1, dmap, mapfl, gpsfl, white, black, colorline
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]  # longitude min
            dy0 = configline[1].split(',')[1]  # latitude max
            dx1 = configline[1].split(',')[2]  # longitude max
            dy1 = configline[1].split(',')[3]  # latitude min
            dmap = configline[3].split('\n')[0]  # displayed map
            mapfl = configline[5].replace("\n", "").split(',')[0]  # map filter
            gpsfl = configline[5].replace("\n", "").split(',')[1]  # GPS/min filter
            white = configline[7].replace("\n", "").split(',')  # nodes whitelist
            black = configline[9].replace("\n", "").split(',')  # nodes blacklist
            colorline = configline[11].replace("\n", "").split(',')  # GUI map colors
        c.close()


class SaveConfigFile:
    def __init__(self):
        pass

    def save_cfg(self, field, input):
        global dmap, mapfl, gpsfl, white, black, colorline
        # ReadConfigFile().read_cfg()
        with open('directTDoA.cfg', "w") as u:
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
        u.close()


class RunUpdate(threading.Thread):

    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        try:
            nbnode = 0
            response = requests.get("http://kiwisdr.com/tdoa/files/kiwi.gps.json")
            json_data = json.loads(response.text)
            if os.path.isfile('directTDoA_server_list.db') is True:
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
                os.remove('directTDoA_server_list.db')
            with open('directTDoA_server_list.db', "w") as g:
                g.write("   \n")
                g.write(
                    "['ffffffffffff', 'linkz.ddns.net:8073', '30', 'linkz', '45.4', '5.3', 'directTDoA GUI developer, French Alps', '0', '4']\n")
                for i in range(len(json_data)):
                    g.write("['" + json_data[i]['mac'] + "', '" + str(json_data[i]['h']) + ":" + str(
                        json_data[i]['p']) + "', '" + str(json_data[i]['fm']) + "', '" + json_data[i][
                                'id'] + "', '" + str(json_data[i]['lat']) + "', '" + str(
                        json_data[i]['lon']) + "', '" + str(json_data[i]['n'].encode('ascii', 'ignore')) + "', '" + str(
                        json_data[i]['u']) + "', '" + str(json_data[i]['um']) + "']\n")
                    nbnode += 1
                g.seek(0)
                g.write("%s\n" % str(nbnode + 1))
                g.close()
                Restart().run()
        except:
            print "UPDATE FAIL, can't retrieve json source"


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
        proc = subprocess.Popen([exec_octave, tdoa_filename], cwd='./TDoA/', stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, shell=False, preexec_fn=os.setsid)
        proc_pid = proc.pid
        logfile = open("./TDoA/iq/" + starttime + "_F" + str(frequency) + "/TDoA_" + varfile + "_log.txt", 'w')
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
    def __init__(self, parent=None):
        super(SnrProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global proc3, snrfreq
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux" or platform.system() == "Darwin":
            execname = 'python2'
        proc3 = subprocess.Popen(
            [execname, 'microkiwi_waterfall.py', '--file=wf.bin', '-z', '8', '-o', str(snrfreq), '-s', str(snrhost)],
            stdout=PIPE, shell=False)
        while True:
            line3 = proc3.stdout.readline()
            if "bytes" in line3:
                print line3.rstrip()
                os.kill(proc3.pid)
                pass


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
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux" or platform.system() == "Darwin":
            execname = 'python2'
        proc2 = subprocess.Popen(
            [execname, 'kiwirecorder.py', '-s', str(hostlisting), '-p', str(portlisting), str(namelisting), '-f',
             str(frequency), '-L', str(0 - lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False,
            preexec_fn=os.setsid)
        proc2_pid = proc2.pid
        self.parent.writelog("IQ recording in progress...please wait")
        # self.parent.writelog(   # debug
        #     execname + ' kiwirecorder.py -s ' + str(hostlisting) + ' -p ' + str(portlisting) + ' ' + str(
        #         namelisting) + ' -f ' + str(frequency) + ' -L ' + str(0 - lpcut) + ' -H ' + str(hpcut) + ' -m iq -w')


class FillMapWithNodes(threading.Thread):

    def __init__(self, parent=None):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
        global manual_bound_x, manual_bound_y, manual_bound_xsize, manual_bound_ysize, map_preset, map_manual
        global my_short, my_name, my_user, my_usermx, my_fm
        if os.path.isfile('directTDoA_server_list.db') is True:
            with open('directTDoA_server_list.db') as h:
                global my_x_zeros, my_y_zeros, my_x_ones, my_y_ones, mycolor, my_host, my_tag
                i = 1
                lines = h.readlines()
                nbgpsnodes = lines[0]
                my_tag = []
                my_host = []
                my_fm = []
                my_short = []
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
                    my_fm.append(id.group(3))
                    my_short.append(id.group(4))
                    my_lat.append(id.group(5))
                    my_lon.append(id.group(6))
                    my_name.append(id.group(7).replace(" ", "_"))
                    my_user.append(id.group(8))
                    my_usermx.append(id.group(9))
                    i += 1
            h.close()
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
                    if my_tag[n] in white:    # favorite node color
                        mycolor.append(self.color_variant(colorline[1], int(self.gpsfix2color(my_fm[n]))))
                    elif my_tag[n] in black:  # blacklist node color
                        mycolor.append(self.color_variant(colorline[2], int(self.gpsfix2color(my_fm[n]))))
                    else:                     # standard node color
                        mycolor.append(self.color_variant(colorline[0], int(self.gpsfix2color(my_fm[n]))))
                else:
                    mycolor.append('red')  # if no slots available, map point is always created red
                n += 1

            m = 0
            while m < len(my_tag):
                if mapfl == "1" and my_tag[m] not in black:
                    self.add_point(m)
                elif mapfl == "2" and my_tag[m] in white:
                    self.add_point(m)
                elif mapfl == "3" and my_tag[m] in black:
                    self.add_point(m)
                elif mapfl == "0":
                    self.add_point(m)
                m += 1
            try:
                if manual_bound_x and map_preset == 0:
                    self.parent.canvas.create_rectangle(manual_bound_x, manual_bound_y, manual_bound_xsize,
                                                        manual_bound_ysize, outline='red', tag="mapmanual")
            except:
                pass
            self.parent.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map pos.
            self.parent.show_image()

    def color_variant(self, hex_color, brightness_offset=1):
        # source : https://chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html
        if len(hex_color) != 7:
            raise Exception("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join([self.int2hex(i) for i in new_rgb_int])

    def gpsfix2color(self, a):
        colorscaled = float(float(a) - 30) / float(30)
        return colorscaled * 255

    def int2hex(self, x):
        val = hex(x)[2:]
        val = "0" + val if len(val) < 2 else val
        return val

    def add_point(self, m):
        global gpsfl
        if int(my_fm[m]) >= int(gpsfl):  # GPS/min filter
            self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m],
                                                fill=mycolor[m], outline="black", activefill='white',
                                                tag=str(
                                                    my_host[m] + "$" + my_tag[m] + "$" + my_short[m] + "$" +
                                                    my_name[m] + "$" + my_user[m] + "$" + my_usermx[
                                                        m] + "$" + my_fm[m]))
            self.parent.canvas.tag_bind(str(
                my_host[m] + "$" + my_tag[m] + "$" + my_short[m] + "$" + my_name[m] + "$" + my_user[m] + "$" +
                my_usermx[m] + "$" + my_fm[m]), "<Button-1>", self.parent.onClick)
        else:
            pass

    def deletePoint(self, n):  # city/site map point deletion process
        self.parent.canvas.delete(self.parent, n.rsplit(' (')[0])


class ZoomAdvanced(Frame):  # src stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 :)
    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        parent.geometry("1200x700+150+10")
        global dx0, dy0, dx1, dy1
        global serverlist, portlist, namelist, shortlist, dmap, host, white, black, mapfl, mapboundaries_set
        # host = Variable
        serverlist = []
        portlist = []
        namelist = []
        shortlist = []
        ReadConfigFile().read_cfg()
        mapboundaries_set = None
        self.x = self.y = 0
        # Create canvas and put image on it
        self.canvas = Canvas(self.master, highlightthickness=0)
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
        # self.canvas.bind_all('<MouseWheel>', self.wheel)  # Windows Zoom disabled in this version !
        # self.canvas.bind('<Button-5>', self.wheel)  # Linux Zoom disabled in this version !
        # self.canvas.bind('<Button-4>', self.wheel)  # Linux Zoom disabled in this version !
        self.canvas.bind("<ButtonPress-3>", self.on_button_press)  # red rectangle selection
        self.canvas.bind("<B3-Motion>", self.on_move_press)  # red rectangle selection
        self.canvas.bind("<ButtonRelease-3>", self.on_button_release)  # red rectangle selection
        self.image = Image.open(dmap)
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the image
        self.delta = 2.0  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.rect = None
        self.start_x = None
        self.start_y = None
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
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # create rectangle if not yet exist
        if not self.rect:
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
        if map_preset == 1 and map_manual == 0:
            pass
        else:
            tkMessageBox.showinfo("TDoA map Geographical boundaries set",
                              message="LATITUDE RANGE: from " + str(lat_min_map) + "° to " + str(lat_max_map) + "°\nLONGITUDE RANGE: from " + str(lon_min_map) + "° to " + str(lon_max_map) + "°")
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
        global snrcheck, snrhost, host, white, black
        # x1, x2, y1, y2, o, full_list, snrcheck, snrhost, host
        host = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        self.menu = Menu(self, tearoff=0, fg="black", bg="gray", font='TkFixedFont 7')
        #  host.rsplit("$", 6)[0]  host
        #  host.rsplit("$", 6)[1]  id
        #  host.rsplit("$", 6)[2]  short name
        #  host.rsplit("$", 6)[3]  name
        #  host.rsplit("$", 6)[4]  users
        #  host.rsplit("$", 6)[5]  users max
        #  host.rsplit("$", 6)[6]  GPS fixes per minute
        if int(host.rsplit("$", 6)[4]) / int(host.rsplit("$", 6)[5]) == 0:
            self.menu.add_command(
                label="Use: " + str(host).rsplit("$", 6)[2] + " [" + host.rsplit("$", 6)[6] + " GPS fix/min] [" + str(
                    host.rsplit("$", 6)[4]) + "/" + str(host.rsplit("$", 6)[5]) + " users] for TdoA process",
                command=self.populate)
            try:
                self.menu.add_command(
                    label="Open \"" + str(host).rsplit("$", 6)[0] + "/f=" + str(frequency.get()) + "iqz8\" in browser",
                    command=self.openinbrowser)
            except ValueError:
                pass
        else:
            self.menu.add_command(
                label="Use: " + str(host).rsplit("$", 6)[2] + " [" + host.rsplit("$", 6)[6] + " GPS fix/min] [" + str(
                    host.rsplit("$", 6)[4]) + "/" + str(host.rsplit("$", 6)[5]) + " users] for TdoA process",
                state=DISABLED, command=None)
            try:
                self.menu.add_command(
                    label="Open \"" + str(host.rsplit("$", 6)[0]) + "/f=" + str(frequency.get()) + "iqz8\" in browser",
                    state=DISABLED, command=None)
            except ValueError:
                pass
        self.menu.add_command(label=str(host.rsplit("$", 6)[3]).replace("_", " "), state=DISABLED, font='TkFixedFont 7',

                              command=None)  # showing the node full name as "comment"
        self.menu.add_separator()
        if host.rsplit('$', 6)[1] in white:  # if node is a favorite
            self.menu.add_command(label="remove from favorites", command=self.remfavorite)
        elif host.rsplit('$', 6)[1] not in black:
            self.menu.add_command(label="add to favorites", command=self.addfavorite)
        if host.rsplit('$', 6)[1] in black:  # if node is blacklisted
            self.menu.add_command(label="remove from blacklist", command=self.remblacklist)
        elif host.rsplit('$', 6)[1] not in white:
            self.menu.add_command(label="add to blacklist", command=self.addblacklist)

        # self.menu.add_command(label="check SNR", state=DISABLED, command=self.displaySNR)  # for next devel
        # if snrcheck == True:
        #     print "SNR requested on " + str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     print snrfreq
        #     snrhost = str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     SnrProcessing(self).start()
        #     app.title("Checking SNR for" + str(snrhost) + ". Please wait")

        self.menu.post(event.x_root, event.y_root)

    def addfavorite(self):
        global white, black
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 6)[1] in white:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already in the favorite list !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                    mapfl, gpsfl))
                if white[0] == "":
                    u.write("# Whitelist \n%s\n" % host.rsplit('$', 6)[1])
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                else:
                    white.append(host.rsplit('$', 6)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the favorite list !")
            Restart().run()

    def remfavorite(self):
        global white, black, newwhite
        newwhite = []
        ReadConfigFile().read_cfg()
        for f in white:
            if f != host.rsplit('$', 6)[1]:
                newwhite.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                mapfl, gpsfl))
            u.write("# Whitelist \n%s\n" % ','.join(newwhite))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the favorites list !")
        Restart().run()

    def addblacklist(self):
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 6)[1] in black:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already blacklisted !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                    mapfl, gpsfl))
                if black[0] == "":
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % host.rsplit('$', 6)[1])
                else:
                    black.append(host.rsplit('$', 6)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the blacklist !")
            Restart().run()

    def remblacklist(self):
        global white, black, newblack
        newblack = []
        ReadConfigFile().read_cfg()
        for f in black:
            if f != host.rsplit('$', 6)[1]:
                newblack.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % dmap)
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted , GPS/min) \n%s,%s\n" % (
                mapfl, gpsfl))
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(newblack))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the blacklist !")
        Restart().run()

    def openinbrowser(self):
        if frequency.get() != 10000:
            url = "http://" + str(host).rsplit("$", 6)[0] + "/?f=" + str(frequency.get()) + "iqz8"
            webbrowser.open_new(url)
        else:
            url = "http://" + str(host).rsplit("$", 6)[0]
            webbrowser.open_new(url)

    def populate(self):
        global full_list, serverlist, portlist, namelist, shortlist
        if len(serverlist) < 6:
            if host.rsplit(':')[0] not in serverlist:
                serverlist.append(host.rsplit(':')[0])  # host
                portlist.append(host.rsplit(':')[1].rsplit('$')[0])  # port
                namelist.append(host.rsplit('$')[1])  # id
                shortlist.append(host.rsplit('$')[2])  # short name
                app.title(VERSION + " - Selected nodes : " + str(shortlist).replace("[", "").replace("'", "").replace("]", "").replace(",", " +"))
                full_list = str(serverlist).replace("[", "").replace("'", "").replace("]", "").replace(",", " +")
            else:
                tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                      message=str(host.rsplit(':')[0]) + " is already in the server list !")
        else:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message="[[[maximum server limit reached]]]")

    def scroll_y(self, *args, **kwargs):
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
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
            if int(i * self.imscale) < 600:
                return  # block zoom if image is less than 600 pixels
            self.imscale /= self.delta
            scale /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
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
        self.canvas.configure(scrollregion=bbox)  # set scroll region
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
        self.member1 = ZoomAdvanced(parent)
        if os.path.isfile('directTDoA_server_list.db') is not True:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ", message="oops no node db found, Click OK to run an update now")
            RunUpdate().run()
        ReadKnownPointFile().run()
        global frequency, checkfilesize
        global line, i, bgc, fgc, dfgc, lpcut, hpcut
        global latmin, latmax, lonmin, lonmax, bbox1, lat_min_map, lat_max_map, lon_min_map, lon_max_map
        global selectedlat, selectedlon, selectedcity, map_preset, map_manual
        frequency = DoubleVar(self, 10000.0)
        #frequency.set("10000.0")  # default frequency
        bgc = '#d9d9d9'  # GUI background color
        fgc = '#000000'  # GUI foreground color
        dfgc = '#a3a3a3'  # GUI (disabled) foreground color
        lpcut = 5000  # default low pass filter
        hpcut = 5000  # default high pass filter
        lat_min_map = ""
        lat_max_map = ""
        lon_min_map = ""
        lon_max_map = ""
        selectedlat = ""
        selectedlon = ""
        selectedcity = ""
        map_preset = 0
        map_manual = 0
        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.69, relheight=0.4, relwidth=1)
        self.label0.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="")

        numeric_entry_only = (self.register(self.numeric_only), '%S')
        self.Entry1 = Entry(parent, textvariable=frequency, validate='key', vcmd=numeric_entry_only)  # frequency box
        self.Entry1.place(relx=0.06, rely=0.892, height=24, relwidth=0.1)
        self.Entry1.configure(background="white", disabledforeground=dfgc, font="TkFixedFont", foreground=fgc,
                              insertbackground=fgc, width=214)
        self.Entry1.bind('<FocusIn>', self.clickfreq)
        #self.Entry1.bind('<Leave>', self.choosedfreq)
        self.Entry1.bind('<KeyPress>', self.choosedfreq)

        self.label1 = Label(parent)
        self.label1.place(relx=0.01, rely=0.895)
        self.label1.configure(background=bgc, font="TkFixedFont", foreground=fgc, text="Freq:")
        self.label2 = Label(parent)
        self.label2.place(relx=0.162, rely=0.895)
        self.label2.configure(background=bgc, font="TkFixedFont", foreground=fgc, text="kHz")

        self.Button1 = Button(parent)  # Start recording button
        self.Button1.place(relx=0.77, rely=0.89, height=24, relwidth=0.10)
        self.Button1.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start recording", command=self.clickstart, state="normal")

        self.Button2 = Button(parent)  # Stop button
        self.Button2.place(relx=0.88, rely=0.89, height=24, relwidth=0.1)
        self.Button2.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start TDoA proc", command=self.clickstop, state="disabled")

        #  2nd part of buttons
        self.Choice = Entry(parent)
        self.Choice.place(relx=0.01, rely=0.95, height=21, relwidth=0.18)
        self.Choice.insert(0, "TDoA map city/site search here")
        self.ListBox = Listbox(parent)
        self.ListBox.place(relx=0.2, rely=0.95, height=21, relwidth=0.3)
        self.label3 = Label(parent)  # Known point
        self.label3.place(relx=0.54, rely=0.95, height=21, relwidth=0.3)
        self.label3.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="", anchor="w")

        self.Button5 = Button(parent)  # Restart GUI button
        self.Button5.place(relx=0.81, rely=0.94, height=24, relwidth=0.08)
        self.Button5.configure(activebackground=bgc, activeforeground=fgc, background="red", disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Restart GUI", command=Restart().run, state="normal")

        self.Button3 = Button(parent)  # Update button
        self.Button3.place(relx=0.90, rely=0.94, height=24, relwidth=0.08)
        self.Button3.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="update map", command=self.runupdate, state="normal")

        self.Text2 = Text(parent)  # Console window
        self.Text2.place(relx=0.005, rely=0.7, relheight=0.18, relwidth=0.6)
        self.Text2.configure(background="black", font="TkTextFont", foreground="red", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")
        self.writelog("This is " + VERSION + " (ounaid@gmail.com), a GUI written for python 2.7 / Tk")
        self.writelog("All credits to Christoph Mayer for his excellent TDoA work : http://hcab14.blogspot.com")
        vsb2 = Scrollbar(parent, orient="vertical", command=self.Text2.yview)  # adding scrollbar to console
        vsb2.place(relx=0.6, rely=0.7, relheight=0.18, relwidth=0.02)
        self.Text2.configure(yscrollcommand=vsb2.set)

        self.Text3 = Text(parent)  # IQ recs file size window
        self.Text3.place(relx=0.624, rely=0.7, relheight=0.18, relwidth=0.37)
        self.Text3.configure(background="white", font="TkTextFont", foreground="black", highlightbackground=bgc,
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
        submenu1.add_command(label="Grayscale (bright)",
                             command=lambda *args: self.setmap('maps/directTDoA_map_grayscale_bright.jpg'))
        submenu1.add_command(label="Grayscale (dark)",
                             command=lambda *args: self.setmap('maps/directTDoA_map_grayscale.jpg'))
        submenu1.add_command(label="Sat",
                             command=lambda *args: self.setmap('maps/directTDoA_map_sat.jpg'))
        submenu1.add_command(label="Snow Cover",
                             command=lambda *args: self.setmap('maps/directTDoA_map_snowcover.jpg'))
        submenu1.add_command(label="NASA Albedo",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_albedo.jpg'))
        submenu1.add_command(label="NASA BlueMarble",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_bluemarble.jpg'))
        submenu1.add_command(label="NASA Topography",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_topo.jpg'))
        submenu1.add_command(label="NASA Topography (grayscale)",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_topo_grayscale.jpg'))
        submenu1.add_command(label="NASA Vegetation",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_vegetation.jpg'))
        submenu1.add_command(label="NASA Vegetation (grayscale)",
                             command=lambda *args: self.setmap('maps/directTDoA_map_NASA_vegetation_grayscale.jpg'))
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

        menubar.add_cascade(label="Map Presets",menu=filemenu2)
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
        filemenu2.add_command(label="World",command=lambda *args: self.map_preset(13))
        # next map boundaries presets come here, keep preset "20" for reset
        #
        #
        filemenu2.add_command(label="--- RESET ---", command=lambda *args: self.map_preset(20))

        menubar.add_cascade(label="IQ bandwidth", menu=filemenu3)
        iqset = ['10000', '9000', '8000', '7000', '6000', '5000', '4000', '3000', '2000', '1000', '900', '800', '700',
                 '600', '500', '400', '300', '200', '100', '50']
        for bw in iqset:
            filemenu3.add_command(label=bw + " Hz", command=lambda bw=bw: self.set_iq(bw))

        menubar.add_cascade(label="?", menu=filemenu4)
        filemenu4.add_command(label="Help", command=self.help)
        filemenu4.add_command(label="About", command=self.about)

        self.listbox_update(my_info1)
        self.ListBox.bind('<<ListboxSelect>>', self.on_select)
        self.Choice.bind('<FocusIn>', self.resetcity)
        self.Choice.bind('<KeyRelease>', self.on_keyrelease)
        self.Entry1.delete(0, 'end')

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
        if event.widget.get(event.widget.curselection()) == " ":
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ", message="Type something in the left box to search for a point")
        else:
            self.label3.configure(text="LAT: " + str(
                my_info2[my_info1.index(event.widget.get(event.widget.curselection()))]) + " LON: " + str(
                my_info3[my_info1.index(event.widget.get(event.widget.curselection()))]))
            selectedlat = str(my_info2[my_info1.index(event.widget.get(event.widget.curselection()))])
            selectedlon = str(my_info3[my_info1.index(event.widget.get(event.widget.curselection()))])
            selectedcity = event.widget.get(event.widget.curselection())
            self.member1.create_point(selectedlat, selectedlon, selectedcity)

    def resetcity(self, my_info1):
        global selectedlat, selectedlon, selectedcity
        self.Choice.delete(0, 'end')
        self.label3.configure(text="")
        if selectedcity is not "":
            self.member1.deletePoint(selectedlat, selectedlon, selectedcity)
            selectedcity = ""
            selectedlat = ""
            selectedlon = ""

    def writelog(self, msg):  # the main console log text feed
        self.Text2.insert('end -1 lines', "[" + str(time.strftime('%H:%M.%S', time.gmtime())) + "] - " + msg + "\n")
        time.sleep(0.01)
        self.Text2.see('end')

    def writelog2(self, msg):  # the Checkfile log text feed
        global t, checkfilesize
        if t == 0 and checkfilesize == 1:
            self.Text3.delete("0.0", END)
            t = 1
        if checkfilesize == 1:
            self.Text3.insert('end -1 lines', msg + "\n")
            time.sleep(0.01)
            self.Text2.see('end')

    @staticmethod
    def help():
        master = Tk()
        w = Message(master, text="""
    1/ Choose KiwiSDR nodes by left-click on them and select \"Use:\" command to add them to the list (min=3 max=6)
    2/ Enter the frequency, between 0 and 30000 (kHz)
    3/ Choose from the top bar menu a specific bandwidth for the IQ recordings if necessary
    4/ Hold Left-mouse button to move the World Map to your desired location
    5/ Hold Right-mouse button to drag a rec rectangle to set the TDoA computed map geographical boundaries 
       or select one of the presets from the top bar menu, you can cancel by drawing again by hand or choose RESET
    6/ Type some text in the bottom left box to search for a city or TX site to display on final TDoA map (if needed)
    7/ Click Start Recording button and wait for some seconds (Recorded IQ files size are displayed in the white window)
    8/ Click Start TDoA button and WAIT until the TDoA process stops! (it may take some CPU process time!)
    9/ Calculated TDoA map is automatically displayed as 'Figure1' ghostscript pop-up window and it will close itself
    10/ A PDF file will be created automaticaly, it takes time, so wait for the final popup window
    11/ All TDoA process files (wav/m/pdf) will be automaticaly saved in a subdirectory of TDoA/iq/
    """, width=1000, font="TkFixedFont 8", bg="white", anchor="center")
        w.pack()

    @staticmethod
    def about():  # About menu
        master = Tk()
        w = Message(master, text="""
    Welcome to directTDoA !

    I've decided to write that python GUI in order to compute the TDoA stuff faster & easier.
    Please note that I have no credits in all the GNU Octave calculation process (TDoA/m/*.m files).
    Also I have no credits in the all the kiwirecorder codes (TDoA/kiwiclient/*.py files).

    A backup copy of processed ".wav", ".m", ".pdf" files is automatically made in a TDoA/iq/ subdirectory
    Check TDoA/iq/<timeofprocess>_F<frequency>/ to find your files.
    You can compute again your IQ recordings, to do so, just copy the .wav in iq/ and proc_tdoa_xxxx.m in TDoA/
    Edit that proc_tdoa_xxxx.m to change map boundaries or remove IQ sources (don't forget to change the index numbers)
    Then, in linux terminal, type "octave-cli proc_tdoa_xxxx.m" from /TDoA directory to run again the process.
    Be aware that the next created PDF file will be stored in TDoA/pdf/ and NOT in the backup iq/ directory !

    The World map is not real-time, click UPDATE button to refresh, of course only GPS enabled nodes are displayed...

    Thanks to Christoph Mayer for the public release of his codes
    Thanks to John Seamons for the GPS timestamps in IQ files
    Thanks to Dmitry Janushkevich for the original kiwirecorder python codes

    linkz
    """, width=1000, font="TkFixedFont 8", bg="white", anchor="center")
        w.pack()

    def map_preset(self, pmap):  # save config menu
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

    def setmap(self, mapc):
        ReadConfigFile().read_cfg()
        SaveConfigFile().save_cfg("mapc", mapc)
        Restart().run()

    def runupdate(self):  # if UPDATE button is pushed
        self.Button1.configure(state="disabled")
        self.Button2.configure(state="disabled")
        self.Button3.configure(state="disabled")
        RunUpdate(self).start()  # start the update thread

    # ---------------------------------------------------MAIN-----------------------------------------------------------
    def clickfreq(self, ff):
        self.Button1.configure(state='normal')
        # self.Entry1.delete(0, 'end')

    def numeric_only(self, S):
        freq_typed = re.match(r"\d+(.\d+)?$", S)
        return freq_typed is not None

    def callback(self, frequency):
        pass

    def choosedfreq(self, ff):
        if ff.char in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'):
            try:
                frequency.trace("w", lambda name, index, mode, frequency=frequency: self.callback(frequency))
                return True
            except ValueError:
                return False
        else:
            pass

    def set_iq(self, m):
        global lpcut, hpcut
        try:
            if 5 < frequency.get() < 30000:
                self.writelog("Setting IQ bandwidth at " + m + " Hz       | " + str(
                float(frequency.get()) - (float(m) / 2000)) + " | <---- " + str(float(frequency.get())) + " ----> | " + str(
                float(frequency.get()) + (float(m) / 2000)) + " |")
                lpcut = hpcut = int(m) / 2
            else:
                frequency.set(10000)
                self.writelog("Error, frequency is too low or too high")
        except ValueError as ve:
            pass

    # def checksnr(self):  # work in progress
    #     global snrcheck, snrfreq
    #     snrcheck = True
    #     snrfreq = float(self.Entry1.get())
    #     snrfreq = snrfreq + 202.94
    #     snrfreq = str(snrfreq)

    def clickstart(self):
        global namelist, namelisting, frequency, hostlisting, latmin, latmax, lonmin, lonmax, lpcut, hpcut
        global serverlist, portlist, portlisting, starttime, x1, x2, y1, y2, mapboundaries_set

        if mapboundaries_set is None:
            tkMessageBox.showinfo("WARNING",
                                  message="Set TDoA map Geographical boundaries, right click and draw red rectangle or select one of presets via the top bar menu.")
        else:
            lonmin = str((((bbox2[0] - 1910) * 180) / 1910)).rsplit('.')[0]  # LONGITUDE MIN
            lonmax = str(((bbox2[2] - 1910) * 180) / 1910).rsplit('.')[0]  # LONGITUDE MAX
            latmax = str(0 - ((bbox2[1] - 990) / 11)).rsplit('.')[0]  # LATITUDE MAX
            latmin = str(20 - ((bbox2[3] - 990) / 11)).rsplit('.')[0]  # LATITUDE MIN
            namelisting = hostlisting = portlisting = ""
            for i in range(len(serverlist)):
                namelisting = namelisting + shortlist[i].replace('/', '') + ','
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
            elif len(namelist) < 3:
                self.writelog("ERROR: Select at least 3 nodes for TDoA processing !")
            else:
                frequency = str(float(self.Entry1.get()))
                self.Button1.configure(state="disabled")
                self.Button2.configure(state="normal")
                self.Button3.configure(state='disabled')
                if platform.system() == "Windows":
                    for wavfiles in glob.glob("TDoA\\iq\\*wav"):
                        os.remove(wavfiles)
                if platform.system() == "Linux" or platform.system() == "Darwin":
                    for wavfiles in glob.glob("./TDoA/iq/*wav"):
                        os.remove(wavfiles)
                time.sleep(0.2)
                StartKiwiSDR(self).start()
                CheckFileSize(self).start()

    def clickstop(self):
        global IQfiles, frequency, varfile, selectedlat, selectedlon
        global selectedcity, starttime, latmin, latmax, lonmin, lonmax, nbfile, proc2_pid
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map, checkfilesize
        checkfilesize = 0
        os.kill(proc2_pid, signal.SIGTERM)
        if platform.system() == "Windows":
            for file in os.listdir("TDoA\iq\\"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])
        if platform.system() == "Linux" or platform.system() == "Darwin":
            for file in os.listdir("./TDoA/iq/"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])
        firstfile = IQfiles[0]
        varfile = str(firstfile.split("_", 2)[1].split("_", 1)[0])
        for i in range(len(IQfiles)):
            nbfile = len(IQfiles)
        self.writelog("IQ Recording(s) has been stopped...")
        self.Button2.configure(state="disabled")

        #  creating the .m file
        with open('./TDoA/proc_tdoa_' + varfile + ".m", "w") as g:
            g.write("## -*- octave -*-\n")
            g.write("## This file was auto-generated by " + VERSION + "\n")
            g.write("\n")
            g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n")
            g.write("\n")
            for i in range(len(IQfiles)):
                g.write("  input(" + str(i + 1) + ").fn    = fullfile('iq', '" + str(IQfiles[i]) + "');\n")  # newformat
            g.write("""
  input = tdoa_read_data(input);

  ## 200 Hz high-pass filter
  b = fir1(1024, 500/12000, 'high');
  n = length(input);
  for i=1:n
    input(i).z      = filter(b,1,input(i).z)(512:end);
  end

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
                    selectedcity.rsplit(' (')[0]).replace('_', ' ') + "\')\n")
                g.write("""                    );\n

  tdoa = tdoa_plot_map(input, tdoa, plot_info);

disp("finished");
endfunction """)

        g.close()
        self.writelog("./TDoA/proc_tdoa_" + varfile + ".m file created")
        # backup of IQ, gnss_pos and .m file in a new directory named by the datetime process start and frequency
        time.sleep(0.5)
        if platform.system() == "Windows":
            os.makedirs("TDoA\iq\\" + starttime + "_F" + str(frequency))
            for file in os.listdir("TDoA\iq\\"):
                if file.endswith(".wav"):
                    copyfile("TDoA\iq\\" + file, "TDoA\iq\\" + starttime + "_F" + str(frequency) + "\\" + file)
            copyfile("TDoA\\proc_tdoa_" + varfile + ".m",
                     "TDoA\\iq\\" + starttime + "_F" + str(frequency) + "\\proc_tdoa_" + varfile + ".m")

        if platform.system() == "Linux" or platform.system() == "Darwin":
            os.makedirs("./TDoA/iq/" + starttime + "_F" + str(frequency))
            for file in os.listdir("./TDoA/iq//"):
                if file.endswith(".wav"):
                    copyfile("./TDoA/iq/" + file, "./TDoA/iq/" + starttime + "_F" + str(frequency) + "/" + file)
            copyfile("./TDoA/proc_tdoa_" + varfile + ".m",
                     "./TDoA/iq/" + starttime + "_F" + str(frequency) + "/proc_tdoa_" + varfile + ".m")
        self.writelog("Running Octave process now... please wait")
        time.sleep(0.5)
        OctaveProcessing(self).start()


class MainW(Tk, object):

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.window = ZoomAdvanced(self)
        self.window2 = MainWindow(self)


if __name__ == '__main__':
    app = MainW()
    app.title(VERSION)
    app.mainloop()