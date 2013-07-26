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
            self.name = chan
            self.user_list = []

        def __str__(self):
            return "[#{} '{} users'>".format(self.name, len(self.user_list))

        # def get_users(self):
        #     self.
        #     if nick[0] in '+%@&~':
        #         nickname = nickname[1:]

            #return names list

        # def bomb(self, target):
        #     _bomb = '{} {}'.format(choice(OPENINGS).format(get_rand_user(),  
        #                                 choice(INSULTS).format(target)
        #                         )
        #     print("BOMBING {} with {}".format(self.chan, _bomb))

    def __init__(self, server, port, user):
        asynchat.async_chat.__init__(self)
        self.set_terminator('\r\n')
        self.collect_incoming_data = self._collect_incoming_data
        self.server = server
        self.port = port
        self.user = user
        self.password = None
        self.chan = '#cool' #will change to list later maybe

        try:
            self.server, self.user
        except AttributeError:
            print("[!] Error: Not enough arguments") #add log()
            exit(0)
        self.port = int(self.port)
        self.nick = self.real = self.user
        self.quit = "bye forever"
        self.chans = []
        self.hooked = {
            'PING':on_ping,
            'KICK':on_kick,
            'PRIVMSG':on_privmsg,
            '433':on_nickused,
            '001':on_connect,
            '353':on_names,
            'JOIN':on_join
        }
        self.connect()

    def connect(self):
        # raw_ip = socket.getaddrinfo(self.vhost, 0)[0][4][0]
        # if ':' in raw_ip:
        #     self.create_socket(socket.AF_INET6, socket.SOCK_STREAM)
        # else:
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.bind((self.vhost,0))
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

def on_ping(self, prefix, params):
    self.sendline('PONG %s' % ' '.join(params))
 
def on_connect(self, prefix, params):
    self.connected = True
    self.joinchan(self.chan)
    print '[!] Joining %s' % self.chan

def on_names(self, prefix, params):
    nicks = params[3].split()

def on_join(self, prefix, params):
    nick = prefix.split('!')[0]
    if nick == self.nick:
        channel = params[0]
        self.chans.append(channel)
        self.sendline('NAMES {}'.format(channel))
     
def on_kick(self, prefix, params):
    nick = prefix.split('!')[0]
    channel = params[0]
    print "[!] %s was kicked from %s" % (nick, channel)
 
def on_nickused(self, prefix, params):
    self.sendline('NICK %s_' % self.nick)
    

def on_privmsg(self, prefix, params):
    nick = prefix.split('!')[0]
    channel = params[0]
    msg = params[1].split()
    trig_char = msg[0][0]
    chan_msg = msg[0:]
    # if (self.master and trig_char == '@'):
    #     cmd = msg[0][1:]
    #     data = msg[1:]
    #     if cmd == 'reload' and nick == self.owner:
    #         reload(cmds)
    #         self.commands = cmds.RelayCmds()
    #         self.say(channel, 
    #                 '13,01[00,01Success13,01] reloaded')
    #     elif cmd in self.commands.triggers.keys():
    #         res = self.commands.triggers.get(cmd)(self, nick, channel, data)
    #     else:
    #         self.say(channel, 
    #                 '13,01[00,01Error13,01] not found')
    # if self.receiver and self.running:
    #     chan_msg = ' '.join(chan_msg)
    #     relay_msg = '%s,01[00,01%s%s,01] <%s> %s' % \
    #                 (self.color, channel, self.color, nick, chan_msg)
    #     self.client.say(self.home_chan, relay_msg)

if __name__ == '__main__':
    #options = {}
    drone = Client('irc.hardchats.com', 6667, 'lolll')
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        exit(0)