#!/bin/sh
# Audible heartbeat via PC speaker as reminder
# of computer's on/off status (per 30mins)
while :
do
	beep -f 950 -d 300
	sleep 30m
	beep -f 4000 -d 200
	sleep 30m
done

