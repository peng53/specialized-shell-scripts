from streamlink import Streamlink

def streams(url: str, session_id: str):
	sl = Streamlink()
	sl.set_plugin_option('crunchyroll', 'session-id', session_id)
	return sl.streams(url)
