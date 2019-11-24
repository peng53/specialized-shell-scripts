from sys import argv, exit
from time import sleep
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

class DownloadThread(threading.Thread):
	def __init__(self, url: str, fmt: int, out: str, ratelimit: int, quiet=True):
		if os.path.exists(out):
			raise FileAlreadyExistsException
		super(DownloadThread, self).__init__()
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
	yd = yt_info()
	info = yd.extract_info(t.url)

	vidf = get_video_fmt(info, t.res, t.fmt) if t.res else None
	audf = get_audio_fmt(info, t.abr) if t.abr else None
	success = True if ((not t.res or vidf) and (not t.abr or audf)) else False

	if not success:
		if t.verbose:
			print('Could not find format(s) matching.')
		return 1
	if t.task=='exists':
		return 0
	elif t.task=='download':
		threads = []
		if t.res:
			vidt = DownloadThread(t.url, vidf, t.out, t.rate, t.verbose)
			if t.verbose:
				print('{} To file {}'.format(vidf, t.out))
			threads.append(vidt)
		if t.abr:
			audt = DownloadThread(t.url, audf, t.out+'aud', t.rate, t.verbose)
			if t.verbose:
				print('{} To file {}'.format(audf, t.out))
			threads.append(audt)

		for t in threads:
			t.start()

		for t in threads:
			t.join()
			if t.exception:
				raise Exception
	return 0

if __name__=='__main__':
	exit(main(argv))
