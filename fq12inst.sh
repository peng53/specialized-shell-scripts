#!/bin/sh
# fq11
readonly tempDirectory=/mnt/ramdisk/
readonly urlQueue=${tempDirectory}mq
readonly urlQueueHist=${tempDirectory}q_hist
readonly lastPids=${tempDirectory}last_pids
readonly playerDefaultArgs='-really-quiet'
readonly youtubeDlDefaultArgs='--no-part --youtube-skip-dash-manifest --no-call-home --no-playlist'

alias yt_dl="~/yt-dlp_linux"
#readonly yt_dlp="~/yt-dlp_linux"
readonly vres=${vres:-240}
readonly vext=${vext:-webm}
readonly abr=${abr:-70}
readonly speed=${speed:-40k}

tryResume=0

downloadMedia(){
	local url=$1
	echo 'Downloading' $url
	[ $tryResume -eq 1 ] && echo 'Resuming from previous.'
	case "$url" in
		*.youtube.com/watch?v=*)
			#downloadYoutube $url
			downloadYoutubeVidAud $url
		;;
		*.crunchyroll.com/*)
			downloadStreamlink $url
		;;
		*)
			echo 'No url matches'
			return 1
		;;
	esac
	return $?
}

downloadStreamlink(){
	local url=$1 to=${tempDirectory}1
	[ $tryResume -eq 0 ] && overwriteVidBuf $to ${to}old
	# streamlink /never/ uses aud file
	overwriteVidBuf ${to}aud ${to}audold
	echo "Downloading at q = ${vres=240}p"
	#streamlink $url ${vres}p -o ${tempDirectory}1 &
	streamlink_dl -u $url -f ${vres}p -o ${tempDirectory}1 -r ${speed=64} &
	echo $! > $lastPids
	sleep 30
	return 0
}

downloadYoutube(){
	local url=$1
	#local out="$tempDirectory/1"
	echo "Downloading video at ${vres}p $vext format with ${abr}k audio"
	[ "$tryResume" -eq 0 ] && yt_dl $youtubeDlDefaultArgs -S 'filesize' -F $url > ${tempDirectory}formats
	getYoutubeFmts ${tempDirectory}formats
	if [ $? -eq 0 ]
	then
		clearPids
		downloadYoutubeFmt $url $vfmt ${tempDirectory}1
		sleep 7
		downloadYoutubeFmt $url $afmt ${tempDirectory}1aud
		sleep 20
		return 0
	else
		return 1
	fi
	return 0
}
downloadYoutubeVidAud(){
	local url=$1
	local vfmt=$2
	local afmt=$3
	if [ -z "$vfmt" ] || [ -z "$afmt" ]
	then
		echo "Downloading video at ${vres}p $vext format with ${abr}k audio"
		[ "$tryResume" -eq 0 ] && yt_dl $youtubeDlDefaultArgs -S 'filesize' -F $url > ${tempDirectory}formats
		getYoutubeFmts ${tempDirectory}formats
		if [ $? -ne 0 ]
		then
			overwriteVidBuf ${tempDirectory}1 ${tempDirectory}1old
			overwriteVidBuf ${tempDirectory}1aud ${tempDirectory}1audold
			return 1
		fi
	fi
	if [ -n $vfmt ] && [ -n $afmt ]
	then
		echo "Downloading video fmt $vfmt audo $afmt"
		clearPids
		downloadYoutubeFmt $url $vfmt ${tempDirectory}1
		sleep 7
		downloadYoutubeFmt $url $afmt ${tempDirectory}1aud
		sleep 20
		return 0
	fi
}
getYoutubeFmts(){
	local lines=$1
	echo $lines
	vfmt=$(findVideoFmtCode $vext $vres $lines)
	if [ "$vfmt" -eq 0 ]
	then
		echo 'Video not available in resolution.'
		return 1
	fi
	echo Vfmt $vfmt
	afmt=$(findAudioFmtCode $abr $lines)
	if [ -z "$afmt" ]
	then
		echo 'Audio not available in bitrate.'
		return 1
	fi
	echo Afmt $afmt
	return 0
}
findAudioFmtCode(){
	local best=0 desired=$1 lines=$2 code=0 line
	local least=9999 lcode=0
	while IFS= read -r line
	do
		echo $line | grep 'audio only' -o >/dev/null
		[ $? -ne 0 ] && continue
		local rate=$(echo $line | egrep '[0-9]{2,3}k' -o | head -n 1)
		rate=${rate%?}
		if [ -n "$rate" ] && [ "$rate" -le "$desired" ] && [ $rate -gt $best ]
		then
			best=$rate
			code=$(echo $line | cut -f 1 -d ' ')
		fi
		if [ -n "$rate" ] && [ "$rate" -le "$least" ]
		then
			least=$rate
			lcode=$(echo $line | cut -f 1 -d ' ')
		fi
	done < $lines
	if [ $best -ne 0 ]
	then
		echo $code
	else
		echo $lcode
	fi
}
findVideoFmtCode(){
	local bestRes=0 bestFmt=0 desiredCodec=$1 desiredVRes=$2 lines=$3 line
	while IFS= read -r line
	do
		echo $line | grep 'video only' | egrep '[0-9]{3}\s+'$desiredCodec > /dev/null
		[ $? -ne 0 ] && continue
		# Check if line has vertical resolution
		local res=$(echo $line | egrep '[0-9]{2,4}x[0-9]{2,4}' -o | cut -d 'x' -f 2)
		[ -z "$res" ] && continue
		# Extract vertical resolution
		if [ "$res" -le "$desiredVRes" ] && [ "$res" -gt "$bestRes" ]
		then
			bestRes=$res
			bestFmt=$(echo $line | cut -f 1 -d ' ')
		fi
	done < $lines
	echo $bestFmt
}
downloadYoutubeFmt(){
	local url=$1 fmt=$2 to=$3
	[ $tryResume -eq 0 ] && overwriteVidBuf $to ${to}old
	echo "Download started for fmt |$fmt|"
	yt_dl $youtubeDlDefaultArgs -r $speed -f $fmt $url -o $to &
	echo $! >> $lastPids
}
printFormats(){
	echo '\033[31mVideo\033[0m'
	grep 'video only' $tempDirectory/formats | cut -d '|' -f 1,2
	echo '---'
	echo '\033[31mAudio\033[0m'
	grep 'audio only' $tempDirectory/formats | grep 'https' | cut -d '|' -f 1,2
}
overwriteVidBuf(){
	# Overwrites filename 2nd arg at ${tempDirectory} with 1st arg
	[ -f $1 ] && mv -f $1 $2
}

addQueueUrl(){
	[ -n "$1" ] && echo $1 >> $urlQueue
}

getQueueUrl(){
	local url
	read -r url < $urlQueue
	echo $url
}
popQueueUrl(){
	sed -i '1d;/^$/d' $urlQueue
}

viewMedia(){
	if [ -s ${tempDirectory}1 ]
	then
		local dash
		[ -s ${tempDirectory}1aud ] && dash="-audiofile ${tempDirectory}1aud"
		echo Viewing media
		echo $dash
		mplayer $playerDefaultArgs ${tempDirectory}1 $dash &
	fi
}


handleHist(){
	case "$1" in
		see|'')
			cat $urlQueueHist
		;;
		add)
			addQueueUrl $(getHistUrl)
		;;
		resume)
			url=$(getHistUrl)
			if [ -n "$url" ]
			then
				echo 'Resuming from history.'
				tryResume=1
				tryDl='true'
			fi
		;;
	esac
}
getHistUrl(){
	[ -s $urlQueueHist ] && echo $(tail -n 1 $urlQueueHist)
}


addToHist(){
	[ -z "$1" ] && return
	local last
	[ -s $urlQueueHist ] && last=$(getHistUrl)
	[ "$last" != "$1" ] && echo $1 >> $urlQueueHist
}

haltLastPid(){
	local pid
	while IFS= read -r pid
	do
		if [ -d /proc/$pid ]
		then
			kill $pid
			echo "Killed PID #${pid}"
		fi
	done < $lastPids
	> $lastPids
}
clearPids(){
	> $lastPids
}

checkPids(){
	[ ! -f $lastPids ] && return 0
	local pid
	while IFS= read -r pid
	do
		if [ -d /proc/$pid ]
		then
			echo Process from last call still open! $pid
			return 1
		fi
	done < $lastPids
	return 0
}

tryDl='false'
case "$1" in
	'')
		url=$(getQueueUrl)
		if [ -n "$url" ]
		then
			popQueueUrl
			tryDl='true'
		fi
	;;
	f)
		downloadYoutubeVidAud $2 $3 $4
		viewMedia
	;;
	resume)
		tryResume=1
		if [ $# -gt 1 ]
		then
			url=$2
		else
			url=$(getQueueUrl)
			[ -n "$url" ] && popQueueUrl
		fi
		[ -n "$url" ] && tryDl='true'
	;;
	add)
		addQueueUrl $2
	;;
	get)
		url=$(getQueueUrl)
		[ -n "$url" ] && popQueueUrl && echo $url
	;;
	top)
		url=$(getQueueUrl)
		[ -n "$url" ] && echo $url
	;;
	flush)
		> $urlQueue
		echo 'Queue flushed.'
	;;
	purge)
		rm -v -i $urlQueue ${tempDirectory}1 ${tempDirectory}1aud ${tempDirectory}1old ${tempDirectory}1audold ${tempDirectory}formats ${tempDirectory}q_hist ${tempDirectory}last_pids
	;;
	see)
		cat $urlQueue
	;;
	view)
		viewMedia
	;;
	hist)
		handleHist $2
	;;
	halt)
		haltLastPid
	;;
	formats)
		printFormats
	;;
	x)
		url=`xclip -o`
		tryDl='true'
	;;
	*)
		url=$1
		tryDl='true'
	;;
esac

if [ "$tryDl" = 'true' ] && [ -n "$url" ]
then
	checkPids
	if [ $? -eq 0 ]
	then
		[ "$(getHistUrl)" = "$url" ] && tryResume=1
		addToHist $url
		downloadMedia $url && viewMedia
	fi
fi
