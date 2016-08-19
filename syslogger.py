        #!/usr/bin/env python
import datetime
import time
import re
import sys
from twisted.internet import reactor, threads, protocol
import psycopg2 
from config import Config
from utils import parse_url,make_connection_string
from utils import get_naslist_from_db
from nasmanager import NasManager

def get_max_bulk_insert():
    cfg = Config()
    return int(cfg.max_bulk_insert)

MAX_BULK_INSERT = get_max_bulk_insert()
queue_length = 0
debug = True

def debug(msg):
    global debug
    if debug:
        print(msg)

def add_to_queue(length):
    global queue_length
    queue_length += length

def get_queue_size():
    global queue_length
    return queue_length

def insert_bulk_messages(query_string_list):
    bulk_size = len(query_string_list)
    start = time.time()
    try:
        connectin_string = make_connection_string()
        conn = psycopg2.connect(connectin_string)
        cur = conn.cursor()
        try:
            for item in query_string_list:
                cur.execute(item.strip())
                print("===[DB] inserting {0} ".format(item[0:80]))
            conn.commit()
        except psycopg2.Error as e:
            print("could not insert into database:{0}, {1}".format( e.pgcode or "", e.pgerror or ""))
        finally:
            conn.close()
            cur.close()
    except psycopg2.Error as e:
        print("could not insert into datbase:{0}, {1}".format(e.pgcode or "", e.pgerror or ""))

    time_taken = time.time() - start
    add_to_queue(-(bulk_size))
    debug("inserted {0} bulk messages in {1} seconds=====remaining: {2}".format(bulk_size, time_taken, get_queue_size()))

def make_query_string(nas_ip, username,method, action, url, source,visited_at):
    url = url.replace("'","")
    names = "nas_ip, username, ip,url, visited_at,method, action "
    values = "'{0}', '{1}','{2}', '{3}', '{4}', '{5}', '{6}' ".format(nas_ip, username, source,url,visited_at,method,action)
    dic = parse_url(url)
    for (k,v) in dic.items():
        names += " ,{0}".format(k) 
        values += " ,'{0}'".format(v)

    query_string = "INSERT INTO weblogs({0}) values({1})".format(names, values);
    # debug(query_string)
    return query_string


class BaseSyslogger(protocol.DatagramProtocol):
    
    def __init__(self,webre, act_login, act_logout,nases,exclusion_rules):
        self.packet_count = 0
        self.querys = []
        self.act_login = act_login
        self.act_logout = act_logout
        self.webre = webre
        self.exclusion_rules = exclusion_rules
        self.has_rules = False
        for key in self.exclusion_rules:
            if len(self.exclusion_rules[key]) > 0:
                self.has_rules = True

        self.nm = NasManager()
        self.nm.add_nases(nases)

    def check_for_new_nases(self):
        nases = get_naslist_from_db()
        for nas_ip,username, password in nases:
            if not (nas_ip in self.nases):
                self.nases[nas_ip] = {}
                self.nases[nas_ip]["username"] = username
                self.nases[nas_ip]["password"] = password
                self.nases[nas_ip]["status"] = self.NOT_CHECKED_YET

    def print_nase(self):
        print(80 * '+')
        for nas_ip in self.nases:
            for ip,user in self.nases[nas_ip]["users"].items():
                print ("nas_ip:{0}, ip: {1}, user:{2}".format(nas_ip, ip ,user) )

