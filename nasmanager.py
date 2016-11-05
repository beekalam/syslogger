import socket
from twisted.internet import threads
from Apiros import ApiRos, ApiRosException

# fixme: currenlty NasManager drops packets while it's getting the nas users
class NasManager:
    CHECKING, CHECKED, NOT_CHECKED_YET = 0, 1, 2
    def __init__(self):
       self.nases = {}
       self.num_packets = 0

    def update_nases(self,nases):
        for nas_ip,username, password in nases:
            if not nas_ip in self.nases:
                self.nases[nas_ip] = {}
                self.nases[nas_ip]["username"] = username
                self.nases[nas_ip]["password"] = password
                self.nases[nas_ip]["users"] = {}
                self.nases[nas_ip]["status"] = self.NOT_CHECKED_YET
            else:
                self.nases[nas_ip]["username"] = username
                self.nases[nas_ip]["password"] = password
        print("[NAS][update_nases]: {0}".format(self.nases))

    def add_nases(self, nases):
        # if nas_ip in self.nases:
        #     return
        for nas_ip,username, password in nases:
            self.nases[nas_ip] = {}
            self.nases[nas_ip]["username"] = username
            self.nases[nas_ip]["password"] = password
            self.nases[nas_ip]["users"] = {}
            self.nases[nas_ip]["status"] = self.NOT_CHECKED_YET
        print("[NAS]add_nases: {0}".format(self.nases))

    def get_nas_users(self, nas_ip):
        # fixme should return immediately if there's no user and password for nas 
        # and check the return value of the callback
        nas_ip = str(nas_ip)
        print("[NAS] get_nas_users: get users from {0}".format(nas_ip))
        user = self.nases[nas_ip]["username"]
        password  = self.nases[nas_ip]["password"]
        ret = []
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((nas_ip, 8728))
            apiros = ApiRos(s);
            apiros.login(user, password)
            ret = apiros.get_active_radius_users()
        except ApiRosException:
            print("could not connect to api on nas:{0}".format(nas_ip))
        except socket.error:
            print("socket errror on connecting to:{0}".format(nas_ip))
        finally:
            s.close()
        return (nas_ip,ret)

    def on_nas_users_received(self, ip_user):
        nas_ip = ip_user[0]
        nas_users = ip_user[1]
        # self.nases[nas_ip]["users"] = dict()
        for (ip,user) in nas_users:
            self.nases[nas_ip]["users"][ip] = user
        self.nases[nas_ip]["status"] = self.CHECKED
        print ("===[NAS]:{0}".format(self.nases[nas_ip]["users"]))

    def skip_nas(self, nas_ip):
        if nas_ip not in self.nases:
            return True
        elif self.nases[nas_ip]["status"] == self.CHECKING:
            return True
        elif self.nases[nas_ip]["status"] == self.NOT_CHECKED_YET:
            self.nases[nas_ip]["status"] = self.CHECKING
            # self.nases[nas_ip]["users"] = {}
            d = threads.deferToThread(self.get_nas_users ,nas_ip) 
            d.addCallback(self.on_nas_users_received)
            return True
        return False

    def login_user(self, nas_ip, user_ip, username):
        if not (user_ip in self.nases[nas_ip]["users"]):
            print ("===[NAS] logging in: {0}".format(username))
            self.nases[nas_ip]["users"][user_ip] = username

    def logout_user(self, nas_ip, username):
        print ("===[NAS] logging out:{0}".format(username))
        ip = self.get_userip(nas_ip, username)
        if ip:
            self.delete_ip(nas_ip, ip)

    def delete_ip(self, nas_ip, ip):
        print ("===[NAS] deleting {0} from {1}".format(ip, nas_ip))
        try:
            del self.nases[nas_ip]["users"][ip]
        except KeyError:
            print("error deleting user")

    def has_ip(self, nas_ip, user_ip):
        return user_ip in self.nases[nas_ip]["users"]

    def get_username(self, nas_ip, user_ip):
        return self.nases[nas_ip]["users"][user_ip]

    def get_userip(self,nas_ip, username):
        ret = None
        for ip, name in self.nases[nas_ip]["users"].items():
            if name == username:
                ret = ip
                break
        return ret

    def username(self,nas_ip):
        return self.nases[nas_ip]["username"]

    def password(self, nas_ip):
        return self.nases[nas_ip]["password"]

    def get_username(self, nas_ip, user_ip):
        username = self.nases[nas_ip]["users"][user_ip]
        return username

    def sync_nas(self, ip_user_list):
        print "===[NAS][SYNC] >>>>>>>"
        try:
            nas_ip = ip_user_list[0]
            nas_users =ip_user_list[1]

            if nas_ip not in self.nases:
                print("unrecognized nas_ip")
                return
            # self.nases["status"] = self.CHECKING
            delete_list = []
            #clean users that are not online anymore
            for user_ip in  self.nases[nas_ip]["users"]:
                found = False
                for (ip, user) in nas_users:
                    if user_ip == ip:
                        found = True
                        break
                if not found:
                    delete_list.append(user_ip)

            for ip in delete_list:
                self.delete_ip(nas_ip,ip)

            for (ip,user) in nas_users:
                self.nases[nas_ip]["users"][ip] = user

            self.nases[nas_ip]["status"] = self.CHECKED
        except  Exception, e:
            print("[NAS][SYNC]: " + str(e))
        print "===[NAS][SYNC] <<<<<<<<<<<"
        # self.nases[nas_ip]["status"] = self.CHECKED
        # print self.nases[nas_ip]["users"]