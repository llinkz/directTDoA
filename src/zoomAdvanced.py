#!/usr/bin/python
# -*- coding: utf-8 -*-
from Tkinter import *
import tkMessageBox
import os
import webbrowser
from PIL import Image, ImageTk
from readConfigFile import ReadConfigFile
from fillMapWithNodes import FillMapWithNodes
from restart import Restart

class ZoomAdvanced(Frame):  # src stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan?noredirect=1&lq=1 :)
    def __init__(self, parent):
        Frame.__init__(self, parent=None)
        self.app = parent
        self.app.geometry("1200x700+150+10")
        self.dx0 = "0"
        self.dx1 = "0"
        self.dy0 = "0"
        self.dy1 = "0"
        
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
        self.canvas.scan_dragto(-int(self.dx0.split('.')[0]), -int(self.dy0.split('.')[0]), gain=1)  # adjust map pos.
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
            tkMessageBox.showinfo("TDoA map boundaries :",
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
        host = self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0]
        self.menu = Menu(self, tearoff=0, fg="black", bg="grey", font='TkFixedFont 7')
        #  host.rsplit("$", 14)[#] <<
        #  0=host  1=id  2=short name  3=name  4=users  5=users max  6=GPS fix/min
        #  7=SNR 0-2 MHz  8=SNR 2-10 MHz  9=SNR 10-20 MHz  10=SNR 20-30 MHz
        #  11=Noise 0-2 MHz  12=Noise 2-10 MHz 13=Noise 10-20 MHz  14=Noise 20-30 MHz
        temp_snr_avg = (int(host.rsplit("$", 14)[7]) + int(host.rsplit("$", 14)[8]) + int(
            host.rsplit("$", 14)[9]) + int(host.rsplit("$", 14)[10])) / 4
        temp_noise_avg = (int(host.rsplit("$", 14)[11]) + int(host.rsplit("$", 14)[12]) + int(
            host.rsplit("$", 14)[13]) + int(host.rsplit("$", 14)[14])) / 4
        font_snr1 = font_snr2 = font_snr3 = font_snr4 = 'TkFixedFont 7'
        if int(host.rsplit("$", 14)[4]) / int(host.rsplit("$", 14)[5]) == 0:  # node is available
            # color gradiant below depending on SNR average
            self.menu.add_command(
                label="Add " + str(host).rsplit("$", 14)[2] + " for TDoA process [" + host.rsplit("$", 14)[
                    6] + " GPS fix/min] [" + str(host.rsplit("$", 14)[4]) + "/" + str(
                    host.rsplit("$", 14)[5]) + " users]",
                background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                command=self.populate)
            self.menu.add_command(label=str(host.rsplit("$", 14)[3]).replace("_", " "), state=NORMAL,
                                  background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                                  foreground=self.get_font_color(
                                      (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))), command=None)
            try:
                self.menu.add_command(
                    label="Open \"" + str(host).rsplit("$", 14)[0] + "/f=" + str(frequency.get()) + "iqz8\" in browser",
                    state=NORMAL, background=(self.color_variant(colorline[0], (int(temp_snr_avg) - 50) * 5)),
                    foreground=self.get_font_color((self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))),
                    command=self.openinbrowser)
                if frequency.get() <= 2000:
                    font_snr1 = 'TkFixedFont 8 bold'
                elif 2001 < frequency.get() <= 10000:
                    font_snr2 = 'TkFixedFont 8 bold'
                elif 10000 < frequency.get() <= 20000:
                    font_snr3 = 'TkFixedFont 8 bold'
                elif 20000 < frequency.get() <= 30000:
                    font_snr4 = 'TkFixedFont 8 bold'
            except ValueError:
                pass
        else:  # node is busy
            self.menu.add_command(label=str(host).rsplit("$", 14)[2] + " is busy, sorry. [" + host.rsplit("$", 14)[
                6] + " GPS fix/min] [" + str(host.rsplit("$", 14)[4]) + "/" + str(host.rsplit("$", 14)[5]) + " users]",
                                  background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                  foreground=self.get_font_color(
                                      (self.color_variant("#FFFF00", (int(temp_snr_avg) - 50) * 5))), command=None)
            self.menu.add_command(label=str(host.rsplit("$", 14)[3]).replace("_", " "), state=NORMAL,
                                  background=(self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5)),
                                  foreground=self.get_font_color(
                                      (self.color_variant("#FF0000", (int(temp_snr_avg) - 50) * 5))), command=None)

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
            self.menu.add_command(label="add to blacklist", command=self.addblacklist)

        # self.menu.add_command(label="check SNR", state=DISABLED, command=self.displaySNR)  # for next devel
        # if snrcheck == True:
        #     print "SNR requested on " + str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     print snrfreq
        #     snrhost = str(self.canvas.gettags(self.canvas.find_withtag(CURRENT))[0].rsplit(':')[0])
        #     SnrProcessing(self).start()
        #     app.title("Checking SNR for" + str(snrhost) + ". Please wait")

        self.menu.post(event.x_root, event.y_root)

    def get_font_color (self, ff):  # adapting the font color regarding background luminosity
        # stackoverflow.com/questions/946544/good-text-foreground-color-for-a-given-background-color/946734#946734
        rgb_hex = [ff[x:x + 2] for x in [1, 3, 5]]
        if int(rgb_hex[0], 16)*0.299 + int(rgb_hex[1], 16)*0.587 + int(rgb_hex[2], 16)*0.114 > 186:
            return "#000000"
        else:
            return "#FFFFFF"
        # if (red*0.299 + green*0.587 + blue*0.114) > 186 use #000000 else use #ffffff
        pass

    def convert_dbm_to_smeter (self, dbm):
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
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already in the favorite list !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (self.dx0, self.dy0, self.dx1, self.dy1))
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
            u.write("# Default map geometry \n%s,%s,%s,%s" % (self.dx0, self.dy0, self.dx1, self.dy1))
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
        if host.rsplit('$', 14)[1] in black:
            tkMessageBox.showinfo(title="  ¯\_(ツ)_/¯ ",
                                  message=str(host.rsplit(':')[0]) + " is already blacklisted !")
        else:
            os.remove('directTDoA.cfg')
            with open('directTDoA.cfg', "w") as u:
                u.write("# Default map geometry \n%s,%s,%s,%s" % (self.dx0, self.dy0, self.dx1, self.dy1))
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
            u.write("# Default map geometry \n%s,%s,%s,%s" % (self.dx0, self.dy0, self.dx1, self.dy1))
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
            url = "http://" + str(host).rsplit("$", 14)[0] + "/?f=" + str(frequency.get()) + "iqz8"
            webbrowser.open_new(url)
        else:
            url = "http://" + str(host).rsplit("$", 14)[0]
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
