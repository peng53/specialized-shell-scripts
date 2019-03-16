#!/bin/env python
import sys

if __name__!="__main__" or len(sys.argv)<2:
	sys.exit()

from typing import Dict
from typing import Tuple
from typing import Callable
from typing import List
from subprocess import Popen

def matches_file_ext(filename: str, exts: List[str]) -> bool:
	return any(filename.endswith(ext) for ext in exts)

class CallOption:
	def __init__(self, test: Callable[[str],bool], action: str, args: str = ''):
		self.test = test
		self.action = action
		self.args = args
	

import os

alias = {
	"fq9" : os.path.join(os.path.dirname(os.path.abspath(__file__)),"fq9")
}
call_type = {
	"image" : CallOption(lambda p: matches_file_ext(p, ['.jpg','.jpeg','.png','.gif']),"feh"),
	"video" : CallOption(lambda p: matches_file_ext(p, ['.mp4','.avi','.flv']),"mpv"),
	"youtube" : CallOption(lambda p: "youtube.com/watch?v=" in p, alias["fq9"], "add"),
	"crunchyroll" : CallOption(lambda p: ".crunchyroll.com/" in p, alias["fq9"], "add")
}

url = sys.argv[1] # type: str
action = None
args = None

for t in call_type:
	if call_type[t].test(url):
		action, args = call_type[t].action, call_type[t].args
		break

if not action:
	action = "xlinks2"

Popen([action, args, url])
