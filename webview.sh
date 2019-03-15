#!/bin/sh
[ "$#" -eq 0 ] && return 1

bin=
case "$1" in
	*.jpg|*.jpeg|*.png|*.gif) # image exts
		bin=feh
	;;
	*.mp4|*.avi|*.flv) # video exts
		bin=mpv
	;;
	https://www.youtube.com/watch?v=*|*.crunchyroll.com/*)
		bin='./fq9 add'
	;;
	*) # the default option
		bin=xlinks2
	;;
esac
exec $bin $1
