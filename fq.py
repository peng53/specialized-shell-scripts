#!/usr/bin/env python3
from __future__ import print_function
import sys
import os
import tempfile
import subprocess
import time
try:
	import youtube_dl
except:
	print("youtube-dl api not available,")
	print("'int' option is useable")

player = "mpv"
player_args = ["--really-quiet","--keep-open","--pause"]
tmp_dir = "/mnt/ramdisk"
q_name = "mq"
def_env = {"quality":"36", "speed":"40K"}
yt_dl = os.path.expanduser("~/.local/bin/youtube-dl")
yt_dl_args = ["--no-part","--youtube-skip-dash-manifest","--no-call-home","--no-playlist"]

def get_envvar(varname):
	# gets var value from enviroment.
	# if not present, select default from def_env dict
	# if not present there, return None.
	if varname in os.environ:
		return os.environ[varname]
	elif varname in def_env:
		return def_env[varname]
	else:
		return None

def top(F):
	# F is an file in 'r' mode.
	# get first line from F. if none, return None.
	l = F.readline()
	return l if len(l) else None

def remove_top(f_name,f_dir):
	# f_name and f_dir are just strs
	# remove the first line from f_dir/f_name. (a file).
	# returns the line that was removed, if it exists, else None
	tmp_f = tempfile.mktemp(dir=f_dir)
	os.rename(os.path.join(f_dir,f_name),tmp_f)
	r = None
	with open(tmp_f,'r') as f, open(os.path.join(f_dir,f_name),'w') as g:
		r = l = f.readline()
		while l:
			l = f.read(1024)
			g.write(l)
	os.remove(tmp_f)
	return r.rstrip() if r else None

def add_bottom(f_name,f_dir,line):
	l = line.rstrip()
	if len(l)>0:
		with open(os.path.join(f_dir,f_name),'a') as f:
			f.write(l+'\n')

def view_vid(v_dir,v_name="1"):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	#return subprocess.run([player,os.path.join(v_dir,v_name)]+player_args).returncode
	return subprocess.Popen([player,os.path.join(v_dir,v_name)]+player_args)

def push_out(v_dir,v_name="1",v_name_old="0"):
	# displaces last vid by replacing v_name_Old with it
	old = os.path.join(v_dir,v_name_old)
	new = os.path.join(v_dir,v_name)
	if os.path.exists(old):
		os.remove(old)
	if os.path.exists(new):
		os.rename(new,old)

def clear_file(tmp_dir,q_name):
	# empties a file
	open(os.path.join(tmp_dir,q_name),'w').close()

def yt_dl_bin(url,v_dir,v_name="1"):
	speed = get_envvar("speed")
	quality = get_envvar("quality")
	cmd = [yt_dl,"-f",quality,"-r",speed,url,"-o",os.path.join(v_dir,v_name)]+yt_dl_args
	print("Downloading video quality={:s} at speed={:s}".format(quality,speed))
	return subprocess.Popen(cmd)

def try_yt(url,v_dir,v_name):
	if not url:
		print("URL was NULL.")
		return
	args = {
		"format": get_envvar("quality"),
		"noplaylist":True,
		"call_home":False,
		"outtmpl": unicode(os.path.join(v_dir,v_name)),
		"tmpfilename": unicode(os.path.join(v_dir,v_name))	
	}
	ydl = youtube_dl.YoutubeDL(args)
	r = ydl.extract_info(url)
	return r

def case_go(args,resume=False):
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
	
def case_default(args):
	return case_go(args,resume=False)

def case_resume(args):
	return case_go(args,resume=True)

def case_flush(args):
	clear_file(tmp_dir,q_name)
	print("Queue was cleared.")

def case_add(args):
	if len(args)>1:
		url = args[1]
		if url:
			add_bottom(q_name,tmp_dir,url)
			return
	else:
		print("URL was blank.")

def case_top(args):
	url = top(open(os.path.join(tmp_dir,q_name),'r'))
	if url:
		print(url.rstrip())
	else:
		print("Queue was empty.")

def case_see(args):
	with open(os.path.join(tmp_dir,q_name),'r') as f:
		for l in f:
			#print(l,end='')
			print(l)

def case_view(args):
	print("Launching {:s}..".format(player))
	return view_vid(tmp_dir)

def case_internal(args):
	if len(args)>1:
		url = args[1]
	else:
		url = remove_top(q_name,tmp_dir)
	if not url:
		sys.exit(1)
	push_out(tmp_dir)
	r = try_yt(url,tmp_dir,"1")
	print(r)
	time.sleep(25)
	view_vid(tmp_dir)

ops = {	#keyword function req_args
	"view": case_view,
	"see" : case_see, #0
	"top" : case_top, #0
	"fls" : case_flush, #0
	"resm": case_resume, #0
	"*"   : case_default, #0
	"int": case_internal, #0
	"go"  : case_go, #1
	"add" : case_add, #1
}

if len(sys.argv)<2:
	ops["*"]([])
else:
	args = sys.argv[1:]
	print(args)
	if args[0] in ops:
		ops[args[0]](args)
