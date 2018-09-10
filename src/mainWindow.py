#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import Frame, DoubleVar, Label, Entry, Button, Listbox, Text, Scrollbar, Menu, Message, Tk, IQfiles
import tkSimpleDialog
import tkFileDialog
import tkMessageBox
import signal
import glob
import re
import os
from shutil import copyfile
import time
from tkColorChooser import askcolor
from restart import Restart
from runUpdate import RunUpdate
from readKnownPointFile import ReadKnownPointFile
from zoomAdvanced import ZoomAdvanced
from readConfigFile import ReadConfigFile
from saveConfigFile import SaveConfigFile
from startKiwiSDR import StartKiwiSDR
from checkFileSize import CheckFileSize
from octaveProcessing import OctaveProcessing

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
        self.label0.configure(background=bgc, foreground=fgc, width=214)
        # legend
        self.label00 = Label(parent)
        self.label00.place(x=0, y=0, height=14, width=75)
        self.label00.configure(background="grey", font="TkFixedFont 7", anchor="w", fg="black", text="Legend:")
        self.label01 = Label(parent)
        self.label01.place(x=0, y=14, height=14, width=75)
        self.label01.configure(background="grey", font="TkFixedFont 7", anchor="w", fg=colorline[0], text="█ Standard")
        self.label02 = Label(parent)
        self.label02.place(x=0, y=28, height=14, width=75)
        self.label02.configure(background="grey", font="TkFixedFont 7", anchor="w", fg=colorline[1], text="█ Favorite")
        self.label03 = Label(parent)
        self.label03.place(x=0, y=42, height=14, width=75)
        self.label03.configure(background="grey", font="TkFixedFont 7", anchor="w", fg="red", text="█ Busy")
        self.label04 = Label(parent)
        self.label04.place(x=0, y=56, height=14, width=75)
        self.label04.configure(background="grey", font="TkFixedFont 7", anchor="w", fg="#001E00", text="█ no SNR data")

        numeric_entry_only = (self.register(self.numeric_only), '%S')
        self.Entry1 = Entry(parent, textvariable=frequency, validate='key', vcmd=numeric_entry_only)  # frequency box
        self.Entry1.place(relx=0.06, rely=0.892, height=24, relwidth=0.1)
        self.Entry1.configure(background="white", disabledforeground=dfgc, font="TkFixedFont", foreground=fgc,
                              insertbackground=fgc, width=214)
        #self.Entry1.bind('<FocusIn>', self.clickfreq)
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
        self.writelog("Thanks to Pierre (linkfanel) for his listing of available KiwiSDR nodes")
        self.writelog("Thanks to Marco (IS0KYB) for his SNR measurements listing of the KiwiSDR network")
        self.writelog(
            "Already computed TDoA runs : " + str([len(d) for r, d, folder in os.walk(os.path.join('TDoA', 'iq'))][0]))
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
        filemenu2.add_command(label="World (use with caution)",command=lambda *args: self.map_preset(13))
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
    1/ Hold Left-mouse button to move the World Map to your desired location
    2/ Enter the frequency, between 0 and 30000 (kHz)
    3/ Choose from the top bar menu a specific bandwidth for the IQ recordings if necessary
    4/ Choose KiwiSDR nodes by left-click on them and select \"Use:\" command to add them to the list (min=3 max=6)
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
    You can compute again your IQ recordings, to do so, just run the ./recompute.sh script
    
    The World map is not real-time, click UPDATE button to refresh, of course only GPS enabled nodes are displayed...

    Thanks to Christoph Mayer for the public release of his TDoA GNU-Octave scripts
    Thanks to John Seamons for including the GPS timestamps in IQ files
    Thanks to Dmitry Janushkevich for the original kiwirecorder project python scripts
    Thanks to Pierre Ynard (linkfanel) for the KiwiSDR network node listing used as source for GUI map update
    Thanks to Marco Cogoni (IS0KYB) for the KiwiSDR network SNR measurements listing used as source for GUI map update

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
            mapname = "maps/directTDoA_map_grayscale_dark.jpg"
        ReadConfigFile().read_cfg()
        SaveConfigFile().save_cfg("mapc", "maps/" + os.path.split(mapname)[1])
        Restart().run()

    def runupdate(self):  # if UPDATE button is pushed
        self.Button1.configure(state="disabled")
        self.Button2.configure(state="disabled")
        self.Button3.configure(state="disabled")
        RunUpdate(self).start()  # start the update thread

    # ---------------------------------------------------MAIN-----------------------------------------------------------

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
            elif len(namelist) < 3:  # debug
                self.writelog("ERROR: Select at least 3 nodes for TDoA processing !")
            else:
                frequency = str(float(self.Entry1.get()))
                self.Button1.configure(state="disabled")
                self.Button2.configure(state="normal")
                self.Button3.configure(state='disabled')
                for wavfiles in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
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
        for file in glob.glob(os.path.join('TDoA', 'iq') + os.sep + "*.wav"):
            IQfiles.append(os.path.split(file)[1])
        firstfile = IQfiles[0]
        varfile = str(firstfile.split("_", 2)[1].split("_", 1)[0])
        for i in range(len(IQfiles)):
            nbfile = len(IQfiles)
        self.writelog("IQ Recordings stopped...")
        self.Button2.configure(state="disabled")

        #  creating the .m file
        with open(os.path.join('TDoA') + os.sep + "proc_tdoa_" + varfile + ".m", "w") as g:
            g.write("## -*- octave -*-\n")
            g.write("## This file was auto-generated by " + VERSION + "\n\n")
            g.write("function [tdoa,input]=proc_tdoa_" + varfile + "\n\n")
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
/usr/bin/cp ./*.wav ../
/usr/bin/cp proc_tdoa_""" + varfile + """.m ../../
cd ../..
$EDITOR proc_tdoa_""" + varfile + """.m
octave-cli proc_tdoa_""" + varfile + """.m""")
            recompute.close()
            os.chmod(os.path.join('TDoA', 'iq') + os.sep + starttime + "_F" + str(
                frequency) + os.sep + "recompute.sh", 0o777)
        self.writelog("Running Octave process now... please wait")
        time.sleep(0.5)
        OctaveProcessing(self).start()