#!/bin/sh
echo "1/3 Upgrading python pip and installing python modules"
sudo python -m pip install --upgrade pip
python -m pip install Pillow requests matplotlib numpy future
echo "2/3 Compilating TDoA binaries and installing packages for GNU Octave"
cd TDoA/src
patch -i ../../json_save_patch.diff json_save_cc.cc
rm -f ../../json_save_patch.diff
mkoctfile json_save_cc.cc
mkoctfile read_kiwi_iq_wav.cc
mv json_save_cc.oct read_kiwi_iq_wav.oct ../oct
octave --silent --eval "pkg install -forge control signal"
octave --silent --eval "pkg load signal"
octave --silent --eval "pkg list"
cd ../..
echo "3/3 Patching some python and GNU Octave files"
patch -i kiwiworker_patch.diff ./kiwiclient/kiwi/worker.py
patch -i kiwiclient_patch.diff ./kiwiclient/kiwi/client.py
patch -i microkiwi_patch.diff ./kiwiclient/microkiwi_waterfall.py
patch -i plot_map_patch.diff ./TDoA/m/tdoa_plot_map.m
patch -i read_data_patch.diff ./TDoA/m/tdoa_read_data.m
rm -f *.diff
echo "The setup is now finished.\nTo start the software from console, type ./directTDoA.py"
sleep 5