# directTDoA v3.10

This piece of software is JUST a GUI written for Python 2.7 designed to compute TDoA maps with GPS enabled KiwiSDR servers around the world using GNU Octave & the EXCELLENT work of Christoph Mayer @ https://github.com/hcab14/TDoA + his forked "kiwiclient" python stuff, original code by Dmitry Janushkevich @ https://github.com/dev-zzo/kiwiclient

Thanks to Pierre Ynard (linkfanel) for the listing of available KiwiSDR nodes used as source for the TDoA map update process (http://rx.linkfanel.net)

Thanks to Marco Cogoni (IS0KYB) for allowing me the use of his SNR measurements of the KiwiSDR network (http://sibamanna.duckdns.org/sdr_map.html)


## INSTALL AND RUN (on LINUX) Thanks Daniel E. for the install procedure

Install python 2.7.xx

Install python-pip (search for the right package for your distro)

Install GNU octave 4.4.0 (stable version)

`git clone --recursive https://github.com/llinkz/directTDoA`

`cd directTDoA`

`./setup.sh` (this script will install python modules, compile the necessary .oct file and apply the patch to bypass the .png file creation)

`./directTDoA.py` (note: check the shebang if it fails on your system. On my Archlinux it should be "#!/usr/bin/python2" for example)


## INSTALL AND RUN (on MAC OS) Thanks Nicolas M. for the install procedure

* REQUIREMENT 	Xcode + Homebrew (https://brew.sh/index_fr)

Install Homebrew, in terminal : `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

Install Python 2.7, in terminal : `brew install python@2`

Install GNU Octave 4.4.0, in Terminal : `brew install octave`

`git clone --recursive https://github.com/llinkz/directTDoA`

`cd directTDoA`

`./setup.sh`  (this script will install python modules, compile the necessary .oct file and apply the patch to bypass the .png file creation)

`./directTDoA.py`


## LICENSE
* This python GUI code has been written and released under the "do what the f$ck you want with it" license


## WARNING
* This code may contain some silly procedures and dumb algorithms as I'm not a python guru, but it almost works so...
* This code is not optimized at all as well, will try to do my best during free time...


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


## TODO LIST
* ultimateTDoA variant mode ? (c)Daniel Ekmann, to basically record all possible nodes at same time in order to post-compute TDoAs later with a dynamic .m file
* securizing the node.db.bak in case of multiple faulty update processes
* adding more error triggers in case of faulty update process or failed connections to node (bad password / node is busy)
* compute mini-waterfall pictures on selected nodes if necessary (directly in python, not via jupyther notebook stuff)
* merging a part of the directKiwi code to connect & get the audio stream from the selected nodes (faster than the webconnect to openwebrx interface)