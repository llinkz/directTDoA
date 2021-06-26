# directTDoA v7.00

This software is JUST a python 2/3 GUI designed to compute TDoA runs on shortwave radio transmissions using remote (GPS enabled) KiwiSDR receivers around the World.

> TDoA = Time Difference of Arrival .. (in this case: the Arrival of shortwave radio transmissions)

## INSTALL AND RUN (on WINDOWS)

##### The decision was made not to support installation from the repository.

Download [directTDoA-windows.zip](https://github.com/llinkz/directTDoA/releases/download/v6.20/directTDoA-windows.zip), unzip and extract it

Then double-click on `directTDoA.bat`

##### NB: Windows users will get directTDoA v6.20

#### IMPORTANT: You must use only this method to launch the program to avoid file path issues.

> Info: this archive contains all the necessary files already patched and compiled and also includes light versions of GNU Octave and python, so no need to install the full versions of the last two on your machine. The unzipped archive is 272 MB, compared to ~2 GB in the other installer way.

## INSTALL AND RUN (on LINUX)

Install python 3 and python-pip using your package manager

Install GNU octave

Install git, patch, gcc, base-devel, ttf-dejavu, gcc-fortran, tk, portaudio, xdg-utils, epdfview, fltk

`git clone --recursive https://github.com/llinkz/directTDoA`

`cd directTDoA`

`./setup.sh` (this script will install python modules, compile the necessary .oct file and apply some files patchs)
#### IMPORTANT: The octave files compilation process takes a lot of time, be patient, ignore warnings and don't stop the script
`./directTDoA.py`

> NOTE: on some distros you may need to install liboctave-dev

## INSTALL AND RUN (on MAC OS X)

* REQUIREMENT 	Xcode + Homebrew (https://brew.sh/index_fr)

Install Homebrew, in terminal : `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

Install Python, in terminal : `brew install python@2` or `brew install python@3`

Install GNU Octave in Terminal : `brew install octave`

`git clone --recursive https://github.com/llinkz/directTDoA`

`cd directTDoA`

`./setup.sh`  (this script will install python modules, compile the necessary .oct file and apply patches to some files. Check errors but Ignore warnings)

`./directTDoA.py`

## LICENSE
* This python GUI code has been written and released under the "do what the f$ck you want with it" license

## CHANGE LOG
* v1.00-1.50 : first working version, basic, static map, manual host adding, hardcoded coordinates, manual octave code run etc...
* v2.00 : current work, update & dynamic maps full of GPS enabled nodes, auto octave code run, easier to use
* v2.10beta : adding differents maps that can be choosed by the user, early work on SNR and tiny waterfall for nodes
* v2.20: adding favorite/blacklist node management, popup menu when clicking a node gives: add for TDoA proc + Open KiwiSDR in browser
* v2.21: reducing the map boundaries red rectangle 'sensivity' when mouse is near main window borders
* v2.30: adding node color change possible + code clean-up + adding a popup window telling you forgot to choose your map boundaries before starting the IQ recording + Popup menus are now disabled (Add/Open) if the node has no slot available + Added a gray scale map more brighter
* v2.31: bugfix on checkfilesize process
* v2.32: adding a restart GUI button
* v2.33: adding MacOS X compatibility, thx Nicolas M.
* v2.40: known points (world capitals) listing is now a file, format is 'name,lat,lon' - easier for you to add yours :-)
* v2.41: update process modified due to missing tags for some nodes in kiwisdr.com/public page
* v2.42: forgot some conditions for MacOS compatibility  oops  thanks Nicolas M. again  :-)
* v2.43: auto create the directTDoA_server_list.db file at 1st start, file does not need to be in the repo anymore
* v2.44: MacOS tested OK, code cleanup + warning about missing GPS timestamps in IQ recordings  -uglymaps +kickass NASA maps
* v2.50: some TODO list items coded or fixed
* v2.60: map update now based on John's json listing + GPS fix/min map filter + nodes are identified by IDs, no hosts anymore + no .png file creation (patch) + no more gnss_pos.txt backup and no more TDoA/gnss_pos/ purge
* v2.70: Octave subprocess management modified (no more octave defunct remaining in "ps aux" now) + stdout & stderr saved in the same "TDoA/iq/<backup>/TDoA_<freq>.txt" file
* v2.71: each node color brightness is now based on its latest GPS fix/min value, it will become darker when fix/min will go towards "0" + my own kiwiSDR coordinates more accurate
* v2.72: Adding the SNR values of each node from linkfanel's (JSON) database + Color points (nodes) change in brightness according to the SNR, minimum=0 <darker - brighter> maximum=35? (version not released)
* v2.80: Listing update is now made from both linkfanel's (JSON) databases only (GPS enabled nodes list + SNR values) + adding regexp to create TDoA_id (parsing callsigns), IPs and node various coordinates format (version not released)
* v2.90: Code clean-up + SNR values are now only from IS0KYB (JSON) database + count TDoA runs at start + adding a ./recompute.sh script to backup dir + directTDoA node db now in JSON format + add map legend + popup menu font color managed for more readibility + new maps
* v3.00: More code clean-up and as the GUI has changed a lot recently, it's now entering the v.3xx version range
* v3.10: Removed "20 kHz wide audio bandwidth mode" set KiwiSDRs from the node list, incompatible with TDoA at this time (2jan19) + reachability & GPS_good, fixes_min, user, users_max values are now dynamic when node is clicked on map (timeout/host not found/obsolete proxy data)
* v3.20: Better management of clicked nodes (checking offline=yes/no + TDoA_ch>=1 + fixes_min>0) + default IQ rec BW in config file added + possibility to restart the IQ rec process + Marco/Pierre websites checked before update process start + current release version check menu added
* v3.21: the popup when map boundaries are set has been removed - adding mode informations in the TDoA map result title - minor bug fixes with the bandwidth default/current setting
* v3.22: map boundaries informations back, as label..
* v3.23: bug fixes with add/remove fav/black process..
* v3.24: allowing the possibility to "Open" a node in browser even if 0 GPS fixes were reported at instant T + minor date modification on TDoA output file title + minor text corrections
* v4.00: no more GUI restart after TDoA runs (node list is kept intact) + Listen/Demod mode added, **requires python modules _pygame_ (for all) + _scipy_ (for MacOS X), new file _KiwiSDRclient.py_ also required** + possibility to remove a single node from the list + purge button added + check version runned on software start + minor fixes on many routines
* v4.10: "Restart Rec" is now "Stop Rec" instead (it saves IQ files and generate .m file only) + added "Abort TDoA" routine so you can stop a previewed bad result octave process w/o having to restart full GUI + minor mods on checkversion(), float(frequency) and restart/close GUI + 200Hz high pass filter block commented out and empty known point block added in proc.m files
* v4.18: early ultimateTDoA mode dev, adding a necessary patch for TDoA/kiwiclient/kiwiworker.py to bypass returned errors causing full IQ recording process freezes (KiwiBadPasswordError & KiwiDownError) **to apply run: _patch -i kiwiworker_patch.diff ./TDoA/kiwiclient/kiwiworker.py_**
* v4.19: adding another patch for TDoA/m/tdoa_plot_map.m to display the 'most likely position' string in the final pdf title + exchanging lon and lat values position for better reading - **Note: that patch already contains the nopng patch previously released**
* v4.20: introducing new **ultimateTDoA** mode (massive IQ recordings without octave run from the GUI), nodes selection using the same way as defining TDoA map boundaries, all IQ files saved and compute_ultimate.sh dynamic bash script created in same ./TDoA/iq/subdirectory + recomputed pdf files now containing a timestamp so you'll keep all of them (instead of overwriting the only ./TDoA/pdf one)
* v5.00: big code optimization + adding waterfall/SNR measurement + removing Marco website source + keyboard shortcuts + filter/color/icon/add rem fav/blk changes w/o restart - better precision on map (coordinates with decimals) + highlight on selected nodes + plot_iq.py script (plotting IQ spectrograms w/o GPS ticks) + GUI colors management
         + mapbox.com world maps in final results + trim_iq.py script to modify the recorded IQ files + Sorcerer TCP client for ALE auto-detect & auto-compute TDoAs
