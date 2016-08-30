from twisted.application import internet, service
from twisted.internet import task, threads
from twisted.web.server import Site
from syslogger import Syslogger
import sys
import re
from utils import can_connect_todb
from utils import try_logging_into_nases
from utils import get_naslist_from_db
from utils import load_exclusion_rules
from nasmanager import NasManager
from syslogecho import SysloggerEcho

# check if we can connect to the datbase and exit if not exit
if not can_connect_todb():
	print("could not connect to db")
	sys.exit()
	print("connection to database: OK")

# fixme: check for at least one nas in the datbase & if there is not one exit
# load exclusion rules
exclusion_rules = load_exclusion_rules()

# read a list of nases and try logging in and log on error.
nases = get_naslist_from_db()
if len(nases) == 0:
	print("could not find any nases")
	sys.exit()

try_logging_into_nases(nases)

act_login = re.compile(r'act===>: ([a-zA-Z0-9\-]+) logged in, (\d+.\d+.\d+.\d+)')
act_logout = re.compile(r'act===>: ([a-zA-Z0-9\-]+) logged out, ')
webre = re.compile(r'web===>: (\d+.\d+.\d+.\d+) (\w+) (.+) action=(\w+) cache=(\w+)')
nas_manager = NasManager()

def sync_nases():

	global nas_manager
	print ("[NAS]sync_nases:{0}".format(nas_manager.nases))
	for nas_ip in nas_manager.nases:
		d = threads.deferToThread(nas_manager.get_nas_users ,nas_ip)
		d.addCallback(nas_manager.sync_nas)

sys_logger = Syslogger(webre, act_login, act_logout,nases,exclusion_rules,nas_manager)
application = service.Application("Syslogger")
syslogger_service = internet.UDPServer(514, sys_logger)
syslogger_service.setServiceParent(application)

root = SysloggerEcho(nas_manager,sys_logger)
factory = Site(root)
syslogger_echo_service = internet.TCPServer(5140, factory)
syslogger_echo_service.setServiceParent(application)

loop = task.LoopingCall(sync_nases)
loop.start(60.0 * 30)

