import asyncore, asynchat, socket
import random
import time


def strip_status(nick):
    if nick[0] in '+%@&~':
        nick = nick[1:]
    return nick


def log(s):
    print("[!] {0}".format(s))


class Channel(object):
    """
    Creates a channel instance for tracking user information.
    """
    def __init__(self, name):
        self.name = name
        self.nick_list = []

    def __str__(self):
        return "<{0} '{1} users'>".format(self.name, len(self.nick_list))


class Client(asynchat.async_chat):
    """
    Creates a client connection for your drone.
    """
    def __init__(self, server, port, user, channels):
        asynchat.async_chat.__init__(self)
        self.set_terminator('\r\n')
        self.collect_incoming_data = self._collect_incoming_data
        self.server = server
        self.port = int(port)
        self.nick = self.real = self.user = user
        self.password = None
        self.channels = channels
        self.active_chans = {}
        self.reply_chance = 1#.1
        self.txt = self.get_text()
        try:
            self.server, self.user
        except AttributeError:
            log("ERROR: Not enough arguments") 
            exit(0)
        self.quit = "bye forever"
        self.hooked = {
            'PING':_PING,
            'KICK':_KICK,
            'PRIVMSG':_PRIVMSG,
            '433':_NICKUSED,
            '001':_CONNECT,
            '353':_NAMES,
            'JOIN':_JOIN,
            'PART':_PART,
            'QUIT':_QUIT
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
            self.sendline('PASS {0}'.format(self.password))
        asynchat.async_chat.connect(self, (self.server, self.port))
        print("[!] {0} connecting to {1} on port {2}".format(self.nick, self.server, self.port)) 

    def disconnect(self):
        # if self.reconn:
        #    self.reconn = False
        self.sendline('QUIT :{0}'.format(self.quit))
        print("[!] {} disconnecting from {0}".format(self.nick, self.server))
        self.close()

    def handle_connect(self):
        self.sendline('USER {0} * * :{1}'.format(self.user, self.real))
        self.sendline('NICK {0}'.format(self.nick))
        print("[!] {} connected!".format(self.nick))

    def handle_close(self):
        if self.reconn:
            self.connect()

    def sendline(self, line):
        self.push('{0}\r\n'.format(line))

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

    def get_text(self):
        txt = {}
        for txt_file in ('openings', 'closings', 'insults', 'links'):
            with open('txt/{0}.txt'.format(txt_file), 'r') as f:
                _txt = [line.rstrip('\n\r') for line in f.readlines()]
                txt[txt_file] = _txt
        return txt

    def say(self, chan, line):
        self.sendline('PRIVMSG {0} {1}'.format(chan, line))

    def partchan(self, chan, reason):
        self.sendline('PART {0} {1}'.format(chan, reason))

    def joinchan(self, chan):
        self.sendline('JOIN {0}'.format(chan))


def _PING(self, prefix, params):
    self.sendline('PONG {0}'.format(' '.join(params)))
 

def _CONNECT(self, prefix, params):
    self.connected = True
    for chan in self.channels:
        self.joinchan(chan)
        log("Joining {0}".format(chan))


def _NAMES(self, prefix, params):
    _nick_list = [strip_status(nick) for nick in params[3].split()]
    _nick_list.remove(self.nick)
    chan = params[2]
    self.active_chans[chan].nick_list = _nick_list


def _JOIN(self, prefix, params):
    nick = prefix.split('!')[0]
    chan = params[0]
    if nick == self.nick:
        self.active_chans[chan] = Channel(chan)
        self.sendline('NAMES {0}'.format(chan))
    else:
        if random.random() < self.reply_chance:
            user = random.choice(self.active_chans[chan].nick_list)
            opening = random.choice(self.txt['openings']).format(user)
            insult = random.choice(self.txt['insults']).format(nick)
            bomb = '{} {}'.format(opening, insult)
            self.say(chan, bomb)
            if random.random() < 0.3:
                time.sleep(3)
                self.say(chan, random.choice(self.txt['closings']))

        self.active_chans[chan].nick_list.append(nick)
     

def _KICK(self, prefix, params):
    nick = prefix.split('!')[0]
    chan = params[0]
    if nick == self.nick:
        log("You were kicked from {0}".format(chan))
    else:
        self.active_chans[chan].nick_list.remove(nick)


def _PART(self, prefix, params):
    nick = prefix.split('!')[0]
    chan = params[0]
    if nick == self.nick:
        log("You haved parted {0}".format(chan))
    # print("[!] {0} was kicked from {1}".format(nick, channel))
    else:
        self.active_chans[chan].nick_list.remove(nick)


def _QUIT(self, prefix, params):
    nick = prefix.split('!')[0]
    chan = params[0]
    if nick == self.nick:
        log("You haved quit")
    else:
        self.active_chans[chan].nick_list.remove(nick)

 
def _NICKUSED(self, prefix, params):

    self.sendline('NICK {}_'.format(self.nick))
    log("Nick {0} in use... changing nick to {0}_".format(self.nick))
    

def _PRIVMSG(self, prefix, params):
    nick = prefix.split('!')[0]
    chan = params[0]
    msg = params[1].split()
    trig_char = msg[0][0]
    chan_msg = msg[0:]
    if ('http://' or 'https://') in chan_msg:
        self.say(chan, random.choice(self.txt['links']))


if __name__ == '__main__':

    client = Client('irc.hardchats.com', 6667, 'gaybot', ['#cool',])

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        exit(0)