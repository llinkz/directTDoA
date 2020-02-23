#!/bin/bash
## This file is intended to copy back *.wav to iq directory
## and to open a node list selection script so you can choose which nodes you want to use to create .m file and run TDoA
cp ./*.wav ../
echo -e "### ultimateTDoA dynamic octave file process started...\n"
declare -a FILELIST
declare -a NODELIST
declare PROCFILE
declare PROCFILEM
declare TEMPFILE
declare EVAL

for e in *.empty; do
    TEMPFILE=$e
done

PROCFILE="${TEMPFILE/empty/m}"
cp $TEMPFILE $PROCFILE

if [ $(python -c 'import sys; print(sys.version_info[0])') -eq "2" ]; then
    PROCFILEM="${TEMPFILE/empty/m}"
    EVAL=$""
else
    PROCFILEM="${TEMPFILE/.empty/}"
    EVAL=$"--eval"
fi

if [ ! -f *spec.pdf ]; then
    echo -e "Creating spectrogram picture from all IQ recordings stored in directory.\n"
    python plot_iq.py
    for f in *spec.pdf; do
        printf '\n%s file has been created.\n\n' "$f"
        xdg-open $f
    done
fi

for f in *.wav; do 
    FILELIST[${#FILELIST[@]}+1]=$(echo "$f");
done

for ((g=1;g<=${#FILELIST[@]};g++)); do
	printf '%s\t%s %s\n' "$g" `echo "${FILELIST[g]}" | awk '{split($0,a,"_"); print a[3]}'` "[`du -k ${FILELIST[g]} |cut -f1` KB]"
done

echo -e "\nEnter node numbers you want to include in the TDoA process (min=3 max=6), separate them with a comma (Ctrl+C to exit)"
read nodeschoice

nodes=$(echo $nodeschoice | tr "," "\n")
for node in $nodes; do
	NODELIST[${#NODELIST[@]}+1]=$(echo "${FILELIST[node]}");
done

if [[ ("${#NODELIST[@]}" -gt 2) && ("${#NODELIST[@]}" -lt 7 ) ]]; then
	i="${#NODELIST[@]}"
	for ((h=1;h<=${#NODELIST[@]};h++)); do	
		sed -i '/\  # nodes/a \ \ input('$i').fn    = fullfile('\''iq'\'', '\'''${NODELIST[h]}''\'');' $PROCFILE
		((i--))
	done
else
	echo "ERROR: process aborted, please choose between 3 and 6 nodes !"
	echo ${NODELIST[@]}
	sleep 2
	exit
fi

read -n1 -p "Do you want to edit $PROCFILE file before running octave process ? [y,n] " next2 
case $next2 in  
  y|Y) printf '\n' && $EDITOR $PROCFILE && cp $PROCFILE $TEMPFILE && sed -i '/wav/d' $TEMPFILE && cp $PROCFILE ../../ && cd ../.. && octave-cli $EVAL $PROCFILEM ;;
  n|N) cp $PROCFILE ../../ && cd ../.. && octave-cli $EVAL $PROCFILEM ;;
  *) exit ;;
esac