#!/bin/sh
xmessage 'Choose keyboard layout.' -buttons CANCEL:0,qwerty:1,colemak:2
case $? in
	1)
		# qwerty
		setxkbmap us
		echo 'Keyboard layout now set to qwerty'
	;;
	2)
		# colemak
		setxkbmap us -variant colemak
		echo 'Keyboard layout now set to colemak'
	;;
	*)
		echo 'No changes made.'
	;;
esac
