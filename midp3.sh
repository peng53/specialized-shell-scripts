#!/bin/sh

cd /mnt/ramdisk/
for i in *.mid
do
	sf='/usr/share/sounds/sf2/FluidR3_GM.sf2'
	out=${i%%mid}
	fluidsynth -F ${out}wav "$sf" "$i"
	#lame -v --vbr-new -b 8 -b 64 ${out}wav ${out}mp3
	#fluidsynth "$sf" "$i" -F | lame -v --vbr-new -b 8 -B 64 ${out}mp3
	lame -v --vbr-new -b 8 -b 64 ${out}wav '/media/COBY4GB/Music/Midi/'${out}mp3
done
