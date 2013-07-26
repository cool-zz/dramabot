import asyncore, asynchat, socket

class Client(asynchat.async_chat):
    """
    Creates a client connection for your drone.
    """

    class Channel(object):
        """
        Creates a channel instance for tracking users and bombing.
        """
        def __init__(self, chan):
            self.chan = chan
            self.users = get_users()

        def get_users(self):
            #return names list

        def bomb(self, target):
            _bomb = '{} {}'.format(choice(OPENINGS).format(get_rand_user(),  
                                        choice(INSULTS).format(target)
                                )
            print("BOMBING {} with {}".format(self.chan, _bomb))

    def __init__(self, server, user):
        asynchat.async_chat.__init__(self)
        self.set_terminator('\r\n')
        self.collect_incoming_data = self._collect_incoming_data
        self.options = options
        try:
            self.server, self.user
        except AttributeError:
            print("[!] Error: Not enough arguments") #add log()
            exit(0)
        self.port = int(self.port)
        self.nick = self.real = self.user
        self.quit = "bye forever"
        self.chans = {}
        self.hooked = {
            'PING':on_ping,
            'KICK':on_kick,
            'PRIVMSG':on_privmsg,
            '433':on_nickused,
            '001':on_connect,
            'JOIN':on_join
        }
        self.connect()

     def connect(self):
        raw_ip = socket.getaddrinfo(self.vhost, 0)[0][4][0]
        if ':' in raw_ip:
            self.create_socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((self.vhost,0))
        if self.password:
            self.sendline('PASS %s' % self.password)
        asynchat.async_chat.connect(self, (self.server, self.port))
        print("[!] {} connecting to {} on port {}".format(self.nick, self.server, self.port)) 

     def disconnect(self):
        # if self.reconn:
        #    self.reconn = False
        self.sendline('QUIT :{}'.format(self.quit))
        print("[!] {} disconnecting from {}".format(self.nick, self.server))
        self.close()

    def handle_connect(self):
        self.sendline('USER {} * * :{}'.format(self.user, self.real))
        self.sendline('NICK {}'.format(self.nick))
        print("[!] {} connected!".format(self.nick))

    def handle_close(self):
        if self.reconn:
            self.connect()

    def sendline(self, line):
        self.push('{}\r\n'.format(line))

    def hook(self, command, function):
        if command not in self.hooked:
            self.hooked[command] = []
        if function not in self.hooked[command]:
            self.hooked[command].append(function)
                
    def recvline(self, prefix, command, params):
        i = self.hooked.get(command)
        if i:
            i(self, prefix, params)
            return 

    def parseline(self, data):
        prefix = ''
        trailing = []
        if not data:
            pass
        if data[0] == ':':
            prefix, data = data[1:].split(' ', 1)
        if data.find(' :') != -1:
            data, trailing = data.split(' :', 1)
            params = data.split()
            params.append(trailing)
        else:
            params = data.split()
        command = params.pop(0)
        return prefix, command, params

    def found_terminator(self):
        data = ''.join(self.incoming)
        self.incoming = []
        prefix, command, params = self.parseline(data)
        self.recvline(prefix, command, params)

    def say(self, chan, line):
        self.sendline('PRIVMSG {} {}'.format(chan, line))

    def partchan(self, chan, reason):
        self.sendline('PART {} {}'.format(chan, reason))

    def joinchan(self, chan):
        self.sendline('JOIN {}'.format(chan))

 
if __name__ == '__main__':
    options = {}
    drone = Client(options)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        exit(0)