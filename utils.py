import syslog
from urlparse import urlparse

def log(to_log=""):
	syslog.syslog("[syslogger] " + to_log)

def parse_url(url):
	ret = dict()
	url_parsed = urlparse(url)
	(SCHEME,NETLOC,PATH,PARAMS,QUERY,FRAGMENT) = (0,1,2,3,4,5)
	scheme = url_parsed[SCHEME]
	netloc = url_parsed[NETLOC]
	params = url_parsed[PARAMS]
	query = url_parsed[QUERY]
	fragment = url_parsed[FRAGMENT]
	path = url_parsed[PATH]
	if path:
		ret['path'] = path
		last_section = path[path.rfind('/'):]
		splitted = last_section.split('.')
		if len(splitted) == 2:
			ret['ext'] = splitted[1]

	if netloc:
		ret['netloc'] = netloc
	if query:
		ret['query'] = query
	if params:
		ret['params'] = params

	return ret

