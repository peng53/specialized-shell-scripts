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
#	print("'int' option is useable")

player = "mpv" # type: str
player_args = ["--really-quiet", "--pause", "--keep-open"] # type: List[str]
tmp_dir = "/mnt/ramdisk" # type: str
q_name = "mq" # type: str
def_env = {"quality":"36", "speed":"40K"} # type: Dict[str,str]
yt_dl = os.path.expanduser("~/.local/bin/youtube-dl") # type: str
yt_dl_args = ["--no-part","--youtube-skip-dash-manifest","--no-call-home","--no-playlist"] # type: List[str]

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
	l = line.rstrip() # type: str
	if len(l)>0:
		with open(os.path.join(f_dir,f_name),'a') as f:
			f.write(l+'\n')

def view_vid(v_dir: str,v_name: str = "1"):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	return subprocess.run([player,os.path.join(v_dir,v_name)]+player_args).returncode

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
	speed = get_envvar("speed") # type: str
	quality = get_envvar("quality") # type: str
	cmd = [yt_dl,"-f",quality,"-r",speed,url,"-o",os.path.join(v_dir,v_name)]+yt_dl_args # type: List[str]
	print("Downloading video quality={:s} at speed={:s}".format(quality,speed))
	return subprocess.Popen(cmd)

def case_go(args: List[str],resume: bool = False) -> None:
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
	case_go(args,resume=False)

def case_resume(args: List[str]) -> None:
	case_go(args,resume=True)

def case_flush(args: List[str]) -> None:
	clear_file(tmp_dir,q_name)
	print("Queue was cleared.")

def case_add(args: List[str]) -> None:
	if len(args)>1:
		url = args[1] # type: str
		if url:
			add_bottom(q_name,tmp_dir,url)
			return
	else:
		print("URL was blank.")

def case_top(args: List[str]) -> None:
	url = top(open(os.path.join(tmp_dir,q_name),'r')) # type :str
	if url:
		print(url.rstrip())
	else:
		print("Queue was empty.")

def case_see(args: List[str]) -> None:
	with open(os.path.join(tmp_dir,q_name),'r') as f:
		for l in f:
			print(l,end='')
			#print(l)

def case_view(args: List[str]) -> None:
	print("Launching {:s}..".format(player))
	view_vid(tmp_dir)

ops = {	
#keyword function req_args
	"view": case_view,
	"see" : case_see, #0
	"top" : case_top, #0
	"fls" : case_flush, #0
	"resm": case_resume, #0
	"*"   : case_default, #0
	#"int": case_internal, #0
	"go"  : case_go, #1
	"add" : case_add, #1
} # type: Dict[str,Callable]

if len(sys.argv)<2:
	ops["*"]([])
else:
	args = sys.argv[1:] # type: List[str]
	if args[0] in ops:
		ops[args[0]](args)
