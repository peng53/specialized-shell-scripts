import youtube_dl
import functools
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
	vid = filter(lambda d: d["ext"]==vfmt, dd["formats"])
	vmatch = next(filter(lambda v: int(v["height"])==vheight, vid), None)
	if not vmatch:
		print("no vmatch")
		return
	aud = filter(lambda d: d["format_note"]=='DASH audio', dd["formats"])
	amatches = filter(lambda a: a["abr"]<=abr, aud)
	abest = functools.reduce(lambda x,y: x if x["abr"]>y["abr"] else y, amatches)
	if abest:
		return (vmatch['url'],abest['url'])
	print("no amatch")

if __name__=='__main__':
	from sys import argv
	if len(argv)>=5:
		url, vheight, fmt, abr = argv[1:]
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
		print(r)
		if r:
			print(r[0])
			print(r[1])
