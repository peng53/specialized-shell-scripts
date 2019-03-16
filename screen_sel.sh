#!/bin/sh
xmessage 'Select screen configuration.' -buttons Cancel:0,Laptop:1,VGA:2,Both:3
case $? in
	1)
		# LVDS
		xrandr --output VGA1 --off
		xrandr --output LVDS1 --mode 1366x768
	;;
	2)
		# VGA
		xrandr --output LVDS1 --off
		xrandr --output VGA1 --mode 1280x1024
	;;
	3)
		# BOTH
		xrandr --output VGA1 --mode 1280x1024
		xrandr --output LVDS1 --mode 1366x768  --right-of VGA1
	;;
esac
