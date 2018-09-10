#!/usr/bin/python
# -*- coding: utf-8 -*-

class SaveConfigFile:

    def save_cfg(self, field, input):
        global dmap, mapfl, gpsfl, white, black, colorline
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