from sys import argv
from time import sleep
import argparse
import youtube_dl
import os
import threading


def yt_info():
	return youtube_dl.YoutubeDL(
		{
		"call_home": False,
		"quiet": True,
		'skip_download': True
		}
	)

def get_video_fmt(info, vheight: int, vfmt: str):
	vids = filter(lambda d: d['vcodec']!='none' and d['acodec']=='none' and d['ext']==vfmt, info['formats'])
	vmatch = next(filter(lambda v: int(v['height'])==vheight, vids), None)
	return vmatch['format_id'] if vmatch else None

def get_audio_fmt(info, abr: int):
	# Returns audio fmt with abr equal or less than desired abr
	auds = filter(lambda d: d['vcodec']=='none' and d['acodec']!='none', info['formats'])
	matches = filter(lambda d: d['abr'] <= abr, auds)
	codes_n_abr = ((m['format_id'], m['abr']) for m in matches)
	amatch = max(codes_n_abr, key=lambda x: x[1])
	return amatch[0] if amatch else None

class DownloadThread(threading.Thread):
	def __init__(self, url: str, fmt: int, out: str, ratelimit: int):
		if os.path.exists(out):
			raise FileAlreadyExistsException
		super(DownloadThread, self).__init__()
		self.url = url
		self.args = {
			"call_home": False,
			"quiet": True,
			'format': fmt,
			'outtmpl': out,
			'nopart': True,
			'ratelimit': ratelimit*1024
		}
		self.exception = None
		self.done = False
	def run(self):
		downloader = youtube_dl.YoutubeDL(self.args)
		print('{} To file {}'.format(self.args['format'], self.args['outtmpl']))
		try:
			downloader.download([self.url])
		except Exception as e:
			self.exception = e
		self.done = True

'''
def download_thread(url: str, fmt: int, out: str, ratelimit: int):
	return threading.Thread(
		target=download_fmt,
		args=(
			url,
			fmt,
			out,
			ratelimit
		)
	)

def download_fmt(url: str, fmt: int, out: str, ratelimit=None):
	if os.path.exists(out):
		raise FileAlreadyExistsException
	args = {
		"call_home": False,
		"quiet": True,
		'format': fmt,
		'outtmpl': out,
		'nopart': True,
	}
	if ratelimit:
		args['ratelimit'] = ratelimit*1000
	downloader = youtube_dl.YoutubeDL(args)
	print('{} To file {}'.format(fmt, out))
	downloader.download([url])

'''

class FileAlreadyExistsException(Exception):
	pass

class MainParser:
	def __init__(self):
		self.parser = argparse.ArgumentParser('Perform certain tasks with youtube-dl api')
		self.vidparams = self.parser.add_argument_group('Video Params', description='params that describe the desired video.')
		self.parser.add_argument('task', type=str, help='Task to be completed with URL', choices=['exists', 'download'])
		self.vidparams.add_argument('url', type=str, help='Video URL')
		self.vidparams.add_argument('-F', '--fmt', type=str, help='File format', default='webm')
		self.vidparams.add_argument('--res', type=int, help='Video vertical resolution')
		self.vidparams.add_argument('-a', '--abr', type=int, help='Max audio bitrate')

		self.vidparams.add_argument('-o', '--out', type=str, help='Download directory', default=os.path.join(os.getcwd(),'out'))
		self.vidparams.add_argument('-r', '--rate', type=int, help='Download rate in KB/S', default=None)

	def parse(self, args):
		return self.parser.parse_args(args)


if __name__=='__main__':
	t = MainParser().parse(argv[1:])
	yd = yt_info()
	info = yd.extract_info(t.url)

	vidf = get_video_fmt(info, t.res, t.fmt) if t.res else None
	audf = get_audio_fmt(info, t.abr) if t.abr else None
	success = True if ((not t.res or vidf) and (not t.abr or audf)) else False

	if t.task=='exists':
		print(success)
	elif t.task=='download' and success:
		threads = []
		if t.res:
			vidt = DownloadThread(t.url, vidf, t.out, t.rate)
			threads.append(vidt)
			#threads.append(download_thread(t.url, vidf, t.out, t.rate))
		if t.abr:
			audt = DownloadThread(t.url, audf, t.out+'aud', t.rate)
			threads.append(audt)
			#threads.append(download_thread(t.url, audf, t.out+'aud', t.rate))

		for t in threads:
			t.start()

		for t in threads:
			if t.exception:
				raise Exception
			t.join()
