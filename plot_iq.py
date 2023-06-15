#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Removes GNSS datas from KiwiSDR IQ files, do a SNR check and plot all into a single .pdf file.
credits: Daniel Ekmann & linkz - usage ./plot_iq.py """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import glob
import math
import os
import re
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr
# import matplotlib.ticker as tkr

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
COLORMAP = clr.LinearSegmentedColormap('SAColorMap', GRADIENT, 1024)


def load(path):
    """ IQ loading. """
    buf = BytesIO()
    with open(path, 'rb') as iq_file:
        size = os.path.getsize(path)
        for i in range(62, size, 2074):
            iq_file.seek(i)
            buf.write(iq_file.read(2048))
    data = np.frombuffer(buf.getvalue(), dtype='int16')
    data = data[0::2] + 1j * data[1::2]
    return data


def score(data):
    """ SNR scoring. """
    max_snr = 0.0
    for offset in range(12000, len(data), 512):
        snr = np.std(np.fft.fft(data[offset:], n=1024))
        if snr > max_snr:
            max_snr = snr
    return max_snr


def plot(files, order, cols):
    """ Plotting. """
    rows = int(math.ceil(len(files) / cols))
    fig, axs = plt.subplots(ncols=cols, nrows=rows)
    fig.set_figwidth(cols * 6.4)
    fig.set_figheight(rows * 4.8)
    for i, (path, _) in enumerate(order):
        a_x = axs.flat[i]
        a_x.specgram(files[path], NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)), noverlap=512,
                     vmin=10, vmax=200, cmap=COLORMAP)
        a_x.set_title(path.rsplit('_', 3)[2])
        a_x.axes.get_yaxis().set_visible(False)
        # a_x.get_yaxis().set_major_formatter(tkr.FuncFormatter(lambda x, pos: '{0:g}'.format(x // 1e3)))
        # a_x.set_ybound(-6000.0, 6000.0)
    for i in range(len(scores), len(axs.flat)):
        fig.delaxes(axs.flat[i])
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    for mfile in glob.glob('*.*m*'):
        oct_file = open(mfile, 'r')
        file_d = oct_file.read()
        oct_file.close()
        fig.suptitle(re.search(r".+title.+\'(.+)\'", file_d).group(1), fontsize=20)
    fig.savefig('TDoA_' + path.rsplit('_', 3)[1] + '_spectrogram.pdf', bbox_inches='tight', dpi=50)


if __name__ == '__main__':
    files = {path: load(path) for path in glob.glob('*.wav*')}
    scores = sorted([(path, score(data)) for path, data in files.items()], key=lambda item: item[1], reverse=True)
    plot(files, scores, cols=3)
