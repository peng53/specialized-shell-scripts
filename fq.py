#!/usr/bin/env python3
import sys
import os
import tempfile
import subprocess

ops = { '' : 'blue',
'bye' : 'black'
}
print(ops)

player = "mpv"
player_args = ""
tmp_dir = "/mnt/ramdisk"
q_name = "mq"


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
	f = open(tmp_f,'r')
	g = open(f_dir.rstrip('/')+'/'+f_name,'w')
	r = l = f.readline()
	while len(l)>0:
		l = f.readline()
		g.write(l)
	g.close()
	f.close()
	return r if len(r) else None

def view_vid(v_dir,v_name="1"):
	# watch the video that was downloaded.
	# uses global 'player' and 'player_args'
	# on linux, this blocks the terminal
	# returns the 'return code'
	return subprocess.run([player,player_args,v_dir.rstrip('/')+'/'+v_name]).returncode

#remove_top(q_name,tmp_dir)
print(view_vid(tmp_dir))
print("hi")
