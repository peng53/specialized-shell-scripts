#!/bin/sh
[ -z $1 ] && return 1
for p in jpg jpeg png gif
do
	[ $1 != ${1%.$p} ] && exec feh $1
done
exec xlinks2 $1
