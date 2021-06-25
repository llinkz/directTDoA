#!/usr/bin/python
# -*- coding: utf-8 -*-
""" credits: Daniel Ekmann for core code & linkz for GUI code
usage ./trim_iq.py """

# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import subprocess
import struct
import os
import glob
import shutil
import platform
import sys
import argparse
import io
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import SpanSelector
from matplotlib.ticker import FuncFormatter

TRIM_PROC = 1
FILE_NUMBER = 0
TOTAL_FILES = len(glob.glob("*.wav"))
START = 0
FREQUENCY = float(os.getcwd().rsplit("F", 1)[1])
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


def on_press(event):
    """ Close IQ preview plot with mouse click. """

    plt.close()


def on_mouse_move(event):
    """ Range selection length measurement. """

    if None not in (event.xdata, event.ydata) and START != 0:
        if -2 <= round(event.xdata - START, 2) <= 2:
            span.set_visible(True)
            span2.set_visible(False)
        else:
            span.set_visible(False)
            span2.set_visible(True)


def on_mouse_click(event):
    """ First click on the spectrogram. """

    global START
    START = event.xdata


def onselect(event1, event2):
    """ Drag-select procedure on temp IQ stored in memory. """

    global START
    if float(event2 - event1) <= 2:
        print ("Period range is too small (less than 2 sec) - deleting " + IQfile)
        plt.close()
        os.remove(IQfile)
    START = 0


def onselect2(event10, event20):
    """ Drag-select procedure on temp IQ stored in memory. """

    global START
    if float(event20 - event10) > 2:
        trim_iq(round(event10, 2), round(event20, 2))
    START = 0


def trim_iq(from_block, to_block):
    """ Trim the original IQ file and save it. """

    global TRIM_PROC
    plt.close()
    block_duration = 512 / 12000.0
    from_idx = int(float(from_block) // block_duration)
    to_idx = int(float(to_block) // block_duration)
    old_f = open(IQfile, 'rb')
    new_f = io.BytesIO()
    new_f.write(b'RIFF')
    new_f.write(struct.pack('<i', (to_idx - from_idx + 1) * 2074 + 28))
    old_f.seek(8)
    new_f.write(old_f.read(28))
    for i in range(from_idx, to_idx + 1):
        old_f.seek(i * 2074 + 36)
        new_f.write(old_f.read(2074))
    old_f.close()
    new_f.seek(0)
    with open(IQfile, 'wb') as f_data:
        shutil.copyfileobj(new_f, f_data)
    # file result preview if requested by user
    if ARGS.get_preview == "y":
        TRIM_PROC = 0
        convert_iq_and_plot_from_mem(IQfile, FILE_NUMBER)
    else:
        TRIM_PROC = 1


def convert_iq_and_plot_from_mem(in_file, number):
    """ remove GNSS data from the IQ file and plot it from memory. """

    global TRIM_PROC, fig, a_x, span, span2
    # Remove GNSS data from the IQ file
    old_f = open(in_file, 'rb')
    old_size = os.path.getsize(in_file)
    data_size = 2048 * ((old_size - 36) // 2074)
    new_f = BytesIO()
    new_f.write(old_f.read(36))
    new_f.write(b'data')
    new_f.write(struct.pack('<i', data_size))
    for i in range(62, old_size, 2074):
        old_f.seek(i)
        new_f.write(old_f.read(2048))
    old_f.close()
    new_f.seek(0, 0)
    data = np.frombuffer(new_f.getvalue(), dtype='int16')
    data = data[0::2] + 1j * data[1::2]
    # Plot the IQ w/o GNSS data
    plt.rcParams['toolbar'] = 'None'
    fig, a_x = plt.subplots()
    plt.specgram(data, NFFT=1024, Fs=12000, window=lambda data: data * np.hanning(len(data)), noverlap=512, vmin=10,
                 vmax=200, cmap=COLORMAP)
    plt.xlabel("Time (s)")
    ticks = FuncFormatter(lambda x, pos: FREQUENCY + (x // 1e3))
    a_x.yaxis.set_major_formatter(ticks)
    a_x.set_ybound(-6000.0, 6000.0)
    if TRIM_PROC == 1:
        plt.title(in_file.rsplit("_", 2)[1] + " - [" + str(number) + "/" + str(TOTAL_FILES) + "]", fontsize=10)
        span = SpanSelector(a_x, onselect, 'horizontal', useblit=True, rectprops=dict(alpha=0.4, facecolor='red'))
        span2 = SpanSelector(a_x, onselect2, 'horizontal', useblit=True, rectprops=dict(alpha=0.4, facecolor='green'))
        fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)
        fig.canvas.mpl_connect('button_press_event', on_mouse_click)
    else:
        plt.gcf().set_facecolor("yellow")
        fig.canvas.mpl_connect('button_press_event', on_press)
        plt.title(in_file.rsplit("_", 2)[1] + " - [" + str(number) + "/" + str(
            TOTAL_FILES) + "]" + " - [trimmed IQ preview]", fontsize=10)
        TRIM_PROC = 1
    plt.show()


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Trim KiwiSDR IQ files.')
    PARSER.add_argument('-o', dest='get_original', action='store', choices=['y', 'n'], default='n',
                        help='Use original IQ files (default=no)')
    PARSER.add_argument('-v', dest='get_preview', action='store', choices=['y', 'n'], default='n',
                        help='Show preview window (default=no)')
    PARSER.add_argument('-p', dest='plot_iq', action='store', choices=['y', 'n'], default='n',
                        help='Run plot_iq script (default=yes)')
    PARSER.add_argument('-r', dest='show_result', action='store', choices=['y', 'n'], default='n',
                        help='Show plot_iq PDF result (default=yes)')
    ARGS = PARSER.parse_args()

    # Always do the backup of IQ files + spectrogram pdf (if present)
    if not os.path.isdir('./IQ'):
        os.makedirs("IQ")
        for OriginalIQfile in glob.glob("*.wav"):
            shutil.copyfile(OriginalIQfile, "IQ" + os.sep + OriginalIQfile)
        for SPECfile in glob.glob("*spec.pdf"):
            shutil.copyfile(SPECfile, "IQ" + os.sep + SPECfile)

    # Restore the IQ files if requested by user
    if ARGS.get_original == "y":
        for IQfile in glob.glob("IQ" + os.sep + "*.wav"):
            shutil.copyfile(IQfile, IQfile.rsplit(os.sep, 1)[1])

    # Compute all IQ files in the current directory
    for IQfile in glob.glob("*.wav"):
        FILE_NUMBER += 1
        convert_iq_and_plot_from_mem(IQfile, FILE_NUMBER)

    # Run plot_iq.py to get the spectrogram pdf file using the new trimmed files if requested by user
    if ARGS.plot_iq == "y":
        with open(os.devnull, 'w') as fp:
            subprocess.call([sys.executable, 'plot_iq.py'], shell=False, stdout=fp)

    # Show the spectrogram pdf file if requested by user
    if ARGS.show_result == "y":
        if platform.system() == "Windows":
            os.system('start' + ' TDoA_' + str(IQfile.rsplit("_", 3)[1]) + '_spec.pdf')
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", 'TDoA_' + str(IQfile.rsplit("_", 3)[1]) + '_spec.pdf'])
        else:
            subprocess.Popen(["xdg-open", 'TDoA_' + str(IQfile.rsplit("_", 3)[1]) + '_spec.pdf'])
