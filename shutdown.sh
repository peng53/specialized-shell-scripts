#!/bin/sh
# Use: execute it for some shutdown options, locking before options
# that can be reverted.
echo $#
if [ $# -lt 1 ]
then
	echo Usage: $(basename $0) option
fi
alias lock='xlock -fg white -bg black &'
case $1 in
	1|shutdown|Shutdown)
		sudo poweroff
	;;
	2|suspend|Suspend)
		lock
		sudo pm-suspend
	;;
	3|hibernate|Hibernate)
		lock
		sudo pm-hibernate
	;;
	4|lock|Lock)
		lock
	;;
	*)
		echo Canceled
	;;
esac
