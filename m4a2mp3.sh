#!/bin/sh
#
# For converting m4a to mp3?
# Must have made this for youtube vids or something
fin='/media/COBY4GB/Music/Vocal/Various'
for f in *.m4a
do
	avconv -i ${f} -f wav pipe:1 | lame - ${fin}/`basename ${f} .m4a`.mp3
done