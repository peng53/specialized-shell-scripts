#!/usr/bin/env python3
from __future__ import print_function
import sys
import os
import tempfile
import subprocess
import time
from typing import Dict
from typing import Callable
from typing import List
#try:
#	import youtube_dl
#	def try_yt(url: str,v_dir: str,v_name: str):
		#if not url:
			#print("URL was NULL.")
			#return
		#args = {
			#"format": get_envvar("quality"),
			#"noplaylist":True,
			#"call_home":False,
			#"outtmpl": unicode(os.path.join(v_dir,v_name)),
			#"tmpfilename": unicode(os.path.join(v_dir,v_name))	
		#}
		#ydl = youtube_dl.YoutubeDL(args)
		#r = ydl.extract_info(url)
		#return r
	#def case_internal(args: List[str]):
		#if len(args)>1:
			#url = args[1]
		#else:
			#url = remove_top(q_name,tmp_dir)
		#if not url:
			#sys.exit(1)
		#push_out(tmp_dir)
		#r = try_yt(url,tmp_dir,"1")
		#print(r)
		#time.sleep(25)
		#view_vid(tmp_dir)

#except:
#	print("youtube-dl api not available,")
#	print("'int' option is not useable")

player = "mpv" # type: str
player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]
tmp_dir = "/mnt/ramdisk" # type: str
q_name = "mq" # type: str
def_env = {
	"quality":"36",
	"speed":"40K",
	"slquality":"240p",
} # type: Dict[str,str]
yt_dl = os.path.expanduser("~/.local/bin/youtube-dl") # type: str
yt_dl_args = ["--no-part","--youtube-skip-dash-manifest","--no-call-home","--no-playlist"] # type: List[str]
sl_bin = os.path.expanduser("~/.local/bin/streamlink") # type: str
sl_bin_args = ["--player-no-close","--player-passthrough","hls"] # type: List[str]

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

def view_vid(v_dir: str,v_name: str = "1"):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	vid = os.path.join(v_dir,v_name)
	if os.path.exists(vid):
		return subprocess.run([player,vid]+player_args).returncode
	else:
		print("No video file exists.")
		return None

def push_out(v_dir: str,v_name: str = "1",v_name_old: str = "0") -> None:
	# displaces last vid by replacing v_name_Old with it
	old = os.path.join(v_dir,v_name_old) # type: str
	new = os.path.join(v_dir,v_name) # type: str
	if os.path.exists(old):
		os.remove(old)
	if os.path.exists(new):
		os.rename(new,old)

def clear_file(tmp_dir,q_name) -> None:
	# empties a file
	open(os.path.join(tmp_dir,q_name),'w').close()

def yt_dl_bin(url: str,v_dir: str,v_name: str ="1"):
	"""
	Downloads video with youtube-dl binary.
	"""
	speed = get_envvar("speed") # type: str
	quality = get_envvar("quality") # type: str
	cmd = [yt_dl,"-f",quality,"-r",speed,url,"-o",os.path.join(v_dir,v_name)]+yt_dl_args # type: List[str]
	print("Downloading video quality={:s} at speed={:s}".format(quality,speed))
	return subprocess.Popen(cmd)

def sl_view_bin(url: str,quality: str):
	"""
	Runs streamlink with url and quality level.
	"""
	cmd = [sl_bin,"-p",player,url,quality]+sl_bin_args
	return subprocess.run(cmd).returncode

def binary_exists(bin_path: str):
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
		#for f in os.environ["PATH"].split(os.pathsep):
		#	if bin_path in os.listdir(f):
		#		return True
		#return False
		return any(bin_path in os.listdir(f) for f in os.environ["PATH"].split(os.pathsep))
	

def case_go(args: List[str],resume: bool = False) -> None:
	"""
	Downloads next item in queue or supplied url from args.
	"""
	url = None # type: str
	if len(args)>1:
		url = args[1]
	else:
		url = remove_top(q_name,tmp_dir)
	if not url:
		return
	if not resume:
		push_out(tmp_dir)
	p = yt_dl_bin(url,tmp_dir)
	time.sleep(25)
	view_vid(tmp_dir)
	
def case_default(args: List[str]) -> None:
	"""
	Default case.
	Downloads next item in queue.
	"""
	case_go(args,resume=False)

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
	view_vid(tmp_dir)

def case_streamlink(args: List[str]) -> None:
	"""
	Tries to play video with streamlink & 'player'
	"""
	url = args[1] if len(args)>1 else remove_top(q_name,tmp_dir) # type: str
	if url:
		quality = get_envvar("slquality") # type: str
		print("Trying streamlink with quality={}".format(quality))
		sl_view_bin(url,quality)
	else:
		print("No URL was provided and queue was empty.")

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
	"sl"  : case_streamlink,
	#"int": case_internal,
} # type: Dict[str,Callable]

if len(sys.argv)<2 or not sys.argv[1] in ops:
	ops["*"]([])
else:
	args = sys.argv[1:] # type: List[str]
	ops[args[0]](args)
