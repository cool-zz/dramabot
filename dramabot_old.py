# dramabot
# a text generation IRC technology
# by c, 2006

from httplib import HTTPConnection
import Queue
from random import choice, randrange
from re import compile
from socks import socks4a  # if using Tor on 127.0.0.1:9050
import threading
from time import sleep
from urllib import urlencode
from socket import AF_INET, SOCK_STREAM, socket

DENOUEMENTS = ('oops', 'oh hi', 'oh... hi', 'eurgh, shit', 'oh shit', 'oh fuck', 'speak of the devil', 'good timing', 'well this is akward, heh', 'this is awkward...')
INSULTS = (
	'%s is such a fat faggot',
	'%s is such a faggot',
	'%s\'s a fucking tool',
	'%s is a judenspy',
	'good thing %s isn\'t here to see that',
	'im gonna tell %s you said that',
	'tell %s to fuck off already',
	'%s is a complete attention whore',
	'%s is a worthless jew, why do we even keep him around?',
	'who the fuck invited %s here',
	'%s is a useless goblinkike',
	'nobody wants %s around but don\'t mention it',
	'%s is a complete cocksucking aspie',
	'i know exactly what you mean about %s',
	'did you hear the rumours about %s?',
	'%s is a loser too',
	'but I won\'t tell %s you said that',
	'%s is a fucking spastic',
	'%s is a cunt',
)
OPENINGS = (
	'yeah, %s,',
	'yeah %s',
	'totally %s,',
	'srsly %s,',
	'agree 100%%, %s,',
	'agreed %s,',
	'%s backs me up on this,',
	'yah, %s told me,',
	'i agree %s,'
)

def rand_char():
	return chr(randrange(ord('a'), ord('z')))

def gen_rand_username():
	#return 'wqat'
	return ''.join([rand_char() for i in range(8)])

class channel:

	def __init__(self, con, chan):
		"""Initialise, join the channel."""

		self.con = con
		self.chan = chan
		self.nicks = [ ]
		self.con.lsend('JOIN ' + chan)

	def rand_nick(self):
		"""Returns a random nick present in this channel."""
		return choice(self.nicks)

	def strip_nick_status_symbol(self, nick):
		"""If present, removes the status character from a nick."""
		if nick[0] in '@%+':
			nick = nick[1:]
		return nick

	def add_nicks(self, nicks):
		"""Add a list of nicks to this channel's nick list."""
		for nick in nicks:
			nick = self.strip_nick_status_symbol(nick)
			if (nick != self.con.nick) and (nick not in self.nicks):
				self.nicks += [ nick ]

	def del_nick(self, nick):
		"""Delete a nick from this channel's nick list."""
		nick = self.strip_nick_status_symbol(nick)
		try:
			self.nicks.remove(nick)
		except:
			print 'Error: failed to remove \'%s\' from nick list for %s' % (nick, self.chan)

	def drama_bomb(self, target):
		"""Say something in the channel to a target nick to provoke them."""
		global DENOUEMENTS, INSULTS, OPENINGS

		template = 'PRIVMSG %s :' + choice(OPENINGS) + ' ' + choice(INSULTS)
		print "TEMPLATE: " + template
		bomb = template % (self.chan, self.rand_nick(), target)

		print '%s: drama bomb "%s"' % (self.chan, bomb)
		self.con.lsend(bomb)

		if randrange(1, 2) != 1:
			# chance of saying a denouement
			sleep(1)
			self.con.lsend('PRIVMSG %s :%s' % (self.chan, choice(DENOUEMENTS)))

	def display_status(self):
		"""Write a status report for this channel on stdout."""
		print '  %s: new nick list length %u' % (self.chan, len(self.nicks))

