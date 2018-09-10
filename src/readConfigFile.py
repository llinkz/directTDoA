#!/usr/bin/python
# -*- coding: utf-8 -*-

class ReadConfigFile:

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
