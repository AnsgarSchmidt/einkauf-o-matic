#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
simple irc bot
"""

import socket
from datetime import timedelta


class Bot(object):
    def __init__(self, server, port, chan, nick, owner):
        self.server = server
        self.port   = port
        self.chan   = chan
        self.nick   = nick
        self.owner  = owner
        self.nspw   = ''        #TODO: Nickserv password from config file
        self.sock   = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server, self.port))
        self.sock.send('USER %s %s %s :einkauf-o-matic IRC bot\n' % (self.nick,
                                                                     self.nick,
                                                                     self.nick))
        self.identify()
        for channel in self.chan:
            self.join(channel)

        #TODO: only return True if connection was succesful
        return True

    def run(self):
        while True:
            resp = self.sock.recv(2048)
            resp = resp.strip('\n\r')
            print 'SERVER>', resp

            if resp.startswith('PING :'):
                self.ping()
            # strings from irc can look like this:
            #:NICK!~NICK@IP PRIVMSG #CHANNEL :MESSAGE
            #:NICK!~NICK@IP PRIVMSG NICK :MESSAGE
            elif resp.startswith(':'):
                nick = resp[1:].split(' :')[0].split(' ')[0]
                chan = resp[1:].split(' :')[0].split(' ')[2]
                msg = ' :'.join(resp[1:].split(' :')[1:])
                self.process(nick, chan, msg)

    def process(self, nick, chan, msg):
        print 'DEBUG>', '%s in %s said: %s' % (nick.split('!')[0], chan, msg)

        # rules for all channels:
        if msg.lower() == 'hello %s' % self.nick:
            self.sendmsg(chan, 'Hello %s' % nick.split('!')[0])
        elif msg.lower() == 'hallo %s' % self.nick:
            self.sendmsg(chan, 'Hallo %s' % nick.split('!')[0])

        # rules for einkauf-o-matic channel:
        if chan == '#einkauf-o-matic':
            elif msg.lower() == '!uptime':
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    uptime_string = str(timedelta(seconds = uptime_seconds))
                self.sendmsg(nick, uptime_string)
            elif msg.lower() == '!status':
                pass

        # rules for other channels:
        else:
            pass

        # rules for bot owners:
        if nick in self.owner:
            pass

    def join(self, chan):
        self.sock.send('JOIN %s\n' % self.chan)

    def sendmsg(self, chan, msg):
        self.sock.send('PRIVMSG %s :%s\n' % (chan, msg))

    def ping(self):
        self.sock.send('PONG :Pong\n')

    def identify(self):
        self.sock.send('NICK %s\n' % self.nick)
        self.sock.send('MSG nickserv IDENTIFY %s\n' % self.nspw)


if __name__ == '__main__':
    server = 'irc.freenode.net'
    port   = 6667
    chan   = ['#c-base', '#einkauf-o-matic']
    nick   = 'einkauf-o-matic-dev'
    owner  = ['XenGi', 'ansi']
    bot    = Bot(server, port, chan, nick, owner)
    if bot.connect():
        bot.run()