class con:

	def __init__(self, server, port, channels, nick, socks4a_proxy = None):

		self.server, self.port, self.nick = server, port, nick

		self.r = { }
		self.r['001'] = compile(':[^ ]+ 001 ')
		self.r['353'] = compile(':[^ ]+ 353 [^ ]+ . ([^ ]+) :(.+)')
		self.r['433'] = compile(':[^ ]+ 433 . [^ ]+ :.+')
		self.r['join'] = compile(':([^!~:]+)![^ ]+ JOIN :([^ ]+)')
		self.r['part'] = compile(':([^!~:]+)![^ ]+ PART ([^ ]+)( :(.+))?')
		self.r['kick'] = compile(':([^!~:]+)![^ ]+ KICK ([^ ]+) ([^ ]+)( :(.+))?')
		self.r['privmsg'] = compile(':([^!~:]+)![^ ]+ PRIVMSG ([^ ]+) :(.+)')
		self.r['http'] = compile(':([^!~:]+)![^ ]+ PRIVMSG ([^ ]+) :.*http://.*')
		self.r['die'] = compile(':([^!~:]+)![^ ]+ PRIVMSG ([^ ]+) :' + nick + ': die')

		self.connect(socks4a_proxy)

		self.channels = { }
		for chan in channels:
			self.channels[chan] = channel(self, chan)

	def lsend(self, s):
		self.sock.send(s + '\r\n')

	def lrecv(self):
		c, s = '', ''
		while c != '\n':
			c = self.sock.recv(1)
			if c == '':  # connection closed
				break
			s += c
		return s.strip('\r\n')

	def connect(self, socks4a_proxy = None):
		"""Make the initial connection to the server and try to register."""

		self.sock = socks4a()

		print 'Connecting to %s:%u' % (self.server, self.port)
		if socks4a_proxy == None:
			self.sock.connect((self.server, self.port))
		else:
			self.sock.proxy_connect(socks4a_proxy, (self.server, self.port))

		username = gen_rand_username()
		print '  username = ' + username
		self.lsend('USER ' + username + ' 0 0 :Unknown')
		self.lsend('NICK ' + self.nick + ' 0')

		# Wait for the 001 status reply.
		while 1:
			line = self.lrecv()
			if self.r['001'].match(line):
				# We got the 001, break out of the loop and proceed.
				break
			elif self.r['433'].match(line):
				# This nick is taken. Change the last 2 chars and retry.
				self.nick = self.nick[:-2] + rand_char() + rand_char()
				self.lsend('NICK ' + self.nick + ' 0')
			elif line == '':
				raise 'ConnectError', (self.server, self.port, 'EOFBefore001')

		print '  got 001'

	def go(self):

		global rand_char

		# Join the channels.
		print '  joining channels'
		for channel in self.channels:
			self.lsend('JOIN ' + channel)
		print '  joined all channels'

		# Sit and watch at the socket for incoming data and act on it.

		while 1:

			line = self.lrecv()

			if line == '':
				raise 'ConnectionClose', (self.server, self.port)

			elif line[:6] == 'PING :':
				print '  PONG :' + line[6:]
				self.lsend('PONG :' + line[6:])
				continue

			m = self.r['join'].match(line)
			if m != None:
				# Somebody joined. If it's not us, start the drama and add
				# their nick to the master list of nicks in this channel.
				print 'Received: JOIN'

				if m.group(1) == self.nick:
					continue

				chan = self.channels[m.group(2)]

				chan.add_nicks([ m.group(1) ])
				chan.display_status()
				chan.drama_bomb(m.group(1))
				
				continue

			m = self.r['part'].match(line)
			if m != None:
				# Somebody parted, remove their nick from the master list of
				# this channel's nicks.
				print 'Received: PART'
				chan = self.channels[m.group(2)]
				chan.del_nick(m.group(1))
				chan.display_status()

			m = self.r['353'].match(line)
			if m != None:
				# 353 lists the nicks of the user in a channel we just
				# joined. Add the list of nicks given to the master list of
				# nicks present in the channel.
				print 'Received: 353'
				chan = self.channels[m.group(1)]
				chan.add_nicks(m.group(2).split())
				chan.display_status()
				continue

			m = self.r['kick'].match(line)
			if m != None:
				# Someone was kicked.
				if m.group(3) == self.nick:
					# It was us! Rejoin.
					print 'Kicked! Attempting to rejoin ' + m.group(2)
					self.lsend('JOIN ' + m.group(2))
			line = self.lrecv()

			if line == '':
				raise 'ConnectionClose', (self.server, self.port)

			elif line[:6] == 'PING :':
				print '  PONG :' + line[6:]
				self.lsend('PONG :' + line[6:])
				continue

			print line

			m = self.r['die'].match(line)
			if m != None:
				print 'Request: die'
				nick = m.group(1).lower().replace('m', '/\\/\\')
				out_queue.put( [m.group(2), 'f u' + nick] )
				print 'response sent'

			m = self.r['http'].match(line)
			if m != None:
				# Someone said a URL.
				reply = [
					'/!\\ FUCKIN\' OLD /!\\',
					'404',
					'broken link',
					'busted link',
					'link fails',
					'LM link dont click!',
					'LastMeasure link detected',
					'OLD',
					'CP link',
					'LM link',
					'CP',
					'LM',
					'OLD i posted that yesterday'
				]
				out_queue.put( [ m.group(2), choice(reply) ] )
				continue

class con_thread(threading.Thread):

	def __init__(self, server, port, channels, nick):
		self.co = con(server, port, channels, nick)
		threading.Thread.__init__(self)

	def run(self):
		self.co.go()
		#self.co.go(('127.0.0.1', 9050))  # connect via Tor

# Create the queue to store events to be announced.
out_queue = Queue.Queue(999)

threads = [
	con_thread('irc.ww88.org', 6667, ['#gnaa'], 'dramabot'),
	#con_thread('irc.chir.pn', 6667, ['#chirp'], 'dramabot')

	# The wacky .onion hostname is because it's Freenode's hidden Tor service
	#con_thread('mejokbp2brhw4omd.onion', 6667, ['#wikipedia'], 'fade')
]

for thread in threads:
	thread.setDaemon(1)
	thread.start()

while 1:
	try:
		event = out_queue.get(True)
	except KeyboardInterrupt:
		break
	for thread in threads:
		thread.co.lsend('PRIVMSG ' + event[0] + ' :' + event[1])