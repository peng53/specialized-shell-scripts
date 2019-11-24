#!/usr/bin/env python3
from sys import exit, argv as ARGV
from typing import Dict
from typing import Callable
from typing import List
from yt_dl_urls import DownloadThread, get_audio_fmt, get_video_fmt, yt_info
import os
import argparse

def binary_exists(bin_path: str,PATH: List[str] = []) -> bool:
	"""Checks if binary exists."""
	is_full_path = '\\' in bin_path if os.name == "nt" else '/' in bin_path
	if is_full_path:
		return os.path.isfile(os.path.expanduser(bin_path))
	else:
		if not PATH:
			PATH += (f for f in os.environ["PATH"].split(os.pathsep))
		return any(bin_path in os.listdir(f) for f in PATH)

player = "mpv" # type: str
player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]

sl_bin = os.path.expanduser("~/.local/bin/streamlink") # type: str
sl_bin_args = ["--player-no-close","--player-passthrough","hls"] # type: List[str]

tmp_dir = "/mnt/ramdisk" # type: str
q_name = "mq" # type: str
q_hist_name = "q_hist" # type: str

def_env = {
	"quality": 240,
	"aquality": 80,
	"speed": 32,
	"slquality":"240p",
	"format": 'webm'
} # type: Dict[str]

if __name__=="__main__":
	for bin_path in [player,sl_bin]:
		# Exits if defined yet doesn't exists
		if bin_path and not binary_exists(bin_path):
			print("{} does not exist.".format(bin_path))
			exit(1)

from tempfile import mktemp
from subprocess import run,Popen
from time import sleep

def get_envvar(varname: str) -> str:
	# gets var value from enviroment.
	# if not present, select default from def_env dict
	# if not present there, return None.
	if varname in os.environ:
		print("Using enviroment var {}".format(varname))
		return os.environ[varname]
	elif varname in def_env:
		print("Using def var {}".format(varname))
		return def_env[varname]

def top(F) -> str:
	# F is an file in 'r' mode.
	# get first line from F. if none, return None.
	return F.readline()

def remove_top(f_name: str,f_dir: str) -> str:
	# f_name and f_dir are just strs
	# remove the first line from f_dir/f_name. (a file).
	# returns the line that was removed, if it exists, else None
	if not os.path.exists(os.path.join(f_dir,f_name)):
		print("Queue file does not exist.")
		return
	tmp_f = mktemp(dir=f_dir) # type: str
	os.rename(os.path.join(f_dir,f_name),tmp_f)
	r = None # type: str
	with open(tmp_f,'r') as f, open(os.path.join(f_dir,f_name),'w') as g:
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
		add_bottom(q_hist_name,tmp_dir, r)
		return r

def add_bottom(f_name: str,f_dir: str,line: str) -> None:
	"""Appends line to file f_name residing in f_dir."""
	l = line.rstrip() # type: str
	if l:
		with open(os.path.join(f_dir,f_name),'a') as f:
			f.write(l+'\n')

def view_vid(v_dir: str,v_name: str, a_name: str = None) -> None:
	"""	Views download media files using global var player and
		player args. Takes a_name optionally as audio track."""
	vid = os.path.join(v_dir,v_name)
	if os.path.exists(vid):
		cmd = [player,vid]+player_args
		if a_name:
			cmd.append('--audio-file='+os.path.join(v_dir,a_name))
		Popen(cmd)
	else:
		print("No video file exists.")

def push_out(v_dir: str,v_name: str = "1",v_name_old: str = "0") -> None:
	# displaces last vid by replacing v_name_old with it
	old = os.path.join(v_dir,v_name_old) # type: str
	new = os.path.join(v_dir,v_name) # type: str
	if os.path.exists(old):
		os.remove(old)
	if os.path.exists(new):
		os.rename(new,old)

def clear_file(tmp_dir,q_name) -> None:
	# empties a file
	open(os.path.join(tmp_dir,q_name),'w').close()

def case_default(args: List[str]) -> None:
	"""	Default case.
		Downloads next item in queue.
		Auto detects what to use."""
	url = args[0] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	if url.find("youtube.com/")>=0: # its a me, youtube
		case_go([None,url],resume=False)
	elif url.find("crunchyroll.com/")>=0: # its a me, me
		quality = args[1] if len(args)>2 else get_envvar("slquality")
		case_streamlink([None,url,quality])
	else:
		print("Url unrecognized or empty.")

