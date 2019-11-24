import youtube_dl
import functools
import os
import urllib
import shutil
import threading
import subprocess
from time import sleep

def get_urls(url: str, vheight: int, vfmt: str, abr: int):
	"""
	Uses youtube-dl's api to get urls matching the video
	resolution and audio bitrate.
	"""
	args = {
		"call_home": False,
		"list_formats": True,
		"quiet": True
	}
	ydl = youtube_dl.YoutubeDL(args)
	dd  = ydl.extract_info(url, download=False)
	vid = filter(lambda d: d['vcodec']!='none' and d["ext"]==vfmt, dd["formats"])
	vmatch = next(filter(lambda v: int(v["height"])==vheight, vid), None)
	if not vmatch:
		print("no vmatch")
		return
	aud = filter(lambda d: d['vcodec']=='none', dd["formats"])
	amatches = filter(lambda a: a["abr"]<=abr, aud)
	abest = functools.reduce(lambda x,y: x if x["abr"]>y["abr"] else y, amatches)
	if abest:
		return (vmatch['url'],abest['url'])
	print("no amatch")

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

def download(url: str, outdir: str, filename: str):
	# Downloads Url to outdir/filename.
	# Will not clobber.
	path = os.path.join(outdir,filename)
	if os.path.exists(path):
		return
	with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
		shutil.copyfileobj(response, out_file)

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
	#downloader.extract_info(url)
	downloader.download([url])

def exist_fmt(args):
	pass

if __name__=='__main__':
	import argparse
	parser = argparse.ArgumentParser('Perform certain tasks with youtube-dl api')
	vidparams = parser.add_argument_group('Video Params', description='params that describe the desired video.')
	parser.add_argument('task', type=str, help='Task to be completed with URL', choices=['exists', 'download'])
	vidparams.add_argument('url', type=str, help='Video URL')
	vidparams.add_argument('-F', '--fmt', type=str, help='File format', default='webm')
	vidparams.add_argument('-r', '--res', type=int, help='Video vertical resolution')
	vidparams.add_argument('-a', '--abr', type=int, help='Max audio bitrate')
	vidparams.add_argument('-o', '--out', type=str, help='Download directory', default=os.path.join(os.getcwd(),'out'))

	from sys import argv

	t = parser.parse_args(argv[1:])
	yd =youtube_dl.YoutubeDL(
		{
		"call_home": False,
		"quiet": True,
		'skip_download': True
		}
	)
	vidf = audf = None
	info = yd.extract_info(t.url)
	if t.res:
		vidf = get_video_fmt(info, t.res, t.fmt)
	if t.abr:
		audf = get_audio_fmt(info, t.abr)
	success = True if ((not t.res or vidf) and (not t.abr or audf)) else False
	if t.task=='exists':
		print(success)
	elif t.task=='download' and success:
		threads = []
		if t.res:
			threads.append(
				threading.Thread(
					target=download_fmt,
					args=(
						t.url,
						vidf,
						t.out,
						40
					)
				)
			)
		if t.abr:
			threads.append(
				threading.Thread(
					target=download_fmt,
					args=(
						t.url,
						audf,
						t.out+'aud',
						40
					)
				)
			)
		for t in threads:
			print("Started!")
			t.start()
		for t in threads:
			print("Ended!")
			t.join()
