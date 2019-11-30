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

class FileQueue:
	def __init__(self, fullpath: str):
		self.fullpath = fullpath

	def front(self):
		with open(self.fullpath,'r') as f:
			return f.readline()
	
	def dequeue(self):
		tmp_f = mktemp(dir=settings['TMP']) # type: str
		os.rename(self.fullpath, tmp_f)
		r = None
		with open(tmp_f,'r') as f, open(self.fullpath,'w') as g:
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
		raise PopOnEmptyQueueException
	
	def enqueue(self, line: str):
		l = line.rstrip()
		if l:
			with open(self.fullpath, 'a') as f:
				f.write(l+'\n')
	
	def clear(self):
		open(self.fullpath,'w').close()
	
	def print_items(self):
		with open(self.fullpath,'r') as f:
			for l in f:
				print(l,end='')

class PopOnEmptyQueueException(Exception):
	pass


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
	print('Found! v {}, a {}'.format(vidf,audf))
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


def streamlinkDownload(url: str, resolution: int, resume: bool=False) -> None:
	"""	Trys to load stream of quality to player"""
	stream = matchStreamlinkRes(url,str(resolution)+'p')
	if stream:
		if resume:
			print('Resume not supported.')
			return
		else:
			overwriteFile(settings['TMP'],'1','0')
			overwriteFile(settings['TMP'],'1aud','0aud')
		downloader = threading.Thread(
			target=downloadAStream,
			args=(stream, os.path.join(settings['TMP'],'1'), resume),
			daemon=True
		)
		downloader.start()
		sleep(15)
		viewVid(settings['TMP'], '1')
		downloader.join()
		print('Download completed')


def matchStreamlinkRes(url: str, res: str):
	streams = streamlink.streams(url)
	if res in streams:
		print("Resolution={}".format(res))
		return streams[res]
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


def downloadAStream(stream, to: str, resume: bool) -> None:
	chunkSize = 1024
	desiredRate = settings['speed']
	sampleRate = 30
	stdDelay = (chunkSize/1024)*sampleRate/desiredRate
	#print('Standard delay: {}'.format(stdDelay))
	with stream.open() as s, open(to, 'ab') as t:
		if resume and s.seekable():
			pos = os.path.getsize(to)
			s.seek(pos)
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


def case_flush(args: List[str]) -> None:
	"""		Clears contents of queue. Also creates it if doesn't already exist."""
	qfile.clear()
	print("Queue was cleared.")

def case_add(args: List[str]) -> None:
	"""	Adds item to queue."""
	url = args[1]
	qfile.enqueue(url)

def case_top(args: List[str]) -> None:
	"""	Print next item in queue if possible."""
	url = qfile.front()
	if url:
		print(url.rstrip())
	else:
		print('Queue was empty')

def case_see(args: List[str]) -> None:
	"""	Print queue contents to stdout.	"""
	qfile.print_items()

def case_view(args: List[str]) -> None:
	"""	Launch viewer and player last downloaded video.	"""
	viewVid(settings['TMP'],'1','1aud')
	print("{:s} Launched.".format(settings['player']))

def case_resume(args: List[str]) -> None:
	"""	Resumes download of last video. Requires url to be in args OR as next item in queue.
		Downloads regardless of wheter the url corresponds to last video."""
	print("Resuming video download.")
	case_default(args,resume=True)

def case_default(args: List[str], resume: bool=False) -> None:
	"""	Default case.
		Downloads next item in queue."""
	url = args[1] if len(args)>1 else qfile.dequeue()
	if url:
		f = autoServicer(url)
		f(url, resume)
	else:
		serNull(url)


def autoServicer(url: str) -> Callable:
	"""Auto detects what to use."""
	searchStringsPairs = {
		"youtube.com/" : serYoutube,
		"crunchyroll.com/" : serStreamlink,
	}
	for s in searchStringsPairs:
		if url.find(s)>=0:
			return searchStringsPairs[s]
	return serNull

def serNull(url: str) -> None:
	''' Called when url doesn't match any servicer'''
	print("Url unrecognized or empty")

def serYoutube(url: str, resume: bool = False) -> None:
	"""	Downloads next item in queue or supplied url from args.	"""
	qhist.enqueue(url)
	vidf, audf = searchYtFormats(url, int(settings['quality']), settings['format'], int(settings['abr']))
	if not audf or not vidf:
		print('Formats not found, ending.')
		return
	if not resume:
		overwriteFile(settings['TMP'],'1','0')
		overwriteFile(settings['TMP'],'1aud','0aud')
	downloadYtFmts(url, vidf, audf)

def serStreamlink(url: str,resume: bool = False) -> None:
	""" Downloads video with aid from streamlink"""
	print('Using streamlink with URL={}'.format(url))
	qhist.enqueue(url)
	streamlinkDownload(url,int(settings["quality"]), resume)

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
	qfile = FileQueue(os.path.join(settings['TMP'],q_name))
	qhist = FileQueue(os.path.join(settings['TMP'],q_hist_name))
	if len(ARGV)==1:
		case_default([])
	elif len(ARGV)==2 and ARGV[1].startswith('http'):
		case_default([None, ARGV[1]])
	else:
		m = MainParser()
		m.parse(ARGV[1:])
