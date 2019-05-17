#!/bin/sh
[ $# -eq 0 ] && return 1

#cwd=`dirname $0`
case "$1" in
	*.jpg|*.jpeg|*.png|*.gif) # image exts
		feh -x -q $1
	;;
	*.mp4|*.avi|*.flv) # video exts
		mpv --pause --keep-open --really-quiet $1
	;;
	https://www.youtube.com/watch?v=*|*.crunchyroll.com/*)
		`dirname $0`/fq9 add $1
	;;
	*) # the default option
		xlinks2 $1
	;;
esac
