#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
import threading, os, signal, subprocess, platform, tkMessageBox, time, urllib2, re, glob, webbrowser, ttk
from os.path import dirname, abspath
from subprocess import PIPE
from PIL import Image, ImageTk
from shutil import copyfile
from tkColorChooser import askcolor


VERSION = "directTDoA v2.30 by linkz"


class ReadConfigFile:

    def __init__(self):
        pass

    def read_cfg(self):
        global dx0, dy0, dx1, dy1, dmap, dmapfilter, white, black, colorline
        with open('directTDoA.cfg', "r") as c:
            configline = c.readlines()
            dx0 = configline[1].split(',')[0]
            dy0 = configline[1].split(',')[1]
            dx1 = configline[1].split(',')[2]
            dy1 = configline[1].split(',')[3]
            dmap = configline[3].split('\n')[0]
            dmapfilter = configline[5].split('\n')[0]
            white = configline[7].replace("\n", "").split(',')
            black = configline[9].replace("\n", "").split(',')
            colorline = configline[11].replace("\n", "").split(',')
        c.close()


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


class OctaveProcessing(threading.Thread):
    def __init__(self, parent=None):
        super(OctaveProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global varfile
        tdoa_filename = "proc_tdoa_" + varfile + ".m"
        if platform.system() == "Windows":  # not working
            exec_octave = 'C:\Octave\Octave-4.2.1\octave.vbs --no-gui '
            tdoa_filename = 'C:\Users\linkz\Desktop\TDoA-master-win\\' + tdoa_filename
        if platform.system() == "Linux":
            exec_octave = '/usr/bin/octave-cli'
        proc = subprocess.Popen([exec_octave, tdoa_filename], cwd=dirname(dirname(abspath(__file__))), stdout=PIPE,
                                shell=False)
        while True:
            line = proc.stdout.readline()
            if line != '':
                pass  # self.parent.writelog("Octave INFO", line.rstrip())
            if "iq/" in line:
                self.parent.writelog("processing " + line.rstrip())
            if "tdoa" in line:
                self.parent.writelog(line.rstrip())
            if "most likely position:" in line:
                tdoa_position = line.rstrip()
            if "finished" in line:
                self.parent.writelog("processing finished, killing " + str(proc.pid) + " pid.")
                os.kill(proc.pid, signal.SIGKILL)
                finish = tkMessageBox.showinfo("PROCESS ENDED", str(tdoa_position) + "\n\nClick to restart the GUI")
                if finish:
                    executable = sys.executable
                    args = sys.argv[:]
                    args.insert(0, sys.executable)
                    os.execvp(sys.executable, args)


class SnrProcessing(threading.Thread):  # work in progress
    def __init__(self, parent=None):
        super(SnrProcessing, self).__init__()
        self.parent = parent

    def run(self):
        global proc3, snrfreq
        if platform.system() == "Windows":
            execname = 'python'
        if platform.system() == "Linux":
            execname = 'python2'
        proc3 = subprocess.Popen(
            [execname, 'microkiwi_waterfall.py', '--file=wf.bin', '-z', '8', '-o', str(snrfreq), '-s', str(snrhost)], stdout=PIPE, shell=False)
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
                    self.parent.writelog2(
                        "~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0
            if platform.system() == "Linux":
                for wavfiles in glob.glob("../iq/*wav"):
                    os.path.getsize(wavfiles)
                    filename = wavfiles.replace("../iq/", "")
                    self.parent.writelog2(
                        "~" + str(filename[17:]) + " - " + str(os.path.getsize(wavfiles) / 1024) + "KB")
                t = 0


class FillMapWithNodes(threading.Thread):

    def __init__(self, parent=None):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
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
        # with open('directTDoA.cfg', "r") as c:
        #     configline = c.readlines()
        #     mapfilter = configline[5].split('\n')[0]
        #     white = configline[7].replace("\n", "").split(',')
        #     black = configline[9].replace("\n", "").split(',')
        # c.close()
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

        if dmapfilter == "0":  # display all nodes
            m = 0
            while m < len(my_tag):
                self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                m += 1
        if dmapfilter == "1":  # display standard + favorites
            m = 0
            while m < len(my_tag):
                if my_tag[m] not in black:
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                else:
                    pass
                m += 1
        if dmapfilter == "2":  # display favorites only
            m = 0
            while m < len(my_tag):
                if my_tag[m] in white:
                    self.parent.canvas.create_rectangle(my_x_zeros[m], my_y_zeros[m], my_x_ones[m], my_y_ones[m], fill=mycolor[m], outline="black", activefill='white', tag=str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]))
                    self.parent.canvas.tag_bind(str(my_host[m] + "$" + my_tag[m] + "$" + my_name[m] + "$" + my_user[m] + "$" + my_usermx[m]), "<Button-1>", self.parent.onClick)
                else:
                    pass
                m += 1
        if dmapfilter == "3":  # display blacklisted only
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
        global dx0, dy0, dx1, dy1
        global serverlist, portlist, namelist, dmap, host, white, black, dmapfilter, mapboundaries_set
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

    def displaySNR(self):  #  work in progress
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
        if event.x > 0.98*w:
            self.canvas.xview_scroll(1, 'units')
        elif event.x < 0.02*w:
            self.canvas.xview_scroll(-1, 'units')
        if event.y > 0.98*h:
            self.canvas.yview_scroll(1, 'units')
        elif event.y < 0.02*h:
            self.canvas.yview_scroll(-1, 'units')
        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
        self.show_image()

    def on_button_release(self, event):
        global mapboundaries_set
        tkMessageBox.showinfo("TDoA map Geographical boundaries set",
                              message="LONGITUDE RANGE: from " + lon_min_map + "° to " + lon_max_map + "°\nLATITUDE RANGE: from " + lat_min_map + "° to " + lat_max_map + "°")
        mapboundaries_set = 1

    def createPoint(self, y ,x ,n):  # city mappoint creation process, works only when self.imscale = 1.0
        global currentcity, selectedcity
        #  city coordinates y & x (degrees) converted to pixels
        xx0 = (1907.5 + ((float(x) * 1910) / 180))
        xx1 = xx0 + 5
        if float(y) > 0:                                    # city is located in North Hemisphere
            yy0 = (987.5 - (float(y) * 11))
            yy1 = (987.5 - (float(y) * 11) + 5)
        else:                                               # city is located in South Hemisphere
            yy0 = (987.5 + (float(0 - (float(y) * 11))))
            yy1 = (987.5 + (float(0 - float(y)) * 11) + 5)

        self.canvas.create_rectangle(xx0, yy0, xx1, yy1, fill=colorline[3], outline="black", activefill=colorline[3],
                                         tag=selectedcity.rsplit(' (')[0])
        self.canvas.create_text(xx0, yy0 - 10, text=selectedcity.rsplit(' (')[0], justify='center', fill=colorline[3],
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
        # print str(host).rsplit("$", 4)[2].replace("_", " ")  # Name
        # print host.rsplit('$', 4)[1]  # ID
        global white, black
        ReadConfigFile().read_cfg()
        if host.rsplit('$', 4)[1] in white:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already in the favorite list !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
                u.write("# Default map picture \n%s\n" % (dmap))
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
        newwhite =[]
        ReadConfigFile().read_cfg()
        for f in white:
            if f != host.rsplit('$', 4)[1]:
                newwhite.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
                u.write("# Default map picture \n%s\n" % (dmap))
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
        newblack =[]
        ReadConfigFile().read_cfg()
        for f in black:
            if f != host.rsplit('$', 4)[1]:
                newblack.append(f)
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s" % (dx0, dy0, dx1, dy1))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
            if int(i * self.imscale) < 600: return  # block zoom if image is less than 600 pixels
            self.imscale /= self.delta
            scale /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
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
        self.member1 = Zoom_Advanced(parent)
        global frequency, checkfilepid
        global line, kiwi_update, i, bgc, fgc, dfgc, city, citylat, citylon, lpcut, hpcut
        global latmin, latmax, lonmin, lonmax, bbox1, lat_min_map, lat_max_map, lon_min_map, lon_max_map
        global selectedlat, selectedlon
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
        #                           values=["IQ bandwidth", "10000", "5000", "4000", "3000", "2000", "1000", "500", "400",
        #                                   "300", "200", "100", "50"])
        # self.TCombobox1.current(0)
        # self.TCombobox1.bind("<<ComboboxSelected>>", self.bwchoice)

        #  2nd part of buttons
        self.citylist = ttk.Combobox(parent, values=list(city), state="readonly")  # KNOWN POINT to display on TDoA map
        self.citylist.place(relx=0.01, rely=0.94, relheight=0.03, relwidth=0.45)
        self.citylist.current(0)
        self.citylist.bind('<<ComboboxSelected>>', self.citychoice)

        self.label7 = Label(parent)  # LABEL for KNOWN POINT coordinates
        self.label7.place(relx=0.52, rely=0.935, relheight=0.04, relwidth=0.3)
        self.label7.configure(background=bgc, font="TkFixedFont", foreground=fgc, width=214, text="", anchor="w")

        self.Button4 = Button(parent)  # KNOWN POINT RESET
        self.Button4.place(relx=0.465, rely=0.94, height=22, relwidth=0.05)
        self.Button4.configure(activebackground=bgc, activeforeground=fgc, background=bgc, disabledforeground=dfgc,
                               foreground=fgc, highlightbackground=bgc, highlightcolor=fgc, pady="0",
                               text="RESET", command=self.resetcity, state="disabled")

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
        self.writelog("All credits to Christoph Mayer for his excellent TDoA work (https://github.com/hcab14/TDoA)")
        vsb2 = Scrollbar(parent, orient="vertical", command=self.Text2.yview)  # adding scrollbar to console
        vsb2.place(relx=0.6, rely=0.7, relheight=0.18, relwidth=0.02)
        self.Text2.configure(yscrollcommand=vsb2.set)

        self.Text3 = Text(parent)  # IQ recs file size window
        self.Text3.place(relx=0.624, rely=0.7, relheight=0.18, relwidth=0.37)
        self.Text3.configure(background="white", font="TkTextFont", foreground="black", highlightbackground=bgc,
                             highlightcolor=fgc, insertbackground=fgc, selectbackground="#c4c4c4",
                             selectforeground=fgc, undo="1", width=970, wrap="word")

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
        filemenu.add_cascade(label='Map Filter', menu=submenu2, underline=0)
        submenu2.add_command(label="Display All nodes", command=lambda *args: self.setMapFilter('0'))
        submenu2.add_command(label="Display Standard + Favorites", command=lambda *args: self.setMapFilter('1'))
        submenu2.add_command(label="Display Favorites", command=lambda *args: self.setMapFilter('2'))
        submenu2.add_command(label="Display Blacklisted", command=lambda *args: self.setMapFilter('3'))
        filemenu.add_cascade(label='Set Colors', menu=submenu3, underline=0)
        submenu3.add_command(label="Standard node color", command=lambda *args: self.color_change(0))
        submenu3.add_command(label="Favorite node color", command=lambda *args: self.color_change(1))
        submenu3.add_command(label="Blacklisted node color", command=lambda *args: self.color_change(2))
        submenu3.add_command(label="Known map point color", command=lambda *args: self.color_change(3))
        menubar.add_command(label="How to TDoA with this tool", command=self.about)
        menubar.add_command(label="General infos", command=self.general)

    # -------------------------------------------------LOGGING------------------------------------------------------

    def writelog(self, msg):  # the main console log text feed
        self.Text2.insert('end -1 lines', "[" + str(time.strftime('%H:%M.%S', time.gmtime())) + "] - " + msg + "\n")
        time.sleep(0.01)
        self.Text2.see('end')

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
    [HOW TO USE THE GUI]

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
    
        PLEASE WAIT UNTIL THE GUI RESTARTS BY ITSELF.
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
    def setMapFilter(dmapfilter):
        ReadConfigFile().read_cfg()
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write("# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
                u.write("# Default map picture \n%s\n" % (dmap))
                u.write(
                    "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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
        global bbox2  # mapfilter
        ReadConfigFile().read_cfg()
        # with open('directTDoA.cfg', "r") as c:
        #     configline = c.readlines()
        #     white = configline[7].replace("\n", "").split(',')
        #     black = configline[9].replace("\n", "").split(',')
        # c.close()
        os.remove('directTDoA.cfg')
        with open('directTDoA.cfg', "w") as u:
            u.write("# Default map geometry \n%s,%s,%s,%s\n" % (bbox2[0], bbox2[1], bbox2[2], bbox2[3]))
            u.write("# Default map picture \n%s\n" % (dmap))
            u.write(
                "# Default map filter (0= All  1= Standard+Favorites  2= Favorites  3= Blacklisted) \n%s\n" % dmapfilter)
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

    # ---------------------------------------------------MAIN-------------------------------------------------------
    def clickfreq(self, ff):
        self.Button1.configure(state='normal')
        # self.Entry1.delete(0, 'end')

    def choosedfreq(self, ff):
        global frequency
        frequency = self.Entry1.get()

    def bwchoice(self, m):  # affects only the main window apparance, real-time
        global bw, lpcut, hpcut
        bw = self.TCombobox1.get()
        self.writelog("|<----" + str(int(bw)/2) + "Hz ----[tune frequency]---- " + str(int(bw)/2) + "Hz ---->|")
        lpcut = hpcut = int(bw) / 2

    def citychoice(self, m):  # affects only the main window apparance, real-time
        global city, citylat, citylon, selectedlat, selectedlon, selectedcity
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
        os.kill(proc2.pid, signal.SIGINT)
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

        if platform.system() == "Linux":
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


class MainW(Tk, object):

    def __init__(self):
        Tk.__init__(self)
        Tk.option_add(self, '*Dialog.msg.font', 'TkFixedFont 7')
        self.window = Zoom_Advanced(self)
        self.window2 = MainWindow(self)

if __name__ == '__main__':
    app = MainW()
    app.title(VERSION)
    app.mainloop()