class Syslogger(BaseSyslogger):

    def __init__(self, webre, act_login, act_logout,nases,exclusion_rules):
        BaseSyslogger.__init__(self,webre, act_login, act_logout,nases,exclusion_rules)

    def skip_url(self, url):
        #if there are no rules get back ASAP
        # if not self.has_rules:
            # return False

        parsed_url = parse_url(url)
        # debug('...:{0}'.format(parsed_url))
        if 'by_ext' in self.exclusion_rules:
            if 'file_ext' in parsed_url:
                if parsed_url['file_ext'] in self.exclusion_rules['by_ext']:
                    print("===[SKIP]: {0}".format(url))
                    return True

        if 'by_domain' in self.exclusion_rules:
            if 'domain' in parsed_url:
                domain = parsed_url['domain'].lower()
                if domain.startswith('www.'):
                    domain = domain[len('www.'):]
                if domain in self.exclusion_rules['by_domain']:
                    print("===[SKIP]: {0}".format(url))
                    return True
        return False

    def datagramReceived(self, data, addr):
        self.packet_count += 1

        nas_ip = addr[0]
        if self.nm.skip_nas(nas_ip):
            return
        # reject packet which is not in our nases
        # if not (nas_ip in self.nases):
            # return
        # check for new nases from databases
        # if self.packet_count > 2000:
            # r = threads.deferToThread(self.check_for_new_nases)
            # self.packet_count = 0
        # if it's the first time receiving from nas_ip load its users
        # if self.nases[nas_ip]["status"] == self.NOT_CHECKED_YET:
        #     self.nases[nas_ip]["status"] = self.CHECKING
        #     self.nases[nas_ip]["users"] = {}
        #     d = threads.deferToThread(self.get_nas_users ,nas_ip, self.nases[nas_ip]["username"], self.nases[nas_ip]["password"])
        #     d.addCallback(self.on_nas_users_received)
        #     fixme: we should skip the packet here how?
        # if getting nas users still in progress skip packets
        # elif self.nases[nas_ip]["status"] == self.CHECKING:
        #     return

        visited_at = str(datetime.datetime.now())
        actlogin_match = self.act_login.search(data)
        actlogout_match = self.act_logout.search(data)
        web_match = self.webre.search(data)
        #debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #debug("received data: '%s'" % data)
        #debug("packet comming from:{0}".format(addr))

        if actlogin_match:
            #debug ("-----------------------accounting login match-----------------")
            mg = actlogin_match.groups()
            username, ip = mg[0], mg[1]
            self.nm.login_user(nas_ip, ip, username)
            # if not (ip in self.nases[nas_ip]["users"]):
                # self.nases[nas_ip]["users"][ip] = username

        elif actlogout_match:
            #debug("-----------------------accounting logout match-------------")
            username = actlogout_match.groups()[0]
            self.nm.logout_user(nas_ip,username)
            # ip = self.get_ip_byname(nas_ip, username)
            # if ip:
            #     try:
            #         del self.nases[nas_ip]["users"][ip]
            #     except KeyError:
            #         print("error deleting user")

        elif web_match:
            #debug("--------------- webmatch ---------------------------------")
            matches  = web_match.groups()
            ip = matches[0]
            method = matches[1]
            url = matches[2]
            action =matches[3]
            cache = matches[4]
            # ok_to_continue = True
            print("===[URL]:{0}".format(url))
            # if self.skip_url(url):
                # return
            # ok_to_continue = (not self.filter_url(url)) and (ip in self.nases[nas_ip]["users"])
            # print(80 * '-')

            # if ip in self.nases[nas_ip]["users"]:
            if self.nm.has_ip(nas_ip, ip):
                # username = self.nases[nas_ip]["users"][ip]
                username = self.nm.get_username(nas_ip, ip)
                query_string = make_query_string(nas_ip, username,method, action, url, ip,visited_at)
                # print("nas_ip:{0}, ip:{1}, username:{2},url:{3}".format(nas_ip, ip, username, url))
                self.querys.append(query_string)
                # print query_string
                if(len(self.querys) > MAX_BULK_INSERT):
                    copy = self.querys[:]
                    threads.deferToThread(insert_bulk_messages, copy)
                    add_to_queue(len(self.querys))
                    self.querys = []

# act_login = re.compile(r'act===>: ([a-zA-Z0-9\-]+) logged in, (\d+.\d+.\d+.\d+)')
# act_logout = re.compile(r'act===>: ([a-zA-Z0-9\-]+) logged out, ')
# webre = re.compile(r'web===>: (\d+.\d+.\d+.\d+) (\w+) (.+) action=(\w+) cache=(\w+)')

# reactor.listenUDP(514, Syslogger(webre, act_login, act_logout))
# reactor.run()
