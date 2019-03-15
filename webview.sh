#!/bin/sh
[ $# -eq 0 ] && return 1

bin=
def_args=
case "$1" in
	*.jpg|*.jpeg|*.png|*.gif) # image exts
		bin=feh
		def_args='-x -k -q'
	;;
	*.mp4|*.avi|*.flv) # video exts
		bin=mpv
		def_args='--pause --keep-open --really-quiet'
	;;
	https://www.youtube.com/watch?v=*|*.crunchyroll.com/*)
		bin='./fq9 add'
	;;
	*) # the default option
		bin=xlinks2
	;;
esac
exec $bin $def_args $1
