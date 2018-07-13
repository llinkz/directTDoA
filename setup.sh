#!/bin/sh
python -m pip install numpy pillow
cd TDoA/kiwiclient
mkoctfile read_kiwi_iq_wav.cc
cd ../..
