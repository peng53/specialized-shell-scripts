#!/bin/sh
#
# Converts all mid on ramdisk to mp3 writing to mp3 player
# Combines mid.sh & mp3.sh
# Would be desirable to now have to write the wav &
# just "pipe" wav data to lame, but couldn't figure
# out how; use of ramdisk may mitigated the writing though
cd /mnt/ramdisk/
for i in *.mid
do
	sf='/usr/share/sounds/sf2/FluidR3_GM.sf2'
	out=${i%%mid}
	fluidsynth -F ${out}wav "$sf" "$i"
	# first to wav to ramdisk
	#lame -v --vbr-new -b 8 -b 64 ${out}wav ${out}mp3
	#fluidsynth "$sf" "$i" -F | lame -v --vbr-new -b 8 -B 64 ${out}mp3
	lame -v --vbr-new -b 8 -b 64 ${out}wav '/media/COBY4GB/Music/Midi/'${out}mp3
	# then wav to mp3 to player
done
