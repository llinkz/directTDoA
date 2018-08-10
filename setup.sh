#!/bin/sh
python -m pip install numpy pillow
cd TDoA/kiwiclient
mkoctfile read_kiwi_iq_wav.cc
cd ../m
patch -i ../../nopng.diff tdoa_plot_map.m
cd ../..