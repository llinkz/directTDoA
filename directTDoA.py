#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
import threading, os, signal, subprocess, platform, tkMessageBox, time, urllib2, re, glob, webbrowser
from os.path import dirname, abspath
from subprocess import PIPE
from PIL import Image, ImageTk
from shutil import copyfile
from tkColorChooser import askcolor


VERSION = "directTDoA v2.44 by linkz"


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
            time.sleep(0.5)
            if platform.system() == "Windows":
                for wavfiles in glob.glob("..\\iq\\*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("..\\iq\\", "")
                    self.parent.writelog2("~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0
            if platform.system() == "Linux" or platform.system() == "Darwin":
                for wavfiles in glob.glob("../iq/*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("../iq/", "")
                    self.parent.writelog2("~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0


class ProcessFinished:
    def __init__(self):
        pass

    def run(self):
        global tdoa_position
        finish = tkMessageBox.showinfo("PROCESS ENDED", str(tdoa_position) + "\n\nClick to restart the GUI")
        if finish:
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)


class ReadConfigFile:

    def __init__(self):
        pass

    def read_cfg(self):
        global dx0, dy0, dx1, dy1, dmap, mapfl, white, black, colorline
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            dmap = configline[3].split('\n')[0]
            mapfl = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
            colorline = configline[11].replace("\n", "").split(',')
        c.close()


class RunUpdate(threading.Thread):

    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        try:
            webpage = urllib2.urlopen("http://kiwisdr.com/public/")  # get the KiwiSDR servers infos page
            datatowrite = webpage.read()
            with open("kiwisdr.com_public_TDoA.htm", 'wb') as w:
                w.write(datatowrite)  # dl listing source
            nbnode = 0
            idfound = namefound = usersfound = usersmaxfound = latfound = lonfound = hostnamefound = gpsfound = None
            if os.path.isfile('directTDoA_server_list.db') is True:
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
                os.remove('directTDoA_server_list.db')
            with open('directTDoA_server_list.db', "w") as g:
                g.write("   \n")
                g.write("['ffffffffffff', 'linkz.ddns.net:8073', '45.5', '5.5', 'hf_linkz', '0', '4']\n")
                #  kiwi_names[u].replace("\xe2\x80\xa2 ", "").replace("\xc2\xb3", "").replace("\xf0\x9f\x93\xbb",
                #  "").replace("\xc2\xb2", "").replace("&#x1f4fb;", "").replace("&#x1f4e1;", "")) # optional for now
                with open('kiwisdr.com_public_TDoA.htm', "r") as f:
                    for line in f:  # parse the listing source html file, line after line, could be a better process
                        class_start = re.search(r'(<div class=\'(.*)cl-entry\'>)$', line)
                        id = re.search(r'<!-- id=([0-9a-f]{12}) -->', line)
                        hostname = re.search(r'<a href=\'http://(.*)\' .*', line)  # (?!:)
                        coords = re.search(r'<!-- gps=\((\s*|\@)(\-?\d+\.?\d+)\D*,\s*(\-?\d+\.?\d+).* -->', line)
                        name = re.search(r'<!-- name=(.*) -->', line)
                        users = re.search(r'<!-- users=(\d) -->', line)
                        users_max = re.search(r'<!-- users_max=(\d) -->', line)
                        sdrhw = re.search(r'<!-- sdr_hw=(.*) -->', line)
                        class_stop = re.search(r'  <span class=\'cl-users\'>(.*)</span> <br>$', line)
                        if class_start:
                            nodefound = True
                        if id:
                            idfound = id.group(1)
                        if name:
                            namefound = name.group(1).replace(".", "").replace(",", "").replace('"', '').replace("'", "")
                            namefound = namefound.decode('utf-8')
                        if sdrhw:
                            if " GPS " in sdrhw.group(1):
                                gpsfound = "GPS"
                        if users:
                            usersfound = users.group(1)
                        if users_max:
                            usersmaxfound = users_max.group(1)
                        if coords:
                            latfound = coords.group(2)
                            lonfound = coords.group(3)
                        if hostname:
                            hostnamefound = hostname.group(1)
                        if class_stop and nodefound is True:
                            nodefound = False
                            if idfound is not None and namefound is not None and gpsfound is not None  \
                                and usersfound is not None and usersmaxfound is not None and latfound is not None \
                                and lonfound is not None and hostnamefound is not None:
                                mynodeid = "['" + idfound + "', '" + hostnamefound + "', '" + latfound + "', '" + lonfound + "', '" + namefound + "', '" + usersfound + "', '" + usersmaxfound + "']"
                                mynodeid = mynodeid.encode('ascii','ignore')
                                nbnode += 1
                                g.write("%s\n" % str(mynodeid))
                                idfound = namefound = usersfound = usersmaxfound = latfound = lonfound = hostnamefound = gpsfound = None
                            else:
                                idfound = namefound = usersfound = usersmaxfound = latfound = lonfound = hostnamefound = gpsfound = None
                                nodefound = False
                        else:
                            pass
                f.close()
                os.remove('kiwisdr.com_public_TDoA.htm')
                g.seek(0)
                g.write("%s\n" % str(nbnode + 1))
            g.close()
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)
        except urllib2.URLError, err:
            print "UPDATE FAIL, can't retrieve kiwisdr.com/public page"
            print str(err.reason)


class OctaveProcessing(threading.Thread):
    def __init__(self, parent=None):
        super(OctaveProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global varfile, tdoa_position, bad_node
        tdoa_filename = "proc_tdoa_" + varfile + ".m"
        bad_node = False
        if platform.system() == "Windows":  # not working
            exec_octave = 'C:\Octave\Octave-4.2.1\octave.vbs --no-gui'
            # tdoa_filename = 'C:\Users\linkz\Desktop\TDoA-master-win\\' + tdoa_filename  # work in progress for Windows
        if platform.system() == "Linux" or platform.system() == "Darwin":
            exec_octave = 'octave'
        proc = subprocess.Popen([exec_octave, tdoa_filename], cwd=dirname(dirname(abspath(__file__))), stdout=PIPE,
                                shell=False)
        while True:
            line = proc.stdout.readline()
            if line != '':
                pass
            if "iq/" in line:
                self.parent.writelog("processing " + line.rstrip())
                if "wav 254" in line:  # adding the parse of number 254 indicating no GPS timestamps found in the IQ rec
                    bad_node = True
                    self.parent.writelog("WARNING: \"" + line.rstrip().rsplit('_', 3)[
                        2] + "\" has no recent GPS timestamps, remove it next time.")
            if "tdoa" in line:
                self.parent.writelog(line.rstrip())
            if "most likely position:" in line:
                tdoa_position = line.rstrip()
                self.parent.writelog(line.rstrip())
            if "finished" in line:
                if bad_node:
                    self.parent.writelog(
                        "WARNING: bad GPS node(s) have been used, consider this TDoA as incomplete.")
                ProcessFinished().run()


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
        global parent, line, nbfile, IQfiles, t
        IQfiles = []
        line = []
        nbfile = 1
        t = 0
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux" or platform.system() == "Darwin":
            execname = 'python2'
        proc2 = subprocess.Popen(
            [execname, 'kiwirecorder.py', '-s', str(hostlisting), str(namelisting), '-f', str(frequency), '-p',
             str(portlisting), '-L', str(lpcut), '-H', str(hpcut), '-m', 'iq', '-w'], stdout=PIPE, shell=False)
        self.parent.writelog("IQ recording in progress...please wait")
        proc2_pid = proc2.pid


class FillMapWithNodes(threading.Thread):

    def __init__(self, parent=None):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
        time.sleep(0.5)
        if os.path.isfile('directTDoA_server_list.db') is True:
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
                    id = re.search(r"\['(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)', '(.*)'\]$", line)
                    my_tag.append(id.group(1))
                    my_host.append(id.group(2))
                    my_lat.append(id.group(3))
                    my_lon.append(id.group(4))
                    my_name.append(id.group(5).replace(" ", "_"))
                    my_user.append(id.group(6))
                    my_usermx.append(id.group(7))
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
                    if my_tag[n] in white:  # if favorite  node color = white
                        mycolor.append(colorline[1])
                    elif my_tag[n] in black:  # if blacklisted  node color = black
                        mycolor.append(colorline[2])
                    else:
                        mycolor.append(colorline[0])  # if normal node color = green
                else:
                    mycolor.append('red')  # if no slots, map point is always created red
                n += 1

            if mapfl == "0":  # display all nodes
                m = 0
                while m < len(my_tag):
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m],
                                                        fill=mycolor[m], outline="black", activefill='white', tag=str(
                            my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(
                        str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]),
                        "<Button-1>", self.parent.onClick)
                    m += 1
            if mapfl == "1":  # display standard + favorites
                m = 0
                while m < len(my_tag):
                    if my_tag[m] not in black:
                        self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m],
                                                            fill=mycolor[m], outline="black", activefill='white',
                                                            tag=str(
                                                                my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" +
                                                                my_user[m] + "$" + my_usermx[m]))
                        self.parent.canvas.tag_bind(str(
                            my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]),
                                                    "<Button-1>", self.parent.onClick)
                    else:
                        pass
                    m += 1
            if mapfl == "2":  # display favorites only
                m = 0
                while m < len(my_tag):
                    if my_tag[m] in white:
                        self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m],
                                                            fill=mycolor[m], outline="black", activefill='white',
                                                            tag=str(
                                                                my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" +
                                                                my_user[m] + "$" + my_usermx[m]))
                        self.parent.canvas.tag_bind(str(
                            my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]),
                                                    "<Button-1>", self.parent.onClick)
                    else:
                        pass
                    m += 1
            if mapfl == "3":  # display blacklisted only
                m = 0
                while m < len(my_tag):
                    if my_tag[m] in black:
                        self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m],
                                                            fill=mycolor[m], outline="black", activefill='white',
                                                            tag=str(
                                                                my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" +
                                                                my_user[m] + "$" + my_usermx[m]))
                        self.parent.canvas.tag_bind(str(
                            my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]),
                                                    "<Button-1>", self.parent.onClick)
                    else:
                        pass
                    m += 1
            self.parent.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map pos.
            self.parent.show_image()

    def deletePoint(self, n):  # city mappoint deletion process
        self.parent.canvas.delete(self.parent, n.rsplit(' (')[0])


