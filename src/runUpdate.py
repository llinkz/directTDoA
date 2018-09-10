#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import requests
import json
import threading
import codecs
import os
from shutil import copyfile
from restart import Restart

class RunUpdate(threading.Thread):
    def __init__(self, parent=None):
        super(RunUpdate, self).__init__()
        self.parent = parent

    def run(self):
        try:
            nodelist = requests.get("http://rx.linkfanel.net/kiwisdr_com.js")  # getting the full KiwiSDR node list
            json_data = json.loads(nodelist.text[nodelist.text.find('['):].replace('},\n]\n;\n', '}]'))  # remove chars
            #json_data = json.loads(nodelist.text)  # when kiwisdr_com.js will be in real json format
            snrlist = requests.get("http://sibamanna.duckdns.org/snrmap_4bands.json")
            json_data2 = json.loads(snrlist.text)
            try:
                linkz_status = requests.get("http://linkz.ddns.net:8073/status", timeout=3)
                s_fix = re.search('fixes_min=(.*)', linkz_status.text)
                l_fixes = s_fix.group(1)
            except:
                l_fixes = 0
                pass
            if os.path.isfile('directTDoA_server_list.db') is True:
                os.remove('directTDoA_server_list.db')
            with codecs.open('directTDoA_server_list.db', 'w', encoding='utf8') as g:
                g.write("[\n")
                for i in range(len(json_data)):  # parse all nodes
                    if 'fixes_min' in json_data[i] and 'GPS' in json_data[i]['sdr_hw']:  # parse only GPS nodes
                        for index, element in enumerate(json_data2['features']):  # check IS0KYB db
                            if json_data[i]['id'] in json.dumps(json_data2['features'][index]):
                                if json_data[i]['tdoa_id'] == '':
                                    node_id = json_data[i]['url'].split('//', 1)[1].split(':', 1)[0].replace(".", "").replace("-", "")
                                    try:
                                        ipfield = re.search(
                                            r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b',
                                            json_data[i]['url'].split('//', 1)[1].split(':', 1)[0])
                                        node_id = "ip" + str(ipfield.group(1)).replace(".", "")
                                    except:
                                        pass
                                    try:
                                        hamcallfield = re.search(
                                            r"(.*)(\s|,|\/|^)([A-Za-z]{1,2}[0-9][A-Za-z]{1,3})(\s|,|\/|\@|\-)(.*)",
                                            json_data[i]['name'])
                                        node_id = hamcallfield.group(3).upper()
                                    except:
                                        pass
                                else:
                                    node_id = json_data[i]['tdoa_id']
                                try:
                                    gpsfield = re.search(
                                        r"([-+]?[0-9]{1,2}(\.[0-9]*)?)(,| ) ?([-+]?[0-9]{1,3}(\.[0-9]*))?",
                                        json_data[i]['gps'][1:-1])
                                    nodelat = gpsfield.group(1)
                                    nodelon = gpsfield.group(4)
                                except:
                                    # Admins not respecting KiwiSDR admin page GPS field format (nn.nnnnnn, nn.nnnnnn)
                                    # => nodes will be shown at top-right map edge, as it fails the update code process
                                    print "*** Error reading <gps> field : >> " + str(unicodedata.normalize("NFKD", json_data[i]['gps'][1:-1]).encode("ascii", "ignore")) + " << for \"" + unicodedata.normalize("NFKD", json_data[i]["name"]).encode("ascii", "ignore") + "\""
                                    print "*** This node will be displayed at 90N 180E position and is not usable for TDoA"
                                    nodelat = "90"
                                    nodelon = "180"
                                # (-?(90[:°d] * 00[:\'\'m]*00(\.0+)?|[0-8][0-9][ :°d]*[0-5][0-9][ :\'\'m]*[0-5][0-9](\.\d+)?)[ :\?\"s]*(N|n|S|s)?)[ ,]*(-?(180[ :°d]*00[ :\'\'m]*00(\.0+)?|(1[0-7][0-9]|0[0-9][0-9])[ :°d]*[0-5][0-9][ :\'\'m]*[0-5][0-9](\.\d+)?)[ :\?\"s]*(E|e|W|w)?)
                                g.write(' { \"mac\":\"' + json_data[i]['id'] + '\", \"url\":\"' + json_data[i]['url'].split('//', 1)[1] + '\", \"gps\":\"' + json_data[i]['fixes_min'] + '\", \"id\":\"' + node_id + '\", \"lat\":\"' + nodelat + '\", \"lon\":\"' + nodelon + '\", \"name\":\"' + unicodedata.normalize("NFKD", json_data[i]["name"]).encode("ascii", "ignore") + '\", \"users\":\"' + json_data[i]['users'] + '\", \"usersmax\":\"' + json_data[i]['users_max'] + '\", \"snr1\":\"' + str(element['properties']['snr1_avg']) + '\", \"snr2\":\"' + str(element['properties']['snr2_avg']) + '\", \"snr3\":\"' + str(element['properties']['snr3_avg']) + '\", \"snr4\":\"' + str(element['properties']['snr4_avg']) + '\", \"nlvl1\":\"' + str(element['properties']['bg1_avg']) + '\", \"nlvl2\":\"' + str(element['properties']['bg2_avg']) + '\", \"nlvl3\":\"' + str(element['properties']['bg3_avg']) + '\", \"nlvl4\":\"' + str(element['properties']['bg4_avg']) + '\"},\n')
                            else:
                                pass
                    else:
                        pass
                # here is the hardcode for my own KiwiSDR, it will soon include real SNR/noise values.. thx Marco
                g.write(' { "mac":"04a316df1bca", "url":"linkz.ddns.net:8073", "gps":"' + str(l_fixes) + '", "id":"linkz", "lat":"45.4", "lon":"5.3", "name":"directTDoA GUI developer, French Alps", "users":"0", "usersmax":"4", "snr1":"0", "snr2":"0", "snr3":"0", "snr4":"0", "nlvl1":"0", "nlvl2":"0", "nlvl3":"0", "nlvl4":"0"}\n]')
                g.close()
                # normally if update process is ok, we can make a backup copy of the server listing
                copyfile("directTDoA_server_list.db", "directTDoA_server_list.db.bak")
                Restart().run()
        except Exception as e:
            print e
            print "UPDATE FAIL, sorry"
