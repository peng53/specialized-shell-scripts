from streamlink import Streamlink

def streams(url: str, cookie: str, email: str, pword: str):
	sl = Streamlink()
	print('here')
	sl.set_plugin_option('funimationnow', 'language', 'english')
	sl.set_option('http-cookies', cookie)
	sl.set_plugin_option('funimationnow', 'email', email)
	sl.set_plugin_option('funimationnow', 'password', pword)
	sl.set_plugin_option('funimationnow', 'mux-subtitles', True)
	return sl.streams(url)
