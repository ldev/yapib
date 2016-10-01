#!/usr/bin/env python3

import re
import socket
import requests
import random
import json
from lxml import html
from sys import exit
from time import sleep

#
# Load configs
#
try:
    with open('config.json') as config_file:    
        config = json.load(config_file)
except FileNotFoundError:
    exit('No config.json file found')
except:
    exit('Error parsing config.json file')

#
# Helper functions
#
def send_pong(msg):
    print('PONG %s\r\n' % msg)
    con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))

def send_message(msg):
    con.send(bytes('PRIVMSG %s :%s\r\n' % (config['channel'], msg), 'UTF-8'))

def send_nick(nick):
    con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))

def send_user(nick):
    con.send(bytes('USER %s 0 * :%s\r\n' % (nick, nick), 'UTF-8'))
    
def join_channel():
    con.send(bytes('JOIN %s\r\n' % config['channel'], 'UTF-8'))

def part_channel(msg):
    con.send(bytes('PART %s :%s\r\n' % (config['channel'], msg), 'UTF-8'))

def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result

def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result

def parse_message(msg):
    if len(msg) >= 1:
        msg = msg.split(' ')
        triggers = {
            '!test': command_test,
            '!lmh1': command_lmh1,
            '!quote': command_quote
        }
        if msg[0] in triggers:
            triggers[msg[0]]()


# Should return something like:
#  - ping
#  - query
#  - in_channel_message
#  - unknown
def determine_type(msg):
    return True



#
# Custom functions - triggered by !<word>
#
def command_lmh1():
    page = html.parse('http://www.diskusjon.no/index.php?showuser=175531&tab=posts')
    send_message('LMH1 sitt siste lol:')
    for x in page.findall(".//div[@class='post_wrap']"):
        url = x.findall('.//h3/a')[0].get('href')
        url_params = url.split('?')[1].split('&')
        clean_params = []
        for param in url_params:
            if param.split('=')[0] is not 's':
                clean_params.append(param)
        url = 'http://diskusjon.no/?' + '&'.join(clean_params)
        title = x.xpath('.//h3/a/text()')[0]
        time = x.xpath(".//p[@class='posted_info']/text()")[0].strip()
        send_message(' * %s: %s - %s' % (time, title[7:], url))

def command_test():
    send_message('Crodot - helt greit, ingenting spessielt')

def command_quote():
    try:
        resp = requests.get('http://api.ldev.no/?application=roadtriplol&key=quotes&starting_point=1200000000&timeframe=1000000000')
        j = resp.json()
        if 'status' in j:
            q = random.choice(list(j['data']['quotes'].values()))
            if '|' in q:
                send_message('%s: %s' % (q.split('|')[1], q.split('|')[0]))
            else:
                send_message(q)
        else:
            send_message('Såri, virker ikke')
    except:
        send_message('lol, noe kræsja')

#
# Exception class
#
class IRC_link_close(Exception):
    pass


#
# Connect to IRC server
#
con = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
con.connect((config['server'], config['port']))
# sleep(1)
send_nick(config['nick'])
# sleep(1)
send_user(config['nick'])
# sleep(1)
join_channel()
# sleep(1)

#
# Main loop
#
data = ''
while True:
    try:
        data = data+con.recv(1024).decode('UTF-8')
        data_split = re.split(r"[~\r\n]+", data)
        data = data_split.pop()

        for line in data_split:
            print(line)
            if line.startswith('ERROR :Closing Link:'):
                raise IRC_link_close('Connection to %s timed out' % config['server'])
            line = str.rstrip(line)
            line = str.split(line)
            
            if len(line) > 1:
                if line[0] == 'PING':
                    send_pong(line[1])

                if line[1] == 'PRIVMSG':
                    sender = get_sender(line[0])
                    message = get_message(line)
                    parse_message(message)
                    print(sender + ": " + message)

    except socket.error:
        exit("Socket died")

    except socket.timeout:
        exit("Socket timeout")
        
    except IRC_link_close:
        exit("Server closed the link")
        
    except UnicodeEncodeError:
        print('Unicode exception occured')
        pass
    except KeyboardInterrupt:
        part_channel('kthnxbye')
        exit()
    except:
        print('Unidentified exception occured')
        pass
