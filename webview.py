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
	def __init__(self, name: str, test: Callable[[str],bool], action: str, args: str = None):
		self.name = name
		self.test = test
		self.action = action
		self.args = args
	

import os

alias = {
	"fq9" : os.path.join(os.path.dirname(os.path.abspath(__file__)),"fq9")
}

call_type = [
	CallOption(
		"image",
		lambda p: matches_file_ext(p, ['.jpg','.jpeg','.png','.gif']),
		"feh"),
	CallOption(
		"video",
		lambda p: matches_file_ext(p, ['.mp4','.avi','.flv']),
		"mpv"),
	CallOption(
		"youtube",
		lambda p: "youtube.com/watch?v=" in p,
		alias["fq9"],
		"add"),
	CallOption(
		"crunchyroll",
		lambda p: ".crunchyroll.com/" in p,
		alias["fq9"],
		"add"),
]

url = sys.argv[1] # type: str
cmd = "xlinks2" # type: str

for t in call_type:
	if t.test(url):
		cmd = t.action+' '+t.args if t.args else t.action # type: str
		break

Popen([cmd, url])
