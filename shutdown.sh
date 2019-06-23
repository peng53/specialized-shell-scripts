#!/bin/sh
# Use: execute it for some shutdown options, locking before options
# that can be reverted.
alias lock='xlock -fg white -bg black &'
xmessage 'Power options' -buttons Cancel:0,Shutdown:1,Suspend:2,Hibernate:3,Lock:4 -default Cancel
case $? in
	1)
		sudo poweroff
	;;
	2)
		lock
		sudo pm-suspend
	;;
	3)
		lock
		sudo pm-hibernate
	;;
	4)
		lock
	;;
	*)
		echo Canceled
	;;
esac
