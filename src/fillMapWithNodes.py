#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import threading

class FillMapWithNodes(threading.Thread):

    def __init__(self, parent=None):
        super(FillMapWithNodes, self).__init__()
        self.parent = parent

    def run(self):
        global manual_bound_x, manual_bound_y, manual_bound_xsize, manual_bound_ysize, map_preset, map_manual
        if os.path.isfile('directTDoA_server_list.db') is True:
            with open('directTDoA_server_list.db') as f:
                db_data = json.load(f)
                for i in range(len(db_data)):
                    try:
                        if (int(db_data[i]["users"])) / (int(db_data[i]["usersmax"])) == 0:  # OK slots available
                            temp_snr_avg = (int(db_data[i]["snr1"]) + int(db_data[i]["snr2"]) + int(
                                db_data[i]["snr3"]) + int(db_data[i]["snr4"])) / 4
                            if db_data[i]["mac"] in white:    # favorite node color
                                node_color = (self.color_variant(colorline[1], (int(temp_snr_avg) - 45) * 5))
                            elif db_data[i]["mac"] in black:  # blacklist node color
                                node_color = (self.color_variant(colorline[2], (int(temp_snr_avg) - 45) * 5))
                            else:                             # standard node color
                                node_color = (self.color_variant(colorline[0], (int(temp_snr_avg) - 45) * 5))
                        else:
                            node_color = 'red'  # if no slots available, map point is always created red
                    except Exception as e:
                        pass
                    try:
                        if mapfl == "1" and db_data[i]["mac"] not in black:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "2" and db_data[i]["mac"] in white:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "3" and db_data[i]["mac"] in black:
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                        elif mapfl == "0":
                            self.add_point(self.convert_lat(db_data[i]["lat"]), self.convert_lon(db_data[i]["lon"]),
                                           node_color, db_data[i]["url"], db_data[i]["mac"], db_data[i]["id"],
                                           db_data[i]["name"].replace(" ", "_").replace("!", "_"), db_data[i]["users"],
                                           db_data[i]["usersmax"], db_data[i]["gps"], db_data[i]["snr1"],
                                           db_data[i]["snr2"], db_data[i]["snr3"], db_data[i]["snr4"],
                                           db_data[i]["nlvl1"], db_data[i]["nlvl2"], db_data[i]["nlvl3"],
                                           db_data[i]["nlvl4"])
                    except Exception as e:
                        print e
                        pass
        self.parent.canvas.scan_dragto(-int(dx0.split('.')[0]), -int(dy0.split('.')[0]), gain=1)  # adjust map pos.
        self.parent.show_image()

    def convert_lat(self, lat):
        if float(lat) > 0:  # nodes are between LATITUDE 0 and 90N
            return 987.5 - (float(lat) * 11)
        else:  # nodes are between LATITUDE 0 and 60S
            return 987.5 + (float(0 - float(lat)) * 11)

    def convert_lon(self, lon):
        return (1907.5 + ((float(lon) * 1910) / 180))

    def color_variant(self, hex_color, brightness_offset=1):
        # source : https://chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html
        rgb_hex = [hex_color[x:x + 2] for x in [1, 3, 5]]
        new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
        new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
        return "#" + "".join(["0" + hex(i)[2:] if len(hex(i)[2:]) < 2 else hex(i)[2:] for i in new_rgb_int])

    def add_point(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r):
        global gpsfl
        #  a   b    c    d   e   f   g    h     i     j   k    l    m    n    o   p   q   r
        # lon lat color host mac id name user usermx gps snr1 snr2 snr3 snr4 bg1 bg2 bg3 bg4
        if int(j) >= int(gpsfl):  # GPS/min filter
            try:
                self.parent.canvas.create_rectangle(float(b), float(a), float(b) + 5, float(a) + 5, fill=str(c),
                                                    outline="black", activefill='white', tag=str(
                        '$'.join(map(str, [d, e, f, g, h, i, j, k, l, m, n, o, p, q, r]))))
                self.parent.canvas.tag_bind(str('$'.join(map(str, [d, e, f, g, h, i, j, k, l, m, n, o, p, q, r]))),
                                            "<Button-1>", self.parent.onClick)
            except Exception as error_add_point:
                print error_add_point

    def deletePoint(self, n):  # city/site map point deletion process
        self.parent.canvas.delete(self.parent, n.rsplit(' (')[0])


