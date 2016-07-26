from twisted.application import internet, service
from syslogger import Syslogger
import sys
from config import Config

# check configuration settings here
# can connect to DB , check
config = Config()


application = service.Application("Syslogger")
syslogger_service = internet.UDPServer(514, Syslogger())
syslogger_service.setServiceParent(application)