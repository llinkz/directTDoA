#!/bin/sh
python -m pip install numpy pillow requests pygame scipy
cd TDoA/kiwiclient
mkoctfile read_kiwi_iq_wav.cc
cd ../..
patch -i kiwiworker_patch.diff ./TDoA/kiwiclient/kiwiworker.py
patch -i plot_map_patch.diff ./TDoA/m/tdoa_plot_map.m
echo -e "The setup is now finished.\nTo start the software from console, type ./directTDoA.py"
sleep 5