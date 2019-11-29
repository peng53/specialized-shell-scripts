#!/usr/bin/env python3
from sys import argv as ARGV
from typing import Dict
from typing import Callable
from typing import List
from yt_dl_urls import YTDownloadThread, get_audio_fmt, get_video_fmt, yt_info, FileAlreadyExistsException
from tempfile import mktemp
from subprocess import Popen
from time import sleep
import threading
import datetime
import os
import argparse
import streamlink

settings = {
	"quality": 240,
	"abr": 80,
	"speed": 56,
	"format": 'webm',
	'player': 'mpv',
	'TMP': "/mnt/ramdisk",
} # type: Dict[str]

for key in settings:
	if key in os.environ:
		settings[key] = os.environ[key]

player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]
q_name = "mq" # type: str
q_hist_name = "q_hist" # type: str


def filePeek(F) -> str:
	''' Return first line from file object'''
	return F.readline()

def filePop(filename: str) -> str:
	''' removes first line from file and return it '''
	if not os.path.exists(filename):
		print("Queue file does not exist.")
		return
	tmp_f = mktemp(dir=settings['TMP']) # type: str
	os.rename(filename,tmp_f)
	r = None # type: str
	with open(tmp_f,'r') as f, open(filename,'w') as g:
		"""This block sets r to the first line
			and then writes the rest to 'new' tmpfile"""
		l = f.readline() # type: str
		r = l
		while l:
			l = f.read(1024)
			g.write(l)
	os.remove(tmp_f)
	if r:
		r = r.rstrip()
		return r

def fileAppend(filename: str,line: str) -> None:
	"""Appends line to file f_name residing in f_dir."""
	l = line.rstrip() # type: str
	if l:
		with open(filename,'a') as f:
			f.write(l+'\n')

def clearFile(filename: str) -> None:
	''' empties a file'''
	open(filename,'w').close()



def viewVid(v_dir: str,v_name: str, a_name: str = None) -> None:
	"""	Views download media files using global var player and
		player args. Takes a_name optionally as audio track."""
	vid = os.path.join(v_dir,v_name)
	if os.path.exists(vid):
		cmd = [settings['player'],vid]+player_args
		if a_name:
			cmd.append('--audio-file='+os.path.join(v_dir,a_name))
		Popen(cmd)
	else:
		print("No video file exists.")


def overwriteFile(v_dir: str,v_name: str = "1",v_name_old: str = "0") -> None:
	''' displaces last vid by replacing v_name_old with it '''
	old = os.path.join(v_dir,v_name_old) # type: str
	new = os.path.join(v_dir,v_name) # type: str
	if os.path.exists(old):
		os.remove(old)
	if os.path.exists(new):
		os.rename(new,old)



def searchYtFormats(url: str, resolution: int, fmt: str, abr: int):
	yd = yt_info()
	print('Getting url data')
	info = yd.extract_info(url)
	print('Searching for formats')
	vidf = get_video_fmt(info, resolution, fmt)
	audf = get_audio_fmt(info, abr)
	return (vidf, audf)

def downloadYtFmts(url: str, video: int, audio: int) -> None:
	vid = YTDownloadThread(url, video, os.path.join(settings['TMP'],'1'), settings['speed'], True)
	aud = YTDownloadThread(url, audio, os.path.join(settings['TMP'],'1aud'), settings['speed'], True)
	print('Starting downloads')
	vid.start()
	sleep(15)
	aud.start()
	sleep(10)
	viewVid(settings['TMP'],'1','1aud')
	vid.join()
	aud.join()


def streamlinkDownload(url: str, resolution: int) -> None:
	"""	Trys to load stream of quality to player"""
	stream = matchStreamlinkRes(url,str(resolution)+'p')
	if stream:
		overwriteFile(settings['TMP'],'1','0')
		overwriteFile(settings['TMP'],'1aud','0aud')
		downloader = threading.Thread(
			target=downloadAStream,
			args=(stream, os.path.join(settings['TMP'],'1')),
			daemon=True
		)
		downloader.start()
		sleep(15)
		viewVid(settings['TMP'], '1')
		downloader.join()


def matchStreamlinkRes(url: str, res: str):
	streams = streamlink.streams(url)
	if res in streams:
		print("Resolution={}".format(res))
		return streams[quality]
	else:
		print("Resolution {} not available.".format(res))
		return streamlinkFmtChooser(streams)

def streamlinkFmtChooser(streams):
	print('  '.join(str(q) for q in streams))
	print('Choose alternative format from above.')
	choice = None
	while (choice not in streams):
		choice = input(':')
		if not choice:
			return
	return streams[choice]


def downloadAStream(stream, to: str) -> None:
	chunkSize = 1024
	desiredRate = settings['speed']
	sampleRate = 30
	stdDelay = (chunkSize/1024)*sampleRate/desiredRate
	#print('Standard delay: {}'.format(stdDelay))
	with stream.open() as s, open(to, 'ab') as t:
		startTime = datetime.datetime.now()
		d = s.read(chunkSize)
		i = 1
		while d:
			t.write(d)
			d = s.read(chunkSize)
			i += 1
			if i==sampleRate:
				elapsedTime = (datetime.datetime.now()-startTime).seconds
				delay = stdDelay-elapsedTime if stdDelay-elapsedTime>0 else stdDelay
				#print('Sleeping {} seconds! // {}'.format(delay,elapsedTime))
				sleep(delay)
				i = 0
				startTime = datetime.datetime.now()


