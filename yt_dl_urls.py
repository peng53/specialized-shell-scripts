from sys import argv, exit
from time import sleep
from typing import Tuple
import argparse
import youtube_dl
import os
import threading


def yt_info():
	''' Returns YoutubeDL object for searching formats '''
	return youtube_dl.YoutubeDL(
		{
		"call_home": False,
		"quiet": True,
		'skip_download': True
		}
	)

def download_dash_yt(url: str, vheight: int, vfmt: str, abr: int, outdir: str, names: Tuple[str,str], speed: float=45):
	fmts = exist_dash_yt(url, vheight, vfmt, abr)
	if not fmts:
		return 1
	vidt = yt_download_thread(url, fmts[0], os.path.join(outdir, names[0]), speed)
	audt = yt_download_thread(url, fmts[1], os.path.join(outdir, names[1]), speed)
	vidt.start()
	audt.start()
	vidt.join()
	audt.join()
	return 0

def yt_download_thread(url: str, fmt: str, out: str, speed: float) -> threading.Thread:
	return threading.Thread(
		target=yt_download_fmt,
		args=(url, fmt, out, speed),
		daemon=True,
	)

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
	amatch = max(codes_n_abr, key=lambda x: x[1])
	return amatch[0] if amatch else None

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


class YTDownloadThread(threading.Thread):
	def __init__(self, url: str, fmt: int, out: str, ratelimit: int, quiet: bool=True):
		if os.path.exists(out):
			raise FileAlreadyExistsException
		super(YTDownloadThread, self).__init__()
		self.url = url
		self.args = {
			"call_home": False,
			"quiet": quiet,
			'format': fmt,
			'outtmpl': out,
			'nopart': True,
			'ratelimit': ratelimit*1024,
			'continuedl': True
		}
		self.exception = None
		self.done = False
	def run(self):
		downloader = youtube_dl.YoutubeDL(self.args)
		try:
			downloader.download([self.url])
		except Exception as e:
			self.exception = e
		self.done = True

class FileAlreadyExistsException(Exception):
	pass

class MainParser:
	def __init__(self):
		self.parser = argparse.ArgumentParser('Perform certain tasks with youtube-dl api')
		self.parser.add_argument('-v', '--verbose', help='Causes more output to stdout', default=False, action='store_false')
		self.parser.add_argument('task', type=str, help='Task to be completed with URL', choices=['exists', 'download'])
		self.vidparams = self.parser.add_argument_group('Video Params', description='params that describe the desired video.')
		self.vidparams.add_argument('url', type=str, help='Video URL')
		self.vidparams.add_argument('-F', '--fmt', type=str, help='File format', default='webm')
		self.vidparams.add_argument('--res', type=int, help='Video vertical resolution')
		self.vidparams.add_argument('-a', '--abr', type=int, help='Max audio bitrate')

		self.vidparams.add_argument('-o', '--out', type=str, help='Download directory', default=os.path.join(os.getcwd(),'out'))
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
		return download_dash_yt(t.url, t.res, t.fmt, t.abr, t.out, ('1','1aud'), t.rate)
	return 0

if __name__=='__main__':
	exit(main(argv))
