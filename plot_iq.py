#!/usr/bin/python
# -*- coding: utf-8 -*-
""" This python script removes GNSS data from KiwiSDR IQ files then convert
them into png spectrogram pictures and then combines all of them in a single png file.
credits: Daniel Ekmann & linkz with some code source from James Gibbard / Maxim / Bernhard Wagner
usage ./plot_iq.py """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import struct
import os
import glob
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

GRADIENT = {
    'red': ((0.0, 0.0, 0.0),
            (0.077, 0.0, 0.0),
            (0.16, 0.0, 0.0),
            (0.265, 1.0, 1.0),
            (0.403, 1.0, 1.0),
            (0.604, 1.0, 1.0),
            (1.0, 1.0, 1.0)),

    'green': ((0.0, 0.0, 0.0),
              (0.077, 0.0, 0.0),
              (0.16, 1.0, 1.0),
              (0.265, 1.0, 1.0),
              (0.403, 0.0, 0.0),
              (0.604, 0.0, 0.0),
              (1.0, 0.764, 0.764)),

    'blue': ((0.0, 0.117, 0.117),
             (0.077, 1.0, 1.0),
             (0.16, 1.0, 1.0),
             (0.265, 0.0, 0.0),
             (0.403, 0.0, 0.0),
             (0.604, 1.0, 1.0),
             (1.0, 1.0, 1.0)),
}

COLORMAP = LinearSegmentedColormap('SAColorMap', GRADIENT, 1024)


def plotspectrogram(source):
    """ Create spectrogram of the IQ file, using specgram and save it to file. """
    old_f = open(source, 'rb')
    new_f = open(source + '.nogps', 'wb')
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
    with open(source + '.nogps', "rb") as no_gps:
        no_gps.seek(0, 0)
        data = np.fromfile(no_gps, dtype='int16')
        data = data[0::2] + 1j * data[1::2]
    # cmap = plt.get_cmap('bone')
    fig, a_x = plt.subplots()
    plt.specgram(data, NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)), noverlap=512, vmin=10,
                 vmax=200, cmap=COLORMAP)
    plt.title(
        source.rsplit("_", 3)[2] + " - [CF=" + str((float(wavfiles.rsplit("_", 3)[1]) / 1000)) + " kHz] - GPS:" + str(
            has_gps(source)))
    plt.xlabel("time (s)")
    plt.ylabel("frequency offset (kHz)")
    ticks = matplotlib.ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x // 1e3))
    a_x.yaxis.set_major_formatter(ticks)
    plt.savefig(source + '.png')
    os.remove(source + '.nogps')


def has_gps(source):
    """ Detect if IQ file has GPS GNSS data (in test). """
    f_src = open(source, 'rb')
    f_src.seek(2118)
    if sys.version_info[0] == 2:
        return ord(f_src.read(1)[0]) < 254
    return f_src.read(1)[0] < 254


def pil_grid(images, filename, max_horiz=np.iinfo(int).max):
    """ Make a poster of png files. """
    n_images = len(images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = [0] * n_horiz, [0] * ((n_images // n_horiz) + (1 if n_images % n_horiz > 0 else 0))
    for i, im_v1 in enumerate(images):
        h_var, v_var = i % n_horiz, i // n_horiz
        h_sizes[h_var] = max(h_sizes[h_var], im_v1.size[0])
        v_sizes[v_var] = max(v_sizes[v_var], im_v1.size[1])
    h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
    im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im_v2 in enumerate(images):
        im_grid.paste(im_v2, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    im_grid.save(filename, resolution=153.5)  # adjust res to ~900x600
    return im_grid


if __name__ == '__main__':

    plt.rcParams.update({'figure.max_open_warning': 0})
    COUNT = 1
    TOTALCOUNT = len(glob.glob("*.wav"))
    for wavfiles in glob.glob("*.wav"):
        print(str(COUNT) + "/" + str(TOTALCOUNT) + " ... [" + wavfiles.rsplit("_", 3)[2] + "]")
        plotspectrogram(wavfiles)
        COUNT += 1
    IMAGES = [Image.open(x) for x in glob.glob("*.png")]
    FINALNAME = 'TDoA_' + str(wavfiles.rsplit("_", 3)[1]) + '_spec.pdf'
    pil_grid(IMAGES, FINALNAME, 3)  # last parameter = the number of images displayed horizontally
    for imgfiles in glob.glob("*.wav.png"):
        os.remove(imgfiles)
