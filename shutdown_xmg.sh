#!/bin/sh
# Creates shutdown dialog with xmessage
# and calls shutdown option with shutdown.sh
xmessage 'Power options' \
	-buttons Cancel:cancel,Shutdown:1,Suspend:2,Hibernate:3,Lock:4\
	-default Cancel
sh shutdown.sh $?
