#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

class ReadKnownPointFile:

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
