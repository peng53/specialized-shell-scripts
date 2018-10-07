#!/bin/sh
[ "$#" -eq 0 ] && return 1

bin=
case "$1" in
	https://www.youtube.com/watch?v=*)
		bin='./fq8 add'
	;;
	*.jpg|*.jpeg|*.png|*.gif) # image exts
		bin=feh
	;;
	*.mp4|*.avi|*.flv) # video exts
		bin=mpv
	;;
	*) # the default option
		bin=xlinks2
	;;
esac
exec $bin $1
