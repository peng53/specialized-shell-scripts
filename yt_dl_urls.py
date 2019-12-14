# -*- coding: future_fstrings -*-
from sys import argv, exit
from time import sleep
from typing import Tuple, List
import argparse
import youtube_dl
import os
import threading
import requests
from datetime import datetime
from collections import namedtuple

def yt_info():
	''' Returns YoutubeDL object for searching formats '''
	return youtube_dl.YoutubeDL(
		{
		"call_home": False,
		"quiet": True,
		'skip_download': True
		}
	)

FmtInfo = namedtuple('YTFmtInfo', 'code, path, speed') # type: Tuple[str,str,float]

def download_dash_yt(url: str, vheight: int, vfmt: str, abr: int, outdir: str, names: Tuple[str,str], speed: float=45) -> int:
	fmts = exist_dash_yt(url, vheight, vfmt, abr)
	if not fmts:
		return 1
	download_by_threads(
		url,
		FmtInfo(fmts[0], os.path.join(outdir, names[0]), speed),
		FmtInfo(fmts[1], os.path.join(outdir, names[1]), speed),
	)
	return 0

def download_by_threads(url: str, vidInfo: FmtInfo, audInfo: FmtInfo):
	vidt = yt_download_thread(url, vidInfo.code, vidInfo.path, vidInfo.speed)
	vidt.start()
	yt_download_fmt(url, audInfo.code, audInfo.path, audInfo.speed) # audio download
	vidt.join()

def exist_dash_yt(url: str, vheight: int, vfmt: str, abr: int):
	''' Returns whether such a dash video/audio
		combo exists and if so return them'''
	info = yt_info().extract_info(url)
	vidf = get_video_fmt(info, vheight, vfmt)
	if vidf:
		audf = get_audio_fmt(info, abr)
		if audf:
			return (vidf,audf)
	return None

def get_video_fmt(info, vheight: int, vfmt: str):
	''' Return video fmt with vheight and vfmt '''
	vids = filter(lambda d: d['vcodec']!='none' and d['acodec']=='none' and d['ext']==vfmt, info['formats'])
	vmatch = next(filter(lambda v: int(v['height'])==vheight, vids), None)
	return vmatch['format_id'] if vmatch else None

def get_audio_fmt(info, abr: int):
	''' Returns audio fmt with abr equal or less than desired abr'''
	auds = filter(lambda d: d['vcodec']=='none' and d['acodec']!='none', info['formats'])
	matches = filter(lambda d: d['abr'] <= abr, auds)
	codes_n_abr = ((m['format_id'], m['abr']) for m in matches)
	amatch = max(codes_n_abr, key=lambda x: x[1], default=None)
	return amatch[0] if amatch else None


def tandem_downloads(urls: List, outputs: List, ratelimit: float) -> None:
	if len(urls)!=len(outputs):
		raise Exception # tbd
	chunkSize = 32*1024 # type: float
	delay = chunkSize/(ratelimit*1024) # type: float # time in between each 32kb chunk
	downloads = [ChunkStreamDownloader(u, o, chunkSize) for (u,o) in zip(urls, outputs)]
	while downloads:
		for d in downloads:
			d.dlChunk()
		downloads = list(filter(lambda x: x.hasdata==True, downloads))
		if downloads:
			sleep(delay)

class ChunkStreamDownloader:
	def __init__(self, url: str, out: str, chunkSize: float):
		self.req = requests.get(url, stream=True)
		self.fout = open(out, 'wb')
		self.data = self.req.iter_content(chunk_size=chunkSize)
		self.hasdata = True

	def __del__(self):
		self.req.close()
		self.fout.close()

	def dlChunk(self):
		if self.hasdata:
			try:
				d = next(self.data)
				self.fout.write(d)
			except StopIteration:
				self.hasdata = False

def yt_download_thread(url: str, fmt: str, out: str, speed: float) -> threading.Thread:
	return threading.Thread(
		target=yt_download_fmt,
		args=(url, fmt, out, speed),
		daemon=True,
	)

def yt_download_fmt(url: str, fmt: str, out: str, ratelimit: float, quiet: bool=True):
	downloader = yt_download_obj(fmt,out,ratelimit,quiet)
	downloader.download([url])

def yt_download_obj(fmt: str, out: str, ratelimit: float, quiet: bool=True):
	''' Returns YoutubeDL object meant for downloading'''
	return youtube_dl.YoutubeDL(
		{
			"call_home": False,
			'nopart': True,
			'continuedl': True,
			'format': fmt,
			'outtmpl': out,
			'ratelimit': ratelimit*1024,
			"quiet": quiet,
		}
	)

class FileAlreadyExistsException(Exception):
	pass

class MainParser:
	def __init__(self):
		self.parser = argparse.ArgumentParser('Perform certain tasks with youtube-dl api')
		self.parser.add_argument('-v', '--verbose', help='Causes more output to stdout', action='store_true')
		self.parser.add_argument('task', type=str, help='Task to be completed with URL', choices=['exists', 'download'])
		self.vidparams = self.parser.add_argument_group('Video Params', description='params that describe the desired video.')
		self.vidparams.add_argument('url', type=str, help='Video URL')
		self.vidparams.add_argument('-F', '--fmt', type=str, help='File format', default='webm')
		self.vidparams.add_argument('--res', type=int, help='Video vertical resolution')
		self.vidparams.add_argument('-a', '--abr', type=int, help='Max audio bitrate')

		self.vidparams.add_argument('-o', '--out', type=str, help='Download directory', default=os.getcwd())
		self.vidparams.add_argument('-r', '--rate', type=int, help='Download rate in KB/S', default=None)

	def parse(self, args):
		return self.parser.parse_args(args)


def main(argv):
	t = MainParser().parse(argv[1:])
	if t.task=='exists':
		fmts = exist_dash_yt(t.url, t.res, t.fmt, t.abr)
		if t.verbose:
			if fmts:
				print(f'Combo exists! (vid,aud): {fmts}')
			else:
				print(f'No combo exists with res={t.res}, fmt={t.fmt}, and abr={t.abr}')
		return 0 if fmts else 1
	elif t.task=='download':
		names = ('1','1aud')
		for fn in names:
			if os.path.exists(os.path.join(t.out, fn)):
				if t.verbose:
					print(f'{os.path.join(t.out,fn)} already exists')
				return 2
		if t.verbose:
			print('Starting downloads')
		return download_dash_yt(t.url, t.res, t.fmt, t.abr, t.out, names, t.rate)
	return 0

if __name__=='__main__':
	exit(main(argv))
