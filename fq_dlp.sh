#!/bin/sh
# fq_dlp.sh / fq rewrite with yt-dlp instead of youtube-dl

readonly tempDirectory=/mnt/ramdisk/
readonly urlQueue=${tempDirectory}mq
readonly urlQueueHist=${tempDirectory}q_hist
readonly lastPids=${tempDirectory}last_pids
readonly playerDefaultArgs='--pause --keep-open --really-quiet'
readonly yt_dlp="~/bin/yt-dlp"

# if setting any of the below in shell, remember to export them
readonly vres=${vres:-240}
readonly vext=${vext:-webm}
readonly abr=${abr:-80}
readonly speed=${speed:-48}


downloadYoutube(){
	local url=$1
	local out="$tempDirectory/yt-vid"
	overwriteVidBuf $out ${out}old
	echo "Downloading video at ${vres}p $vext format with ${abr}k audio"
	eval "$yt_dlp -S "res:$vres,vext:$vext,abr:$abr,size" --no-playlist -r $speed'k' -o $out -c --no-part $url" &
}
viewMedia(){
	if [ -s ${tempDirectory}/yt-vid ]
	then
		echo Viewing media
		mpv $playerDefaultArgs ${tempDirectory}/yt-vid &
	fi
}
overwriteVidBuf(){
	# Overwrites filename 2nd arg at ${tempDirectory} with 1st arg
	[ -f $1 ] && mv -f $1 $2
}

case "$1" in
	'')
		echo 'No arguments..'
	;;
	view)
		viewMedia
	;;
	*)
		echo "Downloading: $1"
		downloadYoutube $1
		sleep 30
		viewMedia
	;;
esac
