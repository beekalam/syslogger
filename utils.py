import syslog
from urlparse import urlparse

def log(to_log=""):
	syslog.syslog("[syslogger] " + to_log)

def get_url_extension(url):
	url_parsed = urlparse(url)
	PATH = 2
	path = url_parsed[PATH]
	if path:
		last_section = path[path.rfind('/'):]
		splitted = last_section.split('.')
		if len(splitted) == 2:
			return splitted[1]

	return ''

