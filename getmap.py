#!/usr/bin/python
# -*- coding: utf-8 -*-
""" get mapbox files, draw POIs and merge to pdf. (linkz 2019)
usage: ./getmap.py <TDoA-LAT> <TDoA-LON> <known-LAT> <known-LON> <map-style> <filename>
known bug: maximum 24 mapmarkers are allowed at this time : fixed for IQ recordings < 22 """

import sys
import os
import json
import glob
import re
import threading
import requests
import shutil
from io import BytesIO
if sys.version_info[0] == 2:
    import urllib
else:
    import urllib.parse

from PIL import Image, ImageDraw, ImageFont

# Mapbox map styles :
# streets-v11 / outdoors-v11 / light-v10 / dark-v10
# satellite-v9 / satellite-streets-v11
# navigation-preview-day-v4 / navigation-preview-night-v4
# navigation-guidance-day-v4 / navigation-guidance-night-v4

map_token = "pk.eyJ1IjoibGxpbmt6IiwiYSI6ImNrM3JzMzE4ZTBlY3gzZXM1MnR5ODZrcnAifQ.fdqW8wmA7qhPYzFsGufZXg"
data_l = []
nb_of_file = 0
mapbox_zoom = {'2': [0, 0], '4': [900, 0], '6': [0, 600], '8': [900, 600]}
nb_of_nodes = len(glob.glob1(sys.argv[6].rsplit(os.sep, 1)[0], "*.wav"))
fnt = ImageFont.truetype('Pillow/Tests/fonts/DejaVuSans.ttf', 18)
new_image = Image.new("RGB", (1800, 1200))

for wavfiles in glob.glob(sys.argv[6].rsplit(os.sep, 1)[0] + os.sep + "*.wav"):
    for gnssfiles in glob.glob("gnss_pos/*.txt"):
        if wavfiles.rsplit("_", 2)[1] + ".txt" == gnssfiles.rsplit(os.sep, 2)[1]:
            data_latlon = {}
            filent2 = open("gnss_pos/" + gnssfiles.rsplit(os.sep, 2)[1], 'r')
            data2 = filent2.readlines()
            data_latlon['lon'] = data2[0].rsplit("[", 1)[1].rsplit("]", 1)[0].rsplit(",", 1)[1]
            data_latlon['lat'] = data2[0].rsplit("[", 1)[1].rsplit("]", 1)[0].rsplit(",", 1)[0]
            data_latlon['size'] = "small"
            data_latlon['symbol'] = "triangle"
            filent = open(os.getcwd() + os.sep + "proc_tdoa_" +
                          str(float(sys.argv[6].rsplit("_F", 1)[1].rsplit("/", 1)[0]) * 1000).rsplit(".", 1)[0] + ".m",
                          'r')
            if wavfiles.rsplit("_", 2)[1] in filent.read():
                data_latlon['color'] = "#ff0"
                data_l.append(data_latlon)
            elif nb_of_nodes <= 22:
                data_latlon['color'] = "#999"
                data_l.append(data_latlon)

# TDoA coordinates and style
data_latlon = dict()
data_latlon['lon'] = sys.argv[2]
data_latlon['lat'] = sys.argv[1]
data_latlon['size'] = "medium"
data_latlon['color'] = "#d00"
data_latlon['symbol'] = ""
data_l.append(data_latlon)

# Known point coordinates and style (if filled)
if sys.argv[3] != "0" and sys.argv[4] != "0":
    data_latlon = dict()
    data_latlon['lon'] = sys.argv[4]
    data_latlon['lat'] = sys.argv[3]
    data_latlon['size'] = "small"
    data_latlon['color'] = "#f70"
    data_latlon['symbol'] = "star"
    data_l.append(data_latlon)

# Mapbox's geojson maker
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [d["lon"], d["lat"]],
            },
            "properties": {
                "marker-size": d["size"],
                "marker-color": d["color"],
                "marker-symbol": d["symbol"]
            },
        } for d in data_l]
}

# Remove double-quotes on coordinates and convert json to url-style
geojson = re.sub('\"(-?\d+(\.\d+)?)\"', r'\1', json.dumps(geojson))
if sys.version_info[0] == 2:
    geojson = urllib.quote(geojson)
else:
    geojson = urllib.parse.quote(geojson)


class CurlCmd(threading.Thread):
    """ Curl processing routine """

    def __init__(self, zooming=None, x=None, y=None):
        super(CurlCmd, self).__init__()
        self.zoom2 = zooming
        self.x_pos = x
        self.y_pos = y

    def run(self):
        global nb_of_file
        r = requests.get("https://api.mapbox.com/styles/v1/mapbox/" +
                         sys.argv[5] + "/static/geojson(" + geojson + ')/' +
                         sys.argv[2] + ',' + sys.argv[1] + "," + self.zoom2 + "/900x600?access_token=" +
                         map_token, timeout=2, stream=True)
        if r.status_code == 200:
            new_pic = BytesIO()
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, new_pic)
            img = Image.open(new_pic)
            new_image.paste(img, (self.x_pos, self.y_pos))
            nb_of_file += 1
            if nb_of_file == 4:
                draw = ImageDraw.Draw(new_image)
                draw.line((900, 0, 900, 1200), fill="#000")
                draw.line((0, 600, 1800, 600), fill="#000")
                text_length = 10.5 * len(sys.argv[1] + " " + sys.argv[2])
                draw.polygon([(395, 255), (395, 235), (395 + text_length, 235), (395 + text_length, 255)], fill="#222")
                draw.polygon([(1295, 255), (1295, 235), (1295 + text_length, 235), (1295 + text_length, 255)],
                             fill="#222")
                draw.polygon([(395, 855), (395, 835), (395 + text_length, 835), (395 + text_length, 855)], fill="#222")
                draw.polygon([(1295, 855), (1295, 835), (1295 + text_length, 835), (1295 + text_length, 855)],
                             fill="#222")
                [(draw.text((x, y), sys.argv[1] + " " + sys.argv[2], fill="#fff", font=fnt)) for x in [400, 1300] for y
                 in [235, 835]]
                new_image.save(sys.argv[6].replace("_[[]", "_[").replace("[]]_", "]_").replace(".png", ".pdf"), "PDF",
                               resolution=144, append_images=[new_image])


if sys.version_info[0] == 2:
    for zoom, placement in mapbox_zoom.iteritems():
        CurlCmd(zoom, placement[0], placement[1]).start()
else:
    for zoom, placement in mapbox_zoom.items():
        CurlCmd(zoom, placement[0], placement[1]).start()
