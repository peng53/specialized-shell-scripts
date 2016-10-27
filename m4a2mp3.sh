#!/bin/sh
tmp='/mnt/ramdisk/'
fin='/media/COBY4GB/Music/Vocal/Various/'

for f in *.m4a
do
	ou=${f%%m4a}
	avconv -i "$f" ${tmp}${ou}wav
	lame -v --vbr-new -b 8 -b 64 ${tmp}${ou}wav ${fin}${ou}mp3
done
