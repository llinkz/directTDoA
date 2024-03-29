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
import shutil
import platform
from io import BytesIO
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
if sys.version_info[0] == 2:
    import urllib
else:
    import urllib.parse

# <map-style> :
# streets-v11 / outdoors-v11 / light-v10 / dark-v10
# satellite-v9 / satellite-streets-v11
# navigation-preview-day-v4 / navigation-preview-night-v4
# navigation-guidance-day-v4 / navigation-guidance-night-v4

MAP_TOK = "Your_Mapbox_token_here"
DATA_L = []
MAPBOX_ZOOM = {'2': [0, 0], '4': [900, 0], '6': [0, 600], '8': [900, 600]}
NB_OF_NODES = len(glob.glob1(sys.argv[6].rsplit(os.sep, 1)[0], "*.wav"))
NB_OF_FILES = 0
if platform.system() == "Windows":
    FONT = ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf', 18)
else:
    FONT = ImageFont.truetype('Pillow/Tests/fonts/DejaVuSans.ttf', 18)
NEW_IMAGE = Image.new("RGB", (1800, 1200))

for wavfiles in glob.glob(sys.argv[6].rsplit(os.sep, 1)[0] + os.sep + "*.wav"):
    for gnssfiles in glob.glob("gnss_pos/*.txt"):
        if wavfiles.rsplit("_", 2)[1] + ".txt" == gnssfiles.rsplit(os.sep, 2)[1]:
            DATA_LATLON = {}
            filent2 = open("gnss_pos/" + gnssfiles.rsplit(os.sep, 2)[1], 'r')
            data2 = filent2.readlines()
            DATA_LATLON['lon'] = data2[0].rsplit("[", 1)[1].rsplit("]", 1)[0].rsplit(",", 1)[1]
            DATA_LATLON['lat'] = data2[0].rsplit("[", 1)[1].rsplit("]", 1)[0].rsplit(",", 1)[0]
            DATA_LATLON['size'] = "small"
            DATA_LATLON['symbol'] = "triangle"
            filent = open(os.getcwd() + os.sep + sys.argv[7], 'r')
            if wavfiles.rsplit("_", 2)[1] in filent.read():
                DATA_LATLON['color'] = "#ff0"
                DATA_L.append(DATA_LATLON)
            elif NB_OF_NODES <= 22:
                DATA_LATLON['color'] = "#999"
                DATA_L.append(DATA_LATLON)

# TDoA coordinates and style
DATA_LATLON = dict()
DATA_LATLON['lon'] = sys.argv[2]
DATA_LATLON['lat'] = sys.argv[1]
DATA_LATLON['size'] = "medium"
DATA_LATLON['color'] = "#d00"
DATA_LATLON['symbol'] = ""
DATA_L.append(DATA_LATLON)

# Known point coordinates and style (if filled)
if sys.argv[3] != "0" and sys.argv[4] != "0":
    DATA_LATLON = dict()
    DATA_LATLON['lon'] = sys.argv[4]
    DATA_LATLON['lat'] = sys.argv[3]
    DATA_LATLON['size'] = "small"
    DATA_LATLON['color'] = "#f70"
    DATA_LATLON['symbol'] = "star"
    DATA_L.append(DATA_LATLON)

# Mapbox's geojson maker
GEOJSON = {
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
        } for d in DATA_L]
}

# Remove double-quotes on coordinates and convert json to url-style
GEOJSON = re.sub(r'\"(-?\d+(\.\d+)?)\"', r'\1', json.dumps(GEOJSON))
if sys.version_info[0] == 2:
    GEOJSON = urllib.quote(GEOJSON)
else:
    GEOJSON = urllib.parse.quote(GEOJSON)


def haversine_distance(lat1, lon1, lat2, lon2):
    """ code source from Dario Radečić https://medium.com/@radecicdario
    https://towardsdatascience.com/heres-how-to-calculate-distance-between-2-geolocations-in-python-93ecab5bbba4 """
    r = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
    res = r * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
    return np.round(res, 2)


class GetMaps(threading.Thread):
    """ Curl processing routine """

    def __init__(self, zooming=None, x=None, y=None):
        super(GetMaps, self).__init__()
        self.zoom2 = zooming
        self.x_pos = x
        self.y_pos = y

    def run(self):
        global NB_OF_FILES
        req = requests.get(
            "https://api.mapbox.com/styles/v1/mapbox/" + sys.argv[5] + "/static/geojson(" + GEOJSON + ')/' + sys.argv[
                2] + ',' + sys.argv[1] + "," + self.zoom2 + "/900x600?access_token=" + MAP_TOK, timeout=2,
            stream=True)
        if req.status_code == 200:
            new_pic = BytesIO()
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, new_pic)
            img = Image.open(new_pic)
            NEW_IMAGE.paste(img, (self.x_pos, self.y_pos))
            NB_OF_FILES += 1
            if NB_OF_FILES == 4:
                draw = ImageDraw.Draw(NEW_IMAGE)
                text_length = 10.5 * len(sys.argv[1] + " " + sys.argv[2])
                draw.polygon([(395, 255), (395, 235), (395 + text_length, 235), (395 + text_length, 255)], fill="#222")
                draw.polygon([(1295, 255), (1295, 235), (1295 + text_length, 235), (1295 + text_length, 255)],
                             fill="#222")
                draw.polygon([(395, 855), (395, 835), (395 + text_length, 835), (395 + text_length, 855)], fill="#222")
                draw.polygon([(1295, 855), (1295, 835), (1295 + text_length, 835), (1295 + text_length, 855)],
                             fill="#222")
                [(draw.text((x, y), sys.argv[1] + " " + sys.argv[2], fill="#fff", font=FONT)) for x in [400, 1300] for y
                 in [235, 835]]
                # distance between most likely & known point red rectangle label
                if sys.argv[3] != "-90" and sys.argv[4] != "180":
                    distance = "Distance between TDoA most likely location and map marker = " + str(
                        haversine_distance(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]),
                                           float(sys.argv[4]))) + " km"
                    draw.polygon([(0, 0), (900, 0), (900, 20), (0, 20)], fill="#FFF")
                    draw.text((0, 0), distance, fill="#000", font=FONT)
                draw.line((900, 0, 900, 1200), fill="#000")
                draw.line((0, 600, 1800, 600), fill="#000")
                NEW_IMAGE.save(sys.argv[6].replace("_[[]", "_[").replace("[]]_", "]_").replace(".png", ".pdf"), "PDF",
                               resolution=144, append_images=[NEW_IMAGE])
        else:
            img = Image.new('RGB', (900, 600), (255, 255, 255))
            NEW_IMAGE.paste(img, (self.x_pos, self.y_pos))
            NB_OF_FILES += 1
            if NB_OF_FILES == 4:
                draw = ImageDraw.Draw(NEW_IMAGE)
                draw.text((15, 15), "Error: unable to get maps, check Mapbox token", (0, 0, 0), font=FONT)
                NEW_IMAGE.save(sys.argv[6].replace("_[[]", "_[").replace("[]]_", "]_").replace(".png", ".pdf"), "PDF",
                               resolution=144, append_images=[NEW_IMAGE])


if sys.version_info[0] == 2:
    for zoom, placement in MAPBOX_ZOOM.iteritems():
        GetMaps(zoom, placement[0], placement[1]).start()
else:
    for zoom, placement in MAPBOX_ZOOM.items():
        GetMaps(zoom, placement[0], placement[1]).start()
