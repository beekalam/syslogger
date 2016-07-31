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
			ext = splitted[1]
			if ext in ['aspx','asp','php','jsp']:
				ret['serverside_file_type'] = ext
			else:
				ret['file_ext'] = ext

	if netloc:
		ret['domain'] = netloc
	if query:
		ret['query'] = query
	if params:
		ret['params'] = params

	return ret

if __name__ == '__main__':
	url="http://www.google.com/a/b/c/d/a.php?i=1&j=1#fragment"
	names = ''
	values = ''
	for (k,v) in  parse_url(url).items():
		names += str(k)
		values += str(v)
	print names
	print values