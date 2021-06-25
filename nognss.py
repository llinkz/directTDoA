#!/usr/bin/python
# -*- coding: utf-8 -*-
""" This python script removes GNSS data from KiwiSDR IQ files
credits: Daniel Ekmann & linkz
usage ./plot_iq.py """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import struct
import os
import glob


def removegnss(source):
    """ Removes GNSS from the KiwiSDR original IQ file and save it as standard wav. """
    old_f = open(source, 'rb')
    new_f = open(source + '.nogps.wav', 'wb')
    old_size = os.path.getsize(source)
    data_size = 2048 * ((old_size - 36) // 2074)
    new_f.write(old_f.read(36))
    new_f.write(b'data')
    new_f.write(struct.pack('<i', data_size))
    for i in range(62, old_size, 2074):
        old_f.seek(i)
        new_f.write(old_f.read(2048))
    new_f.close()
    old_f.close()


if __name__ == '__main__':

    COUNT = 1
    TOTALCOUNT = len(glob.glob("*.wav"))
    for wavfiles in glob.glob("*.wav"):
        print(str(COUNT) + "/" + str(TOTALCOUNT) + " ... [" + wavfiles.rsplit("_", 3)[2] + "]")
        removegnss(wavfiles)
        COUNT += 1
