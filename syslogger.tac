from twisted.application import internet, service
from syslogger import Syslogger
import sys
import re
from utils import can_connect_todb
from utils import try_logging_into_nases
from utils import get_naslist_from_db
from utils import load_exclusion_rules

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

application = service.Application("Syslogger")
syslogger_service = internet.UDPServer(514, Syslogger(webre, act_login, act_logout,nases,exclusion_rules))
syslogger_service.setServiceParent(application)
