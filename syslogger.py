#!/usr/bin/env python
from datetime import datetime
import time
from twisted.internet import reactor, threads, protocol
import psycopg2
from config import Config

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

def make_query_string(method, action, url, source):
    visited_at = str(datetime.now())
    query_string = "INSERT INTO logs(method,action,url, source, visited_at) VALUES ('{0}', '{1}', '{2}','{3}', '{4}') ".format(method, action, url, ip, visited_at)
    return query_string

class Syslogger(protocol.DatagramProtocol):
    def __init__(self):
        self.querys = []

    def datagramReceived(self, data, addr):
        ret = parse_message(data)
        if ret['parsed']:
            query_string = make_query_string(ret['method'], ret['action'], ret['url'], ret['ip'])
            self.querys.append(query_string)
            # insert_message_todb(query_string)
            if(len(self.querys) > MAX_BULK_INSERT):
                copy = self.querys[:]
                threads.deferToThread(insert_bulk_messages, copy)
                add_to_queue(len(self.querys))
                self.querys = []
        #self.transport.write(data, send_to)
reactor.listenUDP(514, Syslogger())
reactor.run()

