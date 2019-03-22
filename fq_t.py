#!/usr/bin/env python3
import sys
import os
from typing import Dict
from typing import Callable
from typing import List

def binary_exists(bin_path: str,PATH: List[str] = []) -> bool:
	"""
	Checks if binary exists.
	"""
	is_win = (os.name == "nt")
	is_full_path = None
	if is_win:
		is_full_path = '\\' in bin_path
	else:
		is_full_path = '/' in bin_path
	if is_full_path:
		return os.path.isfile(os.path.expanduser(bin_path))
	else:
		if not PATH:
			for f in os.environ["PATH"].split(os.pathsep):
				PATH.append(f)
		return any(bin_path in os.listdir(f) for f in PATH)

player = "mpv" # type: str
player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]
yt_dl = os.path.expanduser("~/.local/bin/youtube-dl") # type: str
yt_dl_args = ["--no-part","--youtube-skip-dash-manifest","--no-call-home","--no-playlist"] # type: List[str]
sl_bin = os.path.expanduser("~/.local/bin/streamlink") # type: str
sl_bin_args = ["--player-no-close","--player-passthrough","hls"] # type: List[str]

tmp_dir = "/mnt/ramdisk" # type: str
q_name = "mq" # type: str
def_env = {
	"quality":"242",
	"aquality":"250",
	"speed":"32K",
	"slquality":"240p",
} # type: Dict[str,str]

if __name__=="__main__":
	for bin_path in [player,yt_dl,sl_bin]:
		if bin_path and not binary_exists(bin_path):
			print("{} does not exist.".format(bin_path))
			sys.exit(1)

import tempfile
import subprocess
import time

def get_envvar(varname: str) -> str:
	# gets var value from enviroment.
	# if not present, select default from def_env dict
	# if not present there, return None.
	if varname in os.environ:
		return os.environ[varname]
	elif varname in def_env:
		return def_env[varname]
	else:
		return None

def top(F) -> str:
	# F is an file in 'r' mode.
	# get first line from F. if none, return None.
	l = F.readline() # type: str
	return l if len(l) else None

def remove_top(f_name: str,f_dir: str) -> str:
	# f_name and f_dir are just strs
	# remove the first line from f_dir/f_name. (a file).
	# returns the line that was removed, if it exists, else None
	if not os.path.exists(os.path.join(f_dir,f_name)):
		print("Queue file does not exist.")
		return None
	tmp_f = tempfile.mktemp(dir=f_dir) # type: str
	os.rename(os.path.join(f_dir,f_name),tmp_f)
	r = None # type: str
	with open(tmp_f,'r') as f, open(os.path.join(f_dir,f_name),'w') as g:
		l = f.readline() # type: str
		r = l
		while l:
			l = f.read(1024)
			g.write(l)
	os.remove(tmp_f)
	return r.rstrip() if r else None

def add_bottom(f_name: str,f_dir: str,line: str) -> None:
	"""
	Appends line to file f_name residing in f_dir.
	"""
	l = line.rstrip() # type: str
	if len(l)>0:
		with open(os.path.join(f_dir,f_name),'a') as f:
			f.write(l+'\n')

def view_vid(v_dir: str,v_name: str, a_name: str = None):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	vid = os.path.join(v_dir,v_name)
	if os.path.exists(vid):
		cmd = [player,vid]+player_args
		if a_name:
			cmd.append('--audio-file='+os.path.join(v_dir,a_name))
		return subprocess.run(cmd).returncode
	else:
		print("No video file exists.")
		return None

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

def yt_dl_bin(url: str, dformat: str, v_dir: str,v_name: str ="1"):
	"""
	Downloads video with youtube-dl binary.
	"""
	speed = get_envvar("speed") # type: str
	cmd = [yt_dl,"-q","-f",dformat,"-r",speed,url,"-o",os.path.join(v_dir,v_name)]+yt_dl_args # type: List[str]
	print("Downloading video quality={:s} at speed={:s}".format(dformat,speed))
	return subprocess.Popen(cmd)

def case_go(args: List[str],resume: bool = False) -> None:
	"""
	Downloads next item in queue or supplied url from args.
	"""
	url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	if not url:
		return
	if not resume:
		push_out(tmp_dir,'1','0')
		push_out(tmp_dir,'1aud','0aud')
	vid = yt_dl_bin(url,get_envvar("quality"),tmp_dir)
	time.sleep(15)
	aud = yt_dl_bin(url,get_envvar("aquality"),tmp_dir,"1aud")
	time.sleep(10)
	view_vid(tmp_dir,'1','1aud')
	
def case_default(args: List[str]) -> None:
	"""
	Default case.
	Downloads next item in queue.
	Auto detects what to use.
	"""
	url = args[0] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	if not url:
		return
	if url.find("youtube.com/")>=0: # its a me, youtube
		case_go([None,url],resume=False)
	elif url.find("crunchyroll.com/")>=0: # its a me, me
		quality = args[1] if len(args)>2 else get_envvar("slquality")
		case_streamlink([None,url,quality])
	else:
		print("Unrecognized url?")

