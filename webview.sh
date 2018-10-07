#!/bin/sh
[ -z $1 ] && return 1
image_ext='.jpg .jpeg .png .gif'
video_ext='.mp4 .avi .flv'

has_prefix(){
	# $1 is the string
	# $2 are the exts
	for p in $2
	do
		[ $1 != ${1%$p} ] && return 0
	done
	return 1
}
has_prefix $1 $image_ext && exec feh $1
has_prefix $1 $video_ext && exec mpv $1
exec xlinks $1
