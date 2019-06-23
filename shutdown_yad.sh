#!/bin/sh
# Create shutdown dialog with yad
# and calls shutdown option with shutdown.sh
#yad --title=Shutdown --text='Select power option..'\
	#--button=Cancel:0\
	#--button=Shutdown:1\
	#--button=Suspend:2\
	#--button=Hibernate:3\
	#--button=Lock:4\
	#--skip-taskbar\
	#--mouse\
	#--center
#sh shutdown.sh $?
option=`yad --title=Shutdown --text='Select power option..'\
	--form --field=Option:CB\
	'Shutdown!Suspend!Hibernate!Lock'`

sh shutdown.sh $(echo $option | tr -d '|')

