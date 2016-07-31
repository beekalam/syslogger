import ConfigParser
import io
import traceback
from utils import log

class Config:
	def __init__(self):
			self._ok_to_continue = True
			try:
				config  = self.parsefile('./syslogger.conf')
				self.configs = dict()
				self._db_host = config.get('postgresql', 'host')
				self._db_port = config.get('postgresql', 'port')
				self._db_user = config.get('postgresql', 'user')
				self._db_pass = config.get('postgresql', 'password')
				self._db_dbname = config.get('postgresql', 'dbname')

				self._udp_port = config.get('socket','port')
				self._udp_host = config.get('socket', 'host')
				self._udp_bufsize = config.get('socket', 'bufsize')

				self._pidfile = config.get('daemon', 'pidfile')

				self._skip_extensions = config.get('daemon', 'skip-extensions')

				self._max_bulk_insert = config.get('daemon', 'max_bulk_insert')
			except ConfigParser.NoSectionError:
				log("no section provided")
				self._ok_to_continue = False
			except ConfigParser.DuplicateSectionError:
				log("duplicate sections")
				self._ok_to_continue = False
			except ConfigParser.NoOptionError:
				log("no option error")
				self._ok_to_continue = False
			except ConfigParser.ParsingError:
				log("parsing error")
				self._ok_to_continue = False

	def ok_to_continue(self):
		return self._ok_to_continue

	def parsefile(self, config_file_path):
		config = ConfigParser.RawConfigParser()
		config.read(config_file_path)
		return config

	@property
	def db_host(self):
		return self._db_host

	@property
	def db_port(self):
		return self._db_port

	@property
	def db_user(self):
		return self._db_user

	@property
	def db_password(self):
		return self._db_pass

	@property
	def db_name(self):
		return self._db_dbname

	@property
	def udp_host(self):
		return self._udp_host

	@property
	def udp_port(self):
		return self._udp_port

	@property
	def udp_bufsize(self):
		return self._udp_bufsize

	@property
	def pidfile(self):
		return self._pidfile

	@property
	def skip_extensions(self):
		ret = []
		if not self._skip_extensions:
			return ret

		splitted = self._skip_extensions.split(';')
		has_any = len(splitted) > 1
		if has_any:
			for item in splitted:
				ret.append(item)

		return ret

	@property
	def max_bulk_insert(self):
		return self._max_bulk_insert
	
	'''
	def __str__(self):
		attrs = {'db_host' : self.db_host, 'db_port' : self.db_port, 'db_user' : self.db_user, 'db_pass' : self.db_pass \
					,'db_name' : self.db_name, 'udp_host' : self.udp_host, 'udp_port' : self.udp_port, 'udp_bufsize' : self.udp_bufsize}
		st=""
		for (k,v) in attrs.items():
			st += k + " : "
			st += v
			st += "\n"
		return st
	'''
def test():
	cfg = Config()
	# print cfg
	
if __name__ == '__main__':
	test()