def case_resume(args: List[str]) -> None:
	"""
	Resumes download of last video. Requires url to be in args OR as next item in queue.
	Downloads regardless of wheter the url corresponds to last video.
	"""
	print("Resuming video download.")
	case_go(args,resume=True)

def case_flush(args: List[str]) -> None:
	"""
	Clears contents of queue. Also creates it if doesn't already exist.
	"""
	clear_file(tmp_dir,q_name)
	print("Queue was cleared.")

def case_add(args: List[str]) -> None:
	"""
	Adds item to queue."""
	if len(args)>1:
		url = args[1] # type: str
		if url:
			add_bottom(q_name,tmp_dir,url)
			return
	else:
		print("URL was blank.")

def case_top(args: List[str]) -> None:
	"""
	Print next item in queue if possible.
	"""
	qfile = os.path.join(tmp_dir,q_name)
	if os.path.exists(qfile):
		url = top(open(qfile,'r')) # type: str
		if url:
			print(url.rstrip())
			return
	print("Queue was empty.")

def case_see(args: List[str]) -> None:
	"""
	Print queue contents to stdout.
	"""
	qfile = os.path.join(tmp_dir,q_name) # type: str
	if os.path.exists(qfile):
		with open(qfile,'r') as f:
			for l in f:
				print(l,end='')

def case_view(args: List[str]) -> None:
	"""
	Launch viewer and player last downloaded video.
	"""
	print("Launching {:s}..".format(player))
	view_vid(tmp_dir,'1','1aud')

ops = {
#keyword function req_args
	"view": case_view,
	"see" : case_see,
	"top" : case_top,
	"fls" : case_flush,
	"resm": case_resume,
	"*"   : case_default,
	"go"  : case_go,
	"add" : case_add,
} # type: Dict[str,Callable]

try:
	import youtube_dl
	def try_yt(url: str,dformat: str,v_dir: str,v_name: str):
		"""
		Uses youtube-dl's api to download and watch the video.
		"""
		args = {
			"format": dformat,
			"noplaylist":True,
			"call_home":False,
			"outtmpl": os.path.join(v_dir,v_name),
			"tmpfilename": os.path.join(v_dir,v_name),
		}
		ydl = youtube_dl.YoutubeDL(args)
		r = ydl.extract_info(url)
		return r
	def case_internal(args: List[str]) -> None:
		"""
		Calls try_yt with needed args.
		"""
		url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
		if not url:
			return
		push_out(tmp_dir)
		v = try_yt(url,get_envvar("quality"),tmp_dir,"1")
		print(v)
		time.sleep(15)
		a = try_yt(url,get_envvar("aquality"),tmp_dir,"1aud")
		print(a)
		time.sleep(15)
		view_vid(tmp_dir,'1','1aud')
	ops["int"] = case_internal

except ImportError:
	print("youtube-dl api not available,")
	print("'int' option is not useable")

try:
	import streamlink
	def query_formats(url: str, quality: str=None):
		streams = streamlink.streams(url)
		if quality:
			return streams[quality] if quality in streams else None
		else:
			return [str(q for q in streams)]
	def try_sl(url: str,quality: str):
		"""
		Trys to load stream of quality to player
		"""
		stream = query_formats(url,quality)
		if stream:
			return subprocess.run([player,stream.url]+player_args).returncode
		else:
			print("Not available in quality={}".format(quality))
	def case_streamlink(args: List[str]) -> None:
		"""
		Provides required parameters to streamlink
		"""
		url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
		quality = args[2] if len(args)>2 else get_envvar("slquality")
		if not url or not quality:
			print("URL or quality is required but missing.")
			return
		try_sl(url,quality)
	
except ImportError:
	print("streamlink api not available.\nusing binary for sl option.")
	def sl_view_bin(url: str,quality: str):
		"""
		Runs streamlink with url and quality level.
		"""
		cmd = [sl_bin,"-p",player,url,quality]+sl_bin_args
		return subprocess.run(cmd).returncode

	def case_streamlink(args: List[str]) -> None:
		"""
		Tries to play video with streamlink & 'player'
		args in additon to 'sl' can contain URL and quality.
		args[1] is ALWAYS the quality. If getting url from q_file,
		quality must be set in enviroment.
		"""
		url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
		if url:
			quality = args[2] if len(args)>2 else get_envvar("slquality") # type: str
			print("Trying streamlink with quality={}".format(quality))
			sl_view_bin(url,quality)
		else:
			print("No URL was provided and queue was empty.")

ops["sl"] = case_streamlink

if __name__=="__main__":
	if len(sys.argv)<2 or not sys.argv[1] in ops:
		ops["*"]([])
	else:
		args = sys.argv[1:] # type: List[str]
		ops[args[0]](args)
