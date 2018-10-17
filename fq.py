#!/usr/bin/env python
import sys
import os
import tempfile
import subprocess
import time
#import youtube_dl

player = "mpv"
player_args = "--really-quiet"
tmp_dir = "/mnt/ramdisk"
q_name = "mq"
def_env = {"quality":"36", "speed":"40K"}
yt_dl = os.path.realpath("~/.local/bin/youtube-dl")
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
	os.rename(f_dir.rstrip('/')+'/'+f_name,tmp_f)
	r = None
	with open(tmp_f,'r') as f, open(f_dir.rstrip('/')+'/'+f_name,'w') as g:
		r = l = f.readline()
		while l:
			l = f.read(1024)
			g.write(l)
	os.remove(tmp_f)
	return r.rstrip() if r else None

def add_bottom(f_name,f_dir,line):
	l = line.rstrip()
	if len(l)>0:
		f = open(f_dir.rstrip('/')+'/'+f_name,'a')
		f.write(l+'\n')
		f.close()

def view_vid(v_dir,v_name="1"):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	return subprocess.run([player,player_args,v_dir.rstrip('/')+'/'+v_name]).returncode

def push_out(v_dir,v_name="1",v_name_old="0"):
	# displaces last vid by replacing v_name_Old with it
	t_dir = v_dir.rstrip('/')+'/'
	if os.path.exists(t_dir+v_name_old):
		os.remove(t_dir+v_name_old)
	os.rename(t_dir+v_name,t_dir+v_name_old)

def clear_file(tmp_dir,q_name):
	# empties a file
	open(tmp_dir.rstrip('/')+'/'+q_name,'w').close()

def yt_dl_bin(url,v_dir,v_name="1"):
	cmd = [yt_dl,"-f",get_envvar("quality"),"-r",get_envvar("speed"),url,"-o",v_dir.rstrip('/')+'/'+v_name]+yt_dl_args
	return subprocess.Popen(cmd)

def try_yt(v_dir,v_name="1"):
	ytdl = {
		"format":"36",
		"noplaylist":True,
		"call_home":False,
		"filename": v_dir.rstrip('/')+'/'+v_name,
		"tmpfilename": v_dir.rstrip('/')+'/'+v_name,
		
	}

def case_go(url,resume=False):
	if not resume:
		push_out(tmp_dir)
	p = yt_dl_bin(url,tmp_dir)
	time.sleep(25)
	view_vid(tmp_dir)
	
def case_default():
	u = remove_top(q_name,tmp_dir)
	if u:
		return case_go(u)
	else:
		print("Queue was empty.")

def case_resume(url=None):
	if not url:
		url = remove_top(q_name,tmp_dir)
	if url:
		return case_go(url,resume=True)
	else:
		print("No URL to resume.")

def case_flush():
	clear_file(tmp_dir,q_name)

def case_add(url):
	if url:
		add_bottom(q_name,tmp_dir,url)
	else:
		print("URL was blank.")

def case_top():
	return top(open(tmp_dir.rstrip('/')+'/'+q_name,'r'))

def case_see():
	with open(tmp_dir.rstrip('/')+'/'+q_name,'r') as f:
		for l in f:
			print(l)

def case_view():
	return view_vid(tmp_dir)

#remove_top(q_name,tmp_dir)
#print(view_vid(tmp_dir))
#add_bottom(q_name,tmp_dir,"my_line")
#print(yt_dl_bin("https://www.youtube.com/watch?v=so_Ib0ErkQU",tmp_dir))
#case_default()

if len(sys.argv)<2:
	# 0th is name of script
	# 1th+ are the options
	sys.exit(1)

ops0 = {	#keyword function req_args
	"view": case_view,
	"see" : case_see, #0
	"top" : case_top, #0
	"fls" : case_flush, #0
	"resm": case_resume, #0
	"*"   : case_default, #0
}
ops1 = {
	"go"  : case_go, #1
	"add" : case_add, #1
}
cmd = sys.argv[1].lower()
if cmd in ops0:
	ops0[cmd]()
elif cmd in ops1:
	ops1[cmd](sys.argv[2])

