#!/usr/bin/env python
from datetime import datetime
import time
import re
from twisted.internet import reactor, threads, protocol
import psycopg2
from config import Config
from utils import parse_url

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

def make_connection_string():
    cfg = Config()
    return "dbname='{0}' user='{1}' password='{2}' host='{3}' ".format(cfg.db_name, cfg.db_user, cfg.db_password, cfg.db_host)

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

def insert_bulk_messages(query_string_list):
    bulk_size = len(query_string_list)
    start = time.time()
    try:
        connectin_string = make_connection_string()
        conn = psycopg2.connect(connectin_string)
        cur = conn.cursor()
        try:
            for item in query_string_list:
                cur.execute(item)
            conn.commit()
            cur.close()
        except:
            debug("could not insert into database")
        conn.close()
    except:
        debug("could not insert into datbase")

    time_taken = time.time() - start
    debug("inserted {0} bulk messages in {1} seconds".format(bulk_size, time_taken))
    add_to_queue(-(bulk_size))
    debug("remaining records to insert: {0} seconds".format(get_queue_size()))

def parse_message(data):
    ret= dict()
    ret['parsed'] = True

    if not data:
        ret['parsed'] = False
        return ret

    data_split = data.split()
    if not data_split[1]:
        ret['parsed'] = False
        return

    ret['ip'] = data_split[1]

    if not data_split[2]:
        ret['parsed'] = False
        return ret

    ret['method'] = data_split[2]

    if not data_split[3]:
        ret['parsed'] = False
        return ret

    ret['url'] = data_split[3]

    if not data_split[4] or (not data_split[4].split('=')[1]):
        ret['parsed'] = False
        return ret

    ret['action'] = data_split[4].split('=')[1]
    
    return ret

def make_query_string(username,method, action, url, source,visited_at):
    names = "username, ip,url, visited_at"
    values = "'{0}', '{1}','{2}', '{3}' ".format(username, source,url,visited_at)
    # dic = parse_url(url)
    # for (k,v) in dic.items():
    #     names += " ,{0}".format(k) 
    #     values += " ,'{0}'".format(v)

    query_string = "INSERT INTO weblogs({0}) values({1})".format(names, values);
    return query_string

class Syslogger(protocol.DatagramProtocol):
    def __init__(self, webre, act_login, act_logout):
        self.querys = []
        self.act_login = act_login
        self.act_logout = act_logout
        self.webre = webre
        self.users = dict()

    def get_user_byname(self,username):
        ret = None
        for ip, name in self.users.items():
            if name == username:
                ret = ip
                break
        return ret

    def datagramReceived(self, data, addr):
        visited_at = str(datetime.now())
        actlogin_match = self.act_login.search(data)
        actlogout_match = self.act_logout.search(data)
        web_match = self.webre.search(data)
        debug("+++++++++++++++++++++++++++++++++++++++++")
        debug("received data: '%s'" % data)

        if actlogin_match:
            debug ("-----------------------accounting login match-----------------")
            mg = actlogin_match.groups()
            username, ip = mg[0], mg[1]
            if not (ip in self.users):
                self.users[ip] = username

        elif actlogout_match:
            debug("-----------------------accounting logout match-------------")
            username = actlogout_match.groups()[0]
            ip = self.get_user_byname(username)
            if ip:
                try:
                    del self.users[ip]
                except KeyError:
                    pass

        elif web_match:
            debug("--------------- webmatch ---------------------------------")
            matches  = web_match.groups()
            ip = matches[0]
            method = matches[1]
            url = matches[2]
            action =matches[3]
            cach = matches[4]
            if ip in self.users:
                username = self.users[ip]
                query_string = make_query_string(username,method, action, url, ip,visited_at)
                self.querys.append(query_string)
                if(len(self.querys) > MAX_BULK_INSERT):
                    copy = self.querys[:]
                    threads.deferToThread(insert_bulk_messages, copy)
                    add_to_queue(len(self.querys))
                    self.querys = []

act_login = re.compile(r'act===>: (\w+) logged in, (\d+.\d+.\d+.\d+)')
act_logout = re.compile(r'act===>: (\w+) logged out, ')
webre = re.compile(r'web===>: (\d+.\d+.\d+.\d+) (\w+) (.+) action=(\w+) cache=(\w+)')

reactor.listenUDP(514, Syslogger(webre, act_login, act_logout))
reactor.run()

