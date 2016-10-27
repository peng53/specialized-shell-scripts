#!/bin/sh
out='/mnt/ramdisk/out.'
#twolame -b 160 -v ${out}wav ${out}mp2

#lame -v --vbr-new -V 4 ${out}wav ${out}mp3

lame -v --vbr-new -b 8 -B 64 ${out}wav ${out}mp3
