from twisted.internet import protocol,threads
from utils import load_exclusion_rules
from utils import get_naslist_from_db

class BaseSyslogger(protocol.DatagramProtocol):
    
    def __init__(self,webre, act_login, act_logout,nases,exclusion_rules,nas_manager):
        self.packet_count = 0
        self.querys = []
        self.act_login = act_login
        self.act_logout = act_logout
        self.webre = webre
        self.init_rules(exclusion_rules)
        self.nm = nas_manager
        self.nm.add_nases(nases)

    # def check_for_new_nases(self):
    #     nases = get_naslist_from_db()
    #     for nas_ip,username, password in nases:
    #         if not (nas_ip in self.nases):
    #             self.nases[nas_ip] = {}
    #             self.nases[nas_ip]["username"] = username
    #             self.nases[nas_ip]["password"] = password
    #             self.nases[nas_ip]["status"] = self.NOT_CHECKED_YET

    def print_nase(self):
        print(80 * '+')
        for nas_ip in self.nases:
            for ip,user in self.nases[nas_ip]["users"].items():
                print ("nas_ip:{0}, ip: {1}, user:{2}".format(nas_ip, ip ,user) )

    def init_rules(self,exclusion_rules):
        if exclusion_rules:
            self.exclusion_rules = None
            self.exclusion_rules = exclusion_rules
            self.has_rules = False
            for key in self.exclusion_rules:
                if len(self.exclusion_rules[key]) > 0:
                    self.has_rules = True
            print("[LOGGER][init_rules]:{0}".format(exclusion_rules))

    def reload_config(self):

        drules = threads.deferToThread(load_exclusion_rules)
        drules.addCallback(self.init_rules)

        dnases = threads.deferToThread(get_naslist_from_db)
        dnases.addCallback(self.nm.update_nases)
        print("[LOGGER][reload_config]:")

