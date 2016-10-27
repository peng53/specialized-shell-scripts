#!/bin/sh
#
# For converting m4a to mp3?
# Must have made this for youtube vids or something
tmp='/mnt/ramdisk/'
fin='/media/COBY4GB/Music/Vocal/Various/'
# input,output folder, all in 1 batch
for f in *.m4a
do
	ou=${f%%m4a}
	# strip away m4a postfix
	avconv -i "$f" ${tmp}${ou}wav
	# looks like I had to convert to wav before hand?
	# curious why I couldn't just use avconv to get to
	# mp3 directly
	lame -v --vbr-new -b 8 -b 64 ${tmp}${ou}wav ${fin}${ou}mp3
	# ^^ I didn't want to install restricted-extras
done