def case_resume(args: List[str]) -> None:
	"""	Resumes download of last video. Requires url to be in args OR as next item in queue.
		Downloads regardless of wheter the url corresponds to last video."""
	print("Resuming video download.")
	case_go(args,resume=True)

def case_flush(args: List[str]) -> None:
	"""		Clears contents of queue. Also creates it if doesn't already exist."""
	clear_file(tmp_dir,q_name)
	print("Queue was cleared.")

def case_add(args: List[str]) -> None:
	"""	Adds item to queue."""
	if len(args)>1 and len(args[1])>0:
		url = args[1]
		add_bottom(q_name,tmp_dir,url)
	else:
		print("URL was blank.")

def case_top(args: List[str]) -> None:
	"""	Print next item in queue if possible."""
	qfile = os.path.join(tmp_dir,q_name)
	if os.path.exists(qfile):
		url = top(open(qfile,'r')) # type: str
		if url:
			print(url.rstrip())
			return
	print("Queue was empty.")

def case_see(args: List[str]) -> None:
	"""	Print queue contents to stdout.	"""
	qfile = os.path.join(tmp_dir,q_name) # type: str
	if os.path.exists(qfile):
		with open(qfile,'r') as f:
			for l in f:
				print(l,end='')

def case_view(args: List[str]) -> None:
	"""	Launch viewer and player last downloaded video.	"""
	view_vid(tmp_dir,'1','1aud')
	print("{:s} Launched.".format(player))

def case_go(args: List[str],resume: bool = False) -> None:
	"""	Downloads next item in queue or supplied url from args.	"""
	url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	if not url:
		return
	yd = yt_info()
	print('Getting url data')
	info = yd.extract_info(url)
	print('Searching for formats')
	vidf = get_video_fmt(info, get_envvar("quality"), get_envvar("format"))
	audf = get_audio_fmt(info, get_envvar("aquality"))
	if not audf or not vidf:
		print('Formats not found, ending.')
		return
	if not resume:
		push_out(tmp_dir,'1','0')
		push_out(tmp_dir,'1aud','0aud')

	vid = DownloadThread(url, vidf, os.path.join(tmp_dir,'1'), get_envvar('speed'), True)
	aud = DownloadThread(url, audf, os.path.join(tmp_dir,'1aud'), get_envvar('speed'), True)
	print('Starting downloads')
	vid.start()
	sleep(15)
	aud.start()
	sleep(10)
	view_vid(tmp_dir,'1','1aud')
	vid.join()
	aud.join()

try:
	import streamlink
	def interactive_format_choose(streams):
		print('  '.join(str(q) for q in streams))
		print('Choose alternative format from above.')
		choice = None
		while (choice not in streams):
			choice = input(':')
			if not choice:
				return
		return streams[choice]
	def query_formats(url: str, quality: str):
		streams = streamlink.streams(url)
		if quality in streams:
			print("Quality={}".format(quality))
			return streams[quality]
		else:
			print("Quality {} not available.".format(quality))
			return interactive_format_choose(streams)

	def try_sl(url: str,quality: str) -> None:
		"""	Trys to load stream of quality to player"""
		stream = query_formats(url,quality)
		if stream:
			run([player,stream.url]+player_args)

except ImportError:
	print("streamlink api not available.\nusing binary for sl option.")
	def try_sl(url: str,quality: str) -> None:
		"""	Runs streamlink with url and quality level.	"""
		cmd = [sl_bin,"-p",player,url,quality]+sl_bin_args
		run(cmd)

def case_streamlink(args: List[str]) -> None:
	"""	Tries to play video with streamlink & 'player'
		args in additon to 'sl' can contain URL and quality.
		args[1] is ALWAYS the quality. If getting url from q_file,
		quality must be set in enviroment."""
	url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	quality = args[2] if len(args)>2 else get_envvar("slquality") # type: str
	if not url or not quality:
		print("URL or quality is required but missing.")
	else:
		try_sl(url,quality)

class MainParser:
	def __init__(self):
		# url as task should be intercepted in-lieu of MainParser
		self.parser = argparse.ArgumentParser('File-queue caller system')
		self.tasks = self.parser.add_subparsers(title='Subcommand', help='Task for fq_t to perform')

		self.goTask = self.tasks.add_parser('go', help='Download arg or on queue')
		self.goTask.set_defaults(func=case_default)
		self.goTask.add_argument('url', help='Url to download', required=False)

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
		case_default([ARGV[1]])
	else:
		m = MainParser()
		m.parse(ARGV[1:])
