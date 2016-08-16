import syslog
import socket
import psycopg2
from urlparse import urlparse
from config import Config
from Apiros import ApiRos, ApiRosException

def make_connection_string():
	cfg = Config()
	return "dbname='{0}' user='{1}' password='{2}' host='{3}' ".format(cfg.db_name, cfg.db_user, cfg.db_password, cfg.db_host)

def log(to_log=""):
	syslog.syslog("[syslogger] " + to_log)

def get_url_extension(url):
	ret = None
	url_parsed  = urlparse(url)
	PATH = 2
	path = url_parsed[PATH]
	if path:
		last_section = path[path.rfind('/'):]
		splitted = last_section.split('.')
		if len(splitted) == 2:
			ret = splitted[1]

	return ret

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
		if len(splitted)>=2:
			ext = splitted[-1].strip().lower()
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

def can_connect_todb():
	ret = True
	try:
		connection_string = make_connection_string()
		conn = psycopg2.connect(connection_string)
	except psycopg2.Error:
		ret = False
	finally:
		conn.close()
	return ret

def can_connect_to_nas(nas_ip, user, password):
	ret = True
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect((nas_ip, 8728))
		apiros = ApiRos(s);
		apiros.login(user, password)
	except ApiRosException:
		print("could not connect to api on nas:{0}".format(nas_ip))
	except socket.error:
		print("socket errror on connecting to:{0}".format(nas_ip))
	finally:
		s.close()
	return ret

def get_naslist_from_db():
	NAS_ID, NASIP, USERNAME, PASSWORD, DESCRIPTION = 0, 1, 2, 3, 5
	ret = []
	try:
		connection_string = make_connection_string()
		conn = psycopg2.connect(connection_string)
		cur = conn.cursor()
		try:
			cur.execute("SELECT * FROM nases")
			for nas in cur:
				nasip, username, password = nas[NASIP], nas[USERNAME], nas[PASSWORD]
				ret.append((nasip, username, password))
		except psycopg2.Error as e:
			print("could not get nas from db: {0},{1}".format(e.pgcode or "" , e.pgerror or ""))
		finally:
			cur.close()
			conn.close()
	except psycopg2.Error as e:
		print('error connecting to database: {0}, {1}'.format(e.pgcode or "", e.pgerror or ""))

	return ret

def try_logging_into_nases(nases):
	res = True
	for nasip, username,password in nases:
		res = res and can_connect_to_nas(nasip, username, password)

	if res:
		print('could connect to all nases: OK')

def insert_message_todb(query_string):
	debug('query_string: ', query_string)
	try:
		connection_string = make_connection_string()
		conn = psycopg2.connect(connection_string)
		cur = conn.cursor()
		try:
			cur.execute(query_string)
			conn.commit()
			cur.close()
		except:
			debug("could not insert to database")
		conn.close()
	except:
		debug("could not connect to database")

def load_exclusion_rules():
	ret = {}
	ret['by_ext'] = []
	ret['by_domain'] = []
	EXCLUSION_NAME, EXCLUSION_VALUE = 1, 2
	try:
		connection_string = make_connection_string()
		conn = psycopg2.connect(connection_string)
		cur = conn.cursor()
		try:
			cur.execute("SELECT * FROM exclusion_rules")
			for exclusion_rule in cur:
				exclusion_name, exclusion_value = exclusion_rule[EXCLUSION_NAME], exclusion_rule[EXCLUSION_VALUE]
				if exclusion_name == 'by_ext':
					#fixme: should we check for empty values if any?
					ret['by_ext'].append(str(exclusion_value))
				elif exclusion_name == 'by_domain':
					#fixme: should we check for empty values if any?
					domain = str(exclusion_value).lower()
					if domain.startswith('www.'):
						domain = domain[len('www.'):]
					ret['by_domain'].append(domain)
		except psycopg2.Error as e:
			print("could not load exclusion rules: {0},{1}".format(e.pgcode or "" , e.pgerror or ""))
		finally:
			cur.close()
			conn.close()
	except psycopg2.Error as e:
		print('error connecting to database: {0}, {1}'.format(e.pgcode or "", e.pgerror or ""))

	#remove empty rules
	if len(ret['by_ext']) == 0:
		del ret['by_ext']
	if len(ret['by_domain']) == 0:
		del ret['by_domain']
	return ret

def test_load_exclusion_rules():
	print load_exclusion_rules()

if __name__ == '__main__':
	test_load_exclusion_rules()