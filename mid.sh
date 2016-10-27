#!/bin/sh
sf='/usr/share/sounds/sf2/FluidR3_GM.sf2'
ou='/mnt/ramdisk/out.wav'
fluidsynth -F "$ou" "$sf" "$1"

