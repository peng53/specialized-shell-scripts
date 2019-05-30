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

def download(url: str, outdir: str, filename: str):
	# Downloads Url to outdir/filename.
	# Will not clobber.
	path = os.path.join(outdir,filename)
	if os.path.exists(path):
		return
	with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
		shutil.copyfileobj(response, out_file)

if __name__=='__main__':
	from sys import argv
	if len(argv)>=5:
		url, vheight, fmt, abr = argv[1:]
		outdir = '/mnt/ramdisk/'
		try:
			vheight, abr = int(vheight), int(abr)
		except:
			exit()
		r = get_urls(
			url,
			vheight,
			fmt,
			abr
		)
		if r:
			print("Starting Download")
			vidt = threading.Thread(target=download, args = (r[0], outdir, '1'))
			vidt.start()
			audt = threading.Thread(target=download, args = (r[1], outdir, '1aud'))
			audt.start()
			print("Waiting to play")
			sleep(10)
			vidf = os.path.join(outdir,'1')
			audf = os.path.join(outdir,'1aud')
			subprocess.run(['mpv', vidf, '--audio-file='+audf])
			vidt.join()
			audt.join()
