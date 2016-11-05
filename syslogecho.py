from twisted.protocols import basic
from twisted.internet import protocol, reactor
from twisted.web.resource import Resource, NoResource
import re

class Nases(Resource):
    def __init__(self,nasmanager):
        Resource.__init__(self)
        self.nm = nasmanager

    def render_GET(self,request):
        return "<html><body><pre>%s</pre></body></html>" % (','.join(self.nm.nases.keys()),)

class Nase(Resource):
    def __init__(self, nasmanager, nas_ip):
        Resource.__init__(self)
        self.nm = nasmanager
        self.nas_ip = nas_ip

    def render_GET(self, request):
        ret = ''
        for (k,v) in self.nm.nases[self.nas_ip]["users"].items():
            ret += str(v) + ":" + str(k) + "<br>"
        return "<html><body><pre>%s</pre></body></html>" % (ret,)
        # return "<html><body><pre>%s</pre></body></html>" % ('\n'.join(self.nm.nases[self.nas_ip]["users"].keys()),)

class Message(Resource):
    def __init__(self, message):

        Resource.__init__(self)
        self.message = message

    def render_GET(self,request):
        return "<html><body><pre>%s</pre></body></html>" % (self.message,)

class SysloggerEcho(Resource):
    def __init__(self,nasmanager,syslogger):
        Resource.__init__(self)
        self.ipre = re.compile("\d+.\d+.\d+.\d+")
        self.nm = nasmanager
        self.syslogger = syslogger
        self.lines = []

    def getChild(self, name, request):
        if self.ipre.search(name):
            return Nase(self.nm, name)
        elif name.lower() == 'nases':
            return Nases(self.nm)
        elif name == 'packetcount':
            return Message("{0} packets received".format(self.syslogger.packet_count))
        elif name == 'reload':
            self.syslogger.reload_config()
            return Message('reloading...')
        elif name == 'addr':
            return Message(request.getClientIP())
        else:
            return NoResource

    def render_GET(self, request):
        ret = "<html><body><pre>"
        for nas_ip in self.nm.nases:
            ret += str(nas_ip)
            for user_ip in self.nm.nases[nas_ip]["users"]:
                ret += user_ip + ":" + self.nm.nases[nas_ip]["users"][user_ip] + ""
        ret += "</pre></body></html>"
        return ret
    # def lineReceived(self, line):
    #     self.lines.append(line)
    #     if not line:
    #         self.sendResponse()

    # def sendResponse(self):
    #     self.sendLine("HTTP/1.1 200 OK")
    #     self.sendLine("")
    #     # self.transport.write(responseBody)
    #     for nas_ip in self.nm.nases:
    #         self.lines = []
    #         self.lines.append(nas_ip + "\r\n")
    #         for user_ip in self.nm.nases[nas_ip]["users"]:
    #             self.lines.append(user_ip + ":" + self.nm.nases[nas_ip]["users"][user_ip])
    #         self.transport.write("\r\n".join(self.lines))
    #     self.transport.loseConnection()

# class SysloggerEchoFactory(protocol.ServerFactory):
#     def __init__(self, nasmanager):
#         self.nm = nasmanager
#     def buildProtocol(self, addr):
#         return SysloggerEcho(self.nm)


# reactor.listenTCP(5140, SysloggerEchoFactory(None))
# reactor.run()