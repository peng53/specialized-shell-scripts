#!/bin/sh
#
# Converts resulting wav file from mid.sh to a mp3
#
out='/mnt/ramdisk/out.'
#twolame -b 160 -v ${out}wav ${out}mp2
# mp2 wasn't what I needed
#lame -v --vbr-new -V 4 ${out}wav ${out}mp3
# trying out options on lame
lame -v --vbr-new -b 8 -B 64 ${out}wav ${out}mp3