class ZoomAdvanced(Frame):  # src stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 :)
    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        parent.geometry("1000x670+300+0")
        global dx0, dy0, dx1, dy1
        global serverlist, portlist, namelist, dmap, host, white, black, mapfl, mapboundaries_set
        # host = Variable
        serverlist = []
        portlist = []
        namelist = []
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
        FillMapWithNodes(self).start()

    def displaySNR(self):  # work in progress
        print host

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red')

    def on_move_press(self, event):  # draw mapping bordering for the final TDoA map need
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map
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
        if event.x > 0.98*w:
            self.canvas.xview_scroll(1, 'units')
        elif event.x < 0.02*w:
            self.canvas.xview_scroll(-1, 'units')
        if event.y > 0.98*h:
            self.canvas.yview_scroll(1, 'units')
        elif event.y < 0.02*h:
            self.canvas.yview_scroll(-1, 'units')
        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
        self.show_image()

    def on_button_release(self, event):
        global mapboundaries_set
        tkMessageBox.showinfo("TDoA map Geographical boundaries set",
                              message="LONGITUDE RANGE: from " + lon_min_map + "° to " + lon_max_map + "°\nLATITUDE RANGE: from " + lat_min_map + "° to " + lat_max_map + "°")
        mapboundaries_set = 1

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

    def deletePoint(self, y, x, n):  # city map point deletion process
        FillMapWithNodes(self).deletePoint(n.rsplit(' (')[0])

    def onClick(self, event):
        global snrcheck, snrhost, host, white, black, frequency
        # x1, x2, y1, y2, o, full_list, snrcheck, snrhost, host
        host = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        self.menu = Menu(self, tearoff=0, fg="black", bg="gray", font='TkFixedFont 7')
        if int(host.rsplit("$", 4)[3]) / int(host.rsplit("$", 4)[4]) == 0:
            self.menu.add_command(
                label="Use: " + str(host).rsplit("$", 4)[0] + " (" + str(host).rsplit("$", 4)[3] + "/" +
                      str(host).rsplit("$", 4)[4] + " users) for TdoA process", command=self.populate)
            self.menu.add_command(
                label="Open \"" + str(host).rsplit("$", 4)[0] + "/f=" + str(frequency) + "iqz8\" in browser",
                command=self.openinbrowser)
        else:
            self.menu.add_command(
                label="Use: " + str(host).rsplit("$", 4)[0] + " (" + str(host).rsplit("$", 4)[3] + "/" +
                      str(host).rsplit("$", 4)[4] + " users) for TdoA process", state=DISABLED, command=None)
            self.menu.add_command(
                label="Open \"" + str(host).rsplit("$", 4)[0] + "/f=" + str(frequency) + "iqz8\" in browser",
                state=DISABLED, command=None)

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
        if host.rsplit('$', 4)[1] in white:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already in the favorite list !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
                if white[0] == "":
                    u.write("# Whitelist \n%s\n" % host.rsplit('$', 4)[1])
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                else:
                    white.append(host.rsplit('$', 4)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the favorite list !")
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)

    def remfavorite(self):
        global white, black, newwhite
        newwhite = []
        ReadConfigFile().read_cfg()
        for f in white:
            if f != host.rsplit('$', 4)[1]:
                newwhite.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
            u.write("# Whitelist \n%s\n" % ','.join(newwhite))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
        u.close()
        tkMessageBox.showinfo(title=" ",
                              message=str(host.rsplit(':')[0]) + " has been removed from the favorites list !")
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    def addblacklist(self):
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 4)[1] in black:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already blacklisted !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
                if black[0] == "":
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % host.rsplit('$', 4)[1])
                else:
                    black.append(host.rsplit('$', 4)[1])
                    u.write("# Whitelist \n%s\n" % ','.join(white))
                    u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
            u.close()
            tkMessageBox.showinfo(title=" ",
                                  message=str(host.rsplit(':')[0]) + " has been added to the blacklist !")
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)

    def remblacklist(self):
        global white, black, newblack
        newblack = []
        ReadConfigFile().read_cfg()
        for f in black:
            if f != host.rsplit('$', 4)[1]:
                newblack.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % dmap)
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(newblack))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
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
        # self.canvas.configure(scrollregion=bbox)  # set scroll region
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
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ", message="oops no database found, Click OK to run an update now")
            RunUpdate().run()
        ReadKnownPointFile().run()
        global frequency, checkfilesize
        global line, i, bgc, fgc, dfgc, lpcut, hpcut
        global latmin, latmax, lonmin, lonmax, bbox1, lat_min_map, lat_max_map, lon_min_map, lon_max_map
        global selectedlat, selectedlon, selectedcity
        frequency = DoubleVar()
        bgc = '#d9d9d9'
        fgc = '#000000'
        dfgc = '#a3a3a3'
        frequency = 10000  # default frequency
        lpcut = 5000  # default low pass filter
        hpcut = 5000  # default high pass filter
        lat_min_map = ""
        lat_max_map = ""
        lon_min_map = ""
        lon_max_map = ""
        selectedlat = ""
        selectedlon = ""
        selectedcity = ""

        self.label0 = Label(parent)
        self.label0.place(relx=0, rely=0.69, relheight=0.4, relwidth=1)
        self.label0.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="")

        self.Entry1 = Entry(parent, textvariable=frequency)  # frequency box
        self.Entry1.place(relx=0.06, rely=0.892, height=24, relwidth=0.1)
        self.Entry1.configure(background="white", disabledforeground=dfgc, font="TkFixedFont", foreground=fgc,
                              insertbackground=fgc, width=214)
        self.Entry1.bind('<FocusIn>', self.clickfreq)
        self.Entry1.bind('<Leave>', self.choosedfreq)

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
                               text="Start recording", command=self.clickstart, state="disabled")

        self.Button2 = Button(parent)  # Stop button
        self.Button2.place(relx=0.88, rely=0.89, height=24, relwidth=0.1)
        self.Button2.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Start TDoA proc", command=self.clickstop, state="disabled")

        # self.TCombobox1 = ttk.Combobox(parent, state=DISABLED)  # IQ BW Combobox disabled until it's functionnal
        # self.TCombobox1.place(relx=0.24, rely=0.892, height=24, relwidth=0.1)
        # self.TCombobox1.configure(font="TkTextFont",
        #                         values=["IQ bandwidth", "10000", "5000", "4000", "3000", "2000", "1000", "500", "400",
        #                                   "300", "200", "100", "50"])
        # self.TCombobox1.current(0)
        # self.TCombobox1.bind("<<ComboboxSelected>>", self.bwchoice)

        #  2nd part of buttons

        self.Choice = Entry(parent)
        self.Choice.place(relx=0.01, rely=0.95, height=21, relwidth=0.18)
        self.Choice.insert(0, "TDoA map city/site search here")
        self.ListBox = Listbox(parent)
        self.ListBox.place(relx=0.2, rely=0.95, height=21, relwidth=0.3)
        self.label3 = Label(parent)  # KNOWN POINT
        self.label3.place(relx=0.54, rely=0.95, height=21, relwidth=0.3)
        self.label3.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="", anchor="w")

        self.Button5 = Button(parent)  # Restart GUI button
        self.Button5.place(relx=0.81, rely=0.94, height=24, relwidth=0.08)
        self.Button5.configure(activebackground=bgc, activeforeground=fgc, background="red", disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="Restart GUI", command=self.restartgui, state="normal")

        self.Button3 = Button(parent)  # Update button
        self.Button3.place(relx=0.90, rely=0.94, height=24, relwidth=0.08)
        self.Button3.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="update map", command=self.runupdate, state="normal")

        self.Text2 = Text(parent)  # console window
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
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Map Settings", menu=filemenu)
        submenu1 = Menu(filemenu, tearoff=0)
        submenu2 = Menu(filemenu, tearoff=0)
        submenu3 = Menu(filemenu, tearoff=0)
        filemenu.add_cascade(label='Default map', menu=submenu1, underline=0)
        submenu1.add_command(label="Grayscale (bright)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_grayscale_bright.jpg'))
        submenu1.add_command(label="Grayscale (dark)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_grayscale.jpg'))
        submenu1.add_command(label="Sat",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_sat.jpg'))
        submenu1.add_command(label="Snow Cover",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_snowcover.jpg'))
        submenu1.add_command(label="NASA Albedo",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_albedo.jpg'))
        submenu1.add_command(label="NASA BlueMarble",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_bluemarble.jpg'))
        submenu1.add_command(label="NASA Topography",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_topo.jpg'))
        submenu1.add_command(label="NASA Topography (grayscale)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_topo_grayscale.jpg'))
        submenu1.add_command(label="NASA Vegetation",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_vegetation.jpg'))
        submenu1.add_command(label="NASA Vegetation (grayscale)",
                             command=lambda *args: self.saveconfig('maps/directTDoA_map_NASA_vegetation_grayscale.jpg'))
        filemenu.add_cascade(label='Map Filter', menu=submenu2, underline=0)
        submenu2.add_command(label="Display All nodes", command=lambda *args: self.setmapfilter('0'))
        submenu2.add_command(label="Display Standard + Favorites", command=lambda *args: self.setmapfilter('1'))
        submenu2.add_command(label="Display Favorites", command=lambda *args: self.setmapfilter('2'))
        submenu2.add_command(label="Display Blacklisted", command=lambda *args: self.setmapfilter('3'))
        filemenu.add_cascade(label='Set Colors', menu=submenu3, underline=0)
        submenu3.add_command(label="Standard node color", command=lambda *args: self.color_change(0))
        submenu3.add_command(label="Favorite node color", command=lambda *args: self.color_change(1))
        submenu3.add_command(label="Blacklisted node color", command=lambda *args: self.color_change(2))
        submenu3.add_command(label="Known map point color", command=lambda *args: self.color_change(3))
        menubar.add_command(label="How to TDoA with this tool", command=self.about)
        menubar.add_command(label="General infos", command=self.general)

        self.listbox_update(my_info1)
        self.ListBox.bind('<<ListboxSelect>>', self.on_select)
        self.Choice.bind('<FocusIn>', self.resetcity)
        self.Choice.bind('<KeyRelease>', self.on_keyrelease)

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

    @staticmethod
    def restartgui():
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

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
    def about():  # about menu
        tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                              message="""
1/ Choose nodes by clicking on them (min=3 max=6)
    
2/ Enter a frequency (in kHz)
    
3/ Hold Left-mouse button to move the World Map to your desired location
    
4/ Hold Right-mouse button to drag a rec rectangle to set the TDoA computed map geographical boundaries
    
5/ Type some text in the bottom left box to choose a city or TX site to display on final TDoA map (if needed)
    
6/ Click Start Recording button and wait for some seconds (Recorded IQ files size are displayed in the white window)
    
7/ Click Start TDoA button and WAIT until the TDoA process stops! (it may take some CPU process time!)
        
8/ Calculated TDoA map is automatically displayed as Figure1 pop-up window
    
9/ There is a .pdf created in TDoA/pdf directory but this file creation process takes more time !!!
Wait for the final popup window that tells you the most likely location found by the TDoA process
""")

    @staticmethod
    def general():  # about menu
        tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                              message="""
A backup copy of ".wavs" ".m" and "gnss_pos" files is automatically made in a new "iq/<timeofprocess>_F<frequency>/"
directory to post-compute again the recs if needed

The World map is not real-time, click UPDATE button to refresh, of course, only GPS enabled nodes are displayed...
""")

    @staticmethod
    def setmapfilter(mapfl):
        ReadConfigFile().read_cfg()
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % dmap)
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
        u.close()
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    @staticmethod
    def color_change(value):  # node color choices
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
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
                u.write("# Default map picture \n%s\n" % dmap)
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
                u.write("# Whitelist \n%s\n" % ','.join(white))
                u.write("# Blacklist \n%s\n" % ','.join(black))
                u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % colorline)
            u.close()
            executable = sys.executable
            args = sys.argv[:]
            args.insert(0, sys.executable)
            os.execvp(sys.executable, args)

    @staticmethod
    def saveconfig(dmap):  # save config menu
        global bbox2
        ReadConfigFile().read_cfg()
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % dmap)
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % mapfl)
            u.write("# Whitelist \n%s\n" % ','.join(white))
            u.write("# Blacklist \n%s\n" % ','.join(black))
            u.write("# Default Colors (standard,favorites,blacklisted,known) \n%s\n" % ','.join(colorline))
        u.close()
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(sys.executable, args)

    def runupdate(self):  # if UPDATE button is pushed
        self.Button1.configure(state="disabled")
        self.Button2.configure(state="disabled")
        self.Button3.configure(state="disabled")
        RunUpdate(self).start()  # start the update thread

    # ---------------------------------------------------MAIN-----------------------------------------------------------
    def clickfreq(self, ff):
        self.Button1.configure(state='normal')
        # self.Entry1.delete(0, 'end')

    def choosedfreq(self, ff):
        global frequency
        frequency = self.Entry1.get()

    # def bwchoice(self, m):  # affects only the main window apparance, real-time   work in progress
    #     global bw, lpcut, hpcut
    #     bw = self.TCombobox1.get()
    #     self.writelog("|<----" + str(int(bw)/2) + "Hz ----[tune frequency]---- " + str(int(bw)/2) + "Hz ---->|")
    #     lpcut = hpcut = int(bw) / 2

    # def checksnr(self):  #work in progress
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
                                  message="Set TDoA map Geographical boundaries, right click and draw red rectangle")
        else:
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
            elif len(namelist) < 3:
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
                if platform.system() == "Linux" or platform.system() == "Darwin":
                    for wavfiles in glob.glob("../iq/*wav"):
                        os.remove(wavfiles)
                    for gnssfiles in glob.glob("../gnss_pos/*txt"):
                        os.remove(gnssfiles)
                time.sleep(1)
                StartKiwiSDR(self).start()
                CheckFileSize(self).start()

    def clickstop(self):
        global IQfiles, frequency, varfile, selectedlat, selectedlon
        global selectedcity, starttime, latmin, latmax, lonmin, lonmax, nbfile, proc2_pid
        global lat_min_map, lat_max_map, lon_min_map, lon_max_map, checkfilesize
        checkfilesize = 0
        os.kill(proc2_pid, signal.SIGINT)
        if platform.system() == "Windows":
            for file in os.listdir("..\iq\\"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])
        if platform.system() == "Linux" or platform.system() == "Darwin":
            for file in os.listdir("../iq//"):
                if file.endswith(".wav"):
                    IQfiles.append(os.path.split(file)[1])
        firstfile = IQfiles[0]
        varfile = str(firstfile.split("_", 2)[1].split("_", 1)[0])
        for i in range(len(IQfiles)):
            nbfile = len(IQfiles)
        self.writelog("IQ Recording(s) has been stopped...")
        self.Button2.configure(state="disabled")
        # make a backup of IQ and gnss_pos files in a new directory named by the datetime process start and frequency
        time.sleep(1)
        if platform.system() == "Windows":
            os.makedirs("..\iq\\" + starttime + "_F" + str(frequency))
            for file in os.listdir("..\iq\\"):
                if file.endswith(".wav"):
                    copyfile("..\iq\\" + file, "..\iq\\" + starttime + "_F" + str(frequency) + "\\" + file)
            for file in os.listdir("..\gnss_pos\\"):
                if file.endswith(".txt"):
                    copyfile("..\gnss_pos\\" + file, "..\iq\\" + starttime + "_F" + str(frequency) + "\\" + file)
        if platform.system() == "Linux" or platform.system() == "Darwin":
            os.makedirs("../iq/" + starttime + "_F" + str(frequency))
            for file in os.listdir("../iq//"):
                if file.endswith(".wav"):
                    copyfile("../iq/" + file, "../iq/" + starttime + "_F" + str(frequency) + "/" + file)
            for file in os.listdir("../gnss_pos//"):
                if file.endswith(".txt"):
                    copyfile("../gnss_pos/" + file, "../iq/" + starttime + "_F" + str(frequency) + "/" + file)

        #  creating the .m file
        with open(dirname(dirname(abspath(__file__))) + '/proc_tdoa_' + varfile + ".m", "w") as g:
            g.write("## -*- octave -*-\n")
            g.write("## This file has been generated by " + VERSION + "\n")
            g.write("\n")
            g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n")
            g.write("\n")
            for i in range(len(IQfiles)):
                # g.write("  input(" + str(i + 1) + ").fn    = 'iq/" + str(IQfiles[i]) + "';\n")  old format
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
        self.writelog("../proc_tdoa_" + varfile + ".m file created")
        #  backup the .m file in previously /iq/... created dir
        if platform.system() == "Windows":
            copyfile("..\\proc_tdoa_" + varfile + ".m",
                     "..\\iq\\" + starttime + "_F" + str(frequency) + "\\proc_tdoa_" + varfile + ".m")
        if platform.system() == "Linux" or platform.system() == "Darwin":
            copyfile("../proc_tdoa_" + varfile + ".m",
                     "../iq/" + starttime + "_F" + str(frequency) + "/proc_tdoa_" + varfile + ".m")
        self.writelog("running Octave process now... please wait")
        time.sleep(1)
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