def case_default(args: List[str]) -> None:
	"""	Default case.
		Downloads next item in queue.
		Auto detects what to use."""
	url = args[1] if len(args)>1 else filePop(os.path.join(settings['TMP'],q_name)) # type: str
	if url.find("youtube.com/")>=0: # its a me, youtube
		case_youtube([None,url],resume=False)
	elif url.find("crunchyroll.com/")>=0: # its a me, me
		quality = args[1] if len(args)>2 else settings["quality"]
		case_streamlink([None,url,quality])
	else:
		print("Url unrecognized or empty.")

def case_resume(args: List[str]) -> None:
	"""	Resumes download of last video. Requires url to be in args OR as next item in queue.
		Downloads regardless of wheter the url corresponds to last video."""
	print("Resuming video download.")
	case_youtube(args,resume=True)

def case_flush(args: List[str]) -> None:
	"""		Clears contents of queue. Also creates it if doesn't already exist."""
	clearFile(os.path.join(settings['TMP'],q_name))
	print("Queue was cleared.")

def case_add(args: List[str]) -> None:
	"""	Adds item to queue."""
	if len(args)>1 and len(args[1])>0:
		url = args[1]
		fileAppend(os.path.join(settings['TMP'],q_name),url)
	else:
		print("URL was blank.")

def case_top(args: List[str]) -> None:
	"""	Print next item in queue if possible."""
	qfile = os.path.join(settings['TMP'],q_name)
	if os.path.exists(qfile):
		url = filePeek(open(qfile,'r')) # type: str
		if url:
			print(url.rstrip())
			return
	print("Queue was empty.")

def case_see(args: List[str]) -> None:
	"""	Print queue contents to stdout.	"""
	qfile = os.path.join(settings['TMP'],q_name) # type: str
	if os.path.exists(qfile):
		with open(qfile,'r') as f:
			for l in f:
				print(l,end='')

def case_view(args: List[str]) -> None:
	"""	Launch viewer and player last downloaded video.	"""
	viewVid(settings['TMP'],'1','1aud')
	print("{:s} Launched.".format(settings['player']))

def case_youtube(args: List[str],resume: bool = False) -> None:
	"""	Downloads next item in queue or supplied url from args.	"""
	url = args[1] if len(args)>1 else filePop(os.path.join(settings['TMP'],q_name)) # type: str
	if not url:
		return
	fileAppend(os.path.join(settings['TMP'],q_hist_name), url)
	vidf, audf = searchYtFormats(url, settings['quality'], settings['format'], settings['abr'])
	if not audf or not vidf:
		print('Formats not found, ending.')
		return
	if not resume:
		overwriteFile(settings['TMP'],'1','0')
		overwriteFile(settings['TMP'],'1aud','0aud')
	downloadYtFmts(url, vidf, audf)

def case_streamlink(args: List[str]) -> None:
	"""	Tries to play video with streamlink & 'player'
		args in additon to 'sl' can contain URL and quality.
		args[1] is ALWAYS the quality. If getting url from q_file,
		quality must be set in enviroment."""
	url = args[1] if len(args)>1 else filePop(os.path.join(settings['TMP'],q_name)) # type: str
	quality = args[2] if len(args)>2 else settings["quality"] # type: str
	if not url or not quality:
		print("URL or quality is required but missing.")
	else:
		fileAppend(os.path.join(settings['TMP'],q_hist_name), url)
		streamlinkDownload(url,quality)

class MainParser:
	def __init__(self):
		# url as task should be intercepted in-lieu of MainParser
		self.parser = argparse.ArgumentParser('File-queue caller system')
		self.tasks = self.parser.add_subparsers(title='Subcommand', help='Task for fq_t to perform')

		self.viewTask = self.tasks.add_parser('view', help='View latest video downloaded')
		self.viewTask.set_defaults(func=case_view)
		self.seeTask = self.tasks.add_parser('see', help='View entire file queue')
		self.seeTask.set_defaults(func=case_see)
		self.topTask = self.tasks.add_parser('top', help='View first line of queue')
		self.topTask.set_defaults(func=case_top)
		self.flsTask = self.tasks.add_parser('flush', help='Clear url queue')
		self.flsTask.set_defaults(func=case_flush)
		self.addTask = self.tasks.add_parser('add', help='Add a url to file queue')
		self.addTask.set_defaults(func=case_add)
		self.addTask.add_argument('url', help='Url to add')
		self.resumeTask = self.tasks.add_parser('resume', help='Resume last download.')
		self.resumeTask.set_defaults(func=case_resume)
		self.resumeTask.add_argument('url', help='Url to resume')

	def parse(self, args):
		t = self.parser.parse_args(args)
		t.func(args)

if __name__=='__main__':
	if len(ARGV)==1:
		case_default([])
	elif len(ARGV)==2 and ARGV[1].startswith('http'):
		case_default([None, ARGV[1]])
	else:
		m = MainParser()
		m.parse(ARGV[1:])
