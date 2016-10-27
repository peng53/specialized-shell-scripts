#!/bin/sh
#
# Converts input mid to wav using fluidsynth
#
sf='/usr/share/sounds/sf2/FluidR3_GM.sf2'
ou='/mnt/ramdisk/out.wav'
# sf is the soundfont I used
# output is written to ramdisk temporarily
# for use in mp3.sh
fluidsynth -F "$ou" "$sf" "$1"
