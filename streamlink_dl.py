#!/usr/bin/env python3
from streamlink import streams
from argparse import ArgumentParser
from datetime import datetime
from time import sleep
import sys
import os

def downloadAStream(stream, to: str, speed: float, delayFail=True) -> None:
	print('Using 32kb chunk download variant')
	chunkSize = 1024*32 # type: int # 32kb chunks
	desiredRate = speed # type: float
	delay = 32/desiredRate # type: float # time in between each 32kb chunk
	start = datetime.now()
	progI = True
	try:
		with stream.open() as s, open(to, 'ab') as t:
			d = s.read(chunkSize)
			print('/\r', end='')
			while d:
				try:
					t.write(d)
				except OSError:
					if delayFail:
						print('No space! Waiting 10s!')
						sleep(10)
						t.write(d)
					else:
						raise Exception
				sleep(delay)
				print('\\\r' if progI else '/\r', end='')
				progI = not progI
				d = s.read(chunkSize)
	finally:
		end = datetime.now()
		size = os.path.getsize(to)/1024 # type: int # size in kb
		downloadTime = (end-start).seconds # type: int
		print(f'Download of {size} took {downloadTime} seconds: {size/downloadTime:.3}kb/s')

class MainParser:
	def __init__(self):
		self.parser = ArgumentParser('Streamlink download-limiter')
		self.url = self.parser.add_argument('-u', '--url', help='Url to download', required=True)
		self.fmt = self.parser.add_argument('-f', '--fmt', help='Format to choose', required=True)
		self.rate = self.parser.add_argument('-r', '--rate', help='Download rate at which to download at', required=True, type= float)
		self.out =  self.parser.add_argument('-o', '--out', help='Output file', required=True)

	def download(self, args) -> None:
		t = self.parser.parse_args(args)
		if os.path.exists(t.out):
			print("Output file already exists.")
			return 3
		try:
			stream = streams(t.url)
		except:
			print("Url doesn't exist.")
			return 1
		try:
			url = stream[t.fmt]
		except:
			print("Url or quality doesn't exist.")
			print("Possible choices are:")
			print('\n'.join(q for q in stream))
			return 2
		downloadAStream(url, t.out, t.rate)
		return 0

if __name__=='__main__':
	mp = MainParser()
	r = mp.download(sys.argv[1:])
	sys.exit(r)
