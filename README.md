# directTDoA

This piece of software is JUST a GUI written for Python 2.7 designed to compute TDoA maps with GPS enabled KiwiSDR servers around the world using GNU Octave & the EXCELLENT work of Christoph Mayer @ https://github.com/hcab14/TDoA + his forked "kiwiclient" python stuff (original code by Dmitry Janushkevich)


## LICENSE
* This python GUI code has been written and released under the "do what the f$ck you want with it" license


## WARNING
* This code may contain some silly procedures and dumb algorithms as I'm not a python guru, but it almost works so...
* This GUI may freeze sometimes, just restart it..
* If UPDATE process fails, a copy of the server DB is available under the name "directTDoA_server_list.db.bak"

## CHANGE LOG
* v1.00-1.50 : first working version, basic, static map, manual host adding, hardcoded coordinates, manual octave code run etc...
* v2.00 : current work, update & dynamic maps full of GPS enabled nodes, auto octave code run, easier to use
* v2.10beta : adding differents maps that can be choosed by the user, early work on SNR and tiny waterfall for nodes
* v2.20: adding favorite/blacklist node management, popup menu when clicking a node gives: add for TDoA proc + Open KiwiSDR in browser
* v2.21: reducing the map boundaries red rectangle 'sensivity' when mouse is near main window borders
* v2.30:  adding node color change possible + code clean-up + adding a popup window telling you forgot to choose your map boundaries before starting the IQ recording + Popup menus are now disabled (Add/Open) if the node has no slot available + Added a gray scale map more brighter

## TODO LIST
* adding a list of known MIL/GOV/MARITIME/AERO/DIPLO/... TX site locations beside the list of World cities
* dealing with nodes that forwards a xx° yy' zz.z'' GEO format (gnss_pos retrieving)
* work harder on recorded IQ BW change possibility, the center frequency moves but the IQ bandwidth stays at 10kHz apparently
* adding a pop-up at the end of process to give possibility to display the png, the pdf, the generated .m to be edited and re-processed w/o 1 or 2 nodes and if we want to restart the GUI like it does at this time (v2.20)