* v5.10: removed KiwiSDR nodes "names" from .db files + compute_ultimate script has been transformed into GUI with plot_iq now only displaying the selected nodes + adding command arguments to trim_iq.py script (./trim_iq.py -h ,for help)
* v5.20: "directTDoA_v5.xx" now displayed on the KiwiSDR target's userlist when connected + simplification of the node rec-list management + adding a checkbox to automatically start (or not) _compute_ultimate.py_ script when "Stop Rec" button is clicked + extra command on KiwiSDR first line popup to add the node even if it has _fixes_min=0_
         + new _has_gps_ routine in both _plot_iq.py_ & _compute_ultimate.py_ + bug fix: regexp wrongly detecting LON + bug fix: if Sorcerer TCP client checkbox is unchecked while recording, no more endless record session.
* v6.00: Listen mode (AM/LSB/USB) is back, to get it working you must apply a patch: `patch -i kiwirecorder_patch.diff ./kiwiclient/kiwirecorder.py` from directTDoA dir and install sounddevice + samplerate python modules with `python -m pip install sounddevice samplerate` + some python 2 Vs. python 3 bug fixes + bug fixed on map update process + .desktop files creation removed
* v6.10: Restart GUI routine modified + less CMD windows for Windows OS users (using pythonw instead of python) + bug fix that caused the map to move suddenly far away when selecting a node (problem only noticed on Windows OS) + no more auto-PlotIQ() start on ultimateTDoA runs + modifications of the .bat files for Windows OS users (CPU affinity of the python processes now set towards a single one, the allocation on several generated a delay in the starting of the IQ records)
* v6.20: User demand and personal use: added functionality to manage the overlapping of icons on the map. Now when you click near a cluster of multiple nodes, a menu will appear and allow you to choose the one you really want + some GUI design changes + bug fix on map locations search (avoid multiple displayed)
* v7.00: Adding USB/LSB/CW/AM/2kHz/4kHz/6kHz/8kHz IQ BW presets + display bug fix for known places on map + adding recorded nodes Vs selected nodes counter + recording time in file size window + IQ rec length max limit set to 120 seconds (just in case) + TCP client modified, possibility to change the trigger word (regexp supported) + PDF title mods + remember GUI size & position on close + MAP & SNR update only via KiwiSDR.com/public now + nognss.py script added, to remove GNSS ticks from the IQs so files can get opened and demodulated fine
## Thanks
* Christoph Mayer @ https://github.com/hcab14/TDoA for the main TDoA code, excellent work and thanks for the public release !
* John Seamons, KiwiSDR developper @ https://github.com/jks-prv
* Dmitry Janushkevich @ https://github.com/dev-zzo/kiwiclient for the code that I've modified to work with the GUI 
* Marco Cogoni (IS0KYB) for the microkiwi_waterfall.py code that I've modified to work directly via python
* Nicolas M. for the MAC OS X directTDoA installing procedure

## Special Thanks
* Daniel Ekmann, naturally designated as a beta tester, for the help on coding, feedbacks and suggestions since the beginning.
