# -*- coding: future_fstrings -*-
#!/usr/bin/env python3
from sys import argv as ARGV
from typing import Dict, Callable, List, Tuple
from tempfile import mktemp
from subprocess import Popen
from time import sleep
from threading import Thread
from datetime import datetime
from argparse import ArgumentParser
from typing import List
import os
import signal

settings = {
	"quality": 240,
	"abr": 80,
	"speed": 56,
	"format": ['webm'],
	'player': 'mpv',
	'TMP': "/mnt/ramdisk",
} # type: Dict[str]

for key in settings:
	if key in os.environ:
		settings[key] = os.environ[key]

if 'slplugops' in os.environ:
	# transforms 'x:1:a:2,t:4' to
	# x:1, a:2, t:4
	slplugops = os.environ['slplugops'].split(':')
	slplugops = {slplugops[i]:slplugops[i+1] for i in range(0,len(slplugops),2)}
else:
	slplugops = {}

player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]
q_name = "mq" # type: str
q_hist_name = "q_hist" # type: str

class FileQueue:
	def __init__(self, fullpath: str):
		self.fullpath = fullpath

	def front(self) -> str:
		with open(self.fullpath,'r') as f:
			return f.readline()

	def dequeue(self) -> str:
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

	def enqueue(self, line: str) -> None:
		l = line.rstrip()
		if l:
			with open(self.fullpath, 'a') as f:
				f.write(l+'\n')

	def clear(self) -> None:
		open(self.fullpath,'w').close()

	def print_items(self) -> None:
		try:
			with open(self.fullpath,'r') as f:
				for l in f:
					print(l,end='')
		except:
			print('Queue is empty (non-existent)')

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


def overwriteFile(v_dir: str,v_name: str,v_name_old: str) -> None:
	''' displaces last vid by replacing v_name_old with it '''
	old = os.path.join(v_dir,v_name_old) # type: str
	new = os.path.join(v_dir,v_name) # type: str
	if os.path.exists(old):
		os.remove(old)
	if os.path.exists(new):
		os.rename(new,old)


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
	print(f"{settings['player']} Launched.")

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
		"funimation.com/" : serStreamlink,
	}
	for s in searchStringsPairs:
		if url.find(s)>=0:
			return searchStringsPairs[s]
	return serNull

def serNull(url: str) -> None:
	''' Called when url doesn't match any servicer'''
	print("Url unrecognized or empty")


def serYoutube(url: str, resume: bool = False) -> None:
	from yt_dl_urls import exist_dash_yt
	qhist.enqueue(url)
	print('Searching formats..')
	fmts = exist_dash_yt(url, int(settings['quality']), settings['format'], int(settings['abr']))
	if not fmts:
		print('Formats not found, ending.')
		return
	if not resume:
		overwriteFile(settings['TMP'],'1','0')
		overwriteFile(settings['TMP'],'1aud','0aud')
	downloader = downloadYtFmtsThread(url, fmts)
	downloader.start()
	print('Downloading..')
	sleep(40)
	print('Playing video..')
	viewVid(settings['TMP'],'1','1aud')
	downloader.join()
	print('Download complete!')

def downloadYtFmtsThread(url: str, fmts: Tuple[str,str]) -> Thread:
	from yt_dl_urls import download_by_threads, FmtInfo
	return Thread(
		target=download_by_threads,
		args=(
			url,
			FmtInfo(fmts[0], os.path.join(settings['TMP'], '1'), float(settings['speed'])),
			FmtInfo(fmts[1], os.path.join(settings['TMP'], '1aud'), float(settings['speed']))
		)
	)

def serStreamlink(url: str,resume: bool = False) -> None:
	""" Downloads video with aid from streamlink"""
	print(f'Using streamlink with URL={url}')
	qhist.enqueue(url)

	if url.find("crunchyroll.com/") >= 0 and 'cr_session' in slplugops:
		from crunchyroll_sl import streams as streams_F
		streams = lambda url: streams_F(url, session_id=slplugops['cr_session'])
	elif url.find("funimation.com/") >= 0 and 'fu_session' in slplugops\
	and 'fu_login' in slplugops:
		from funimation_sl import streams as streams_F
		email,pword = slplugops['fu_login'].split('=',1)
		streams = lambda url: streams_F(url, cookie=slplugops['fu_session'], email=email, pword=pword)
	else:
		from streamlink import streams as streams_F
		streams = lambda url: streams_F(url)

	stream = matchStreamlinkRes(url,str(settings['quality'])+'p', streams)
	if not stream:
		return
	signal.signal(signal.SIGINT, lambda signum, frame: exit(1))
	joiner = streamlinkDownload(stream, os.path.join(settings['TMP'],'1'), resume)
	if joiner:
		viewVid(settings['TMP'],'1')
		joiner.join()

def matchStreamlinkRes(url: str, res: str, streams: Callable):
	streams = streams(url)
	if res in streams:
		print(f"Resolution={res}")
		return streams[res]
	else:
		print(f"Resolution {res} not available.")
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

def streamlinkDownload(stream, to: str, resume: bool=False) -> Thread:
	"""	Trys to load stream of quality to player"""
	from streamlink_dl import downloadAStream
	if resume:
		print('Resume not supported.')
		return
	else:
		overwriteFile(settings['TMP'],'1','0')
		overwriteFile(settings['TMP'],'1aud','0aud')
	joiner = Thread(
		target=downloadAStream,
		args=(stream, to, float(settings['speed'])),
		daemon=True
	)
	joiner.start()
	sleep(15)
	return joiner

class MainParser:
	def __init__(self):
		# url as task should be intercepted in-lieu of MainParser
		self.parser = ArgumentParser('File-queue caller system')
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

	def parse(self, args) -> None:
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
