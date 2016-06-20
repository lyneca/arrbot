import requests
import websocket
import api
from datetime import datetime
import re
import random

num_search_results = 4  # number of google results to display

try:
    with open("google.apikey") as keyfile:
        google_key = keyfile.read()
except FileNotFoundError:
    raise FileNotFoundError("Arr, ye need to put yer Google API key in a file named 'google.apikey'.")

try:
    with open("slack.apikey") as keyfile:
        slack_key = keyfile.read()
except FileNotFoundError:
    raise FileNotFoundError("Arr, ye need to put yer Slack API key in a file named 'slack.apikey'.")

slack = api.API(slack_key)

letters = ['.-', '-...', '-.-.', '-..', '.', '..-.', '--.', '....', '..', '.---', '-.-', '.-..', '--', '-.', '---',
           '.--.', '--.-', '.-.', '...', '-', '..-', '...-', '.--', '-..-', '-.--', '--..']
numbers = ['.----', '..---', '...--', '....-', '.....', '-....', '--...', '---..', '----.', '-----']
symbols = {'"': '.-..-.', '$': '...-..-', '\'': '.----.', '(': '-.--.', ')': '-.--.-', '[': '-.--.', ']': '-.--.-',
           '+': '.-.-.', ',': '--..--', '-': '-....-', '.': '.-.-.-', '/': '-..-.', ':': '---...', ';': '-.-.-.',
           '=': '-...-', '?': '..--..', '@': '.--.-.', '_': '..--.-', '¶': '.-.-..', '!': '-.-.--'}
letters = {chr(x + 97): letters[x] for x in range(25)}
numbers = {str(x): numbers[x] for x in range(10)}
text_to_morse = letters
text_to_morse.update(numbers)
text_to_morse.update(symbols)
morse_to_text = {text_to_morse[x]: x for x in text_to_morse}

help = [
    "`google: <query>`: performs a Google search on that query and displays the results inline",
    "`morse: <words>`: translates words into Morse Code",
    "Just typing morse code will result in auto translation - as long as your message only contains morse-y characters,"
]


class Arrbot:
    def __init__(self):
        self.responses = {
            'arrbot: help': '\n'.join(help)
        }
        self.functions = {
            r'': self.morse,
            r'morse:': self.to_morse,
            r'google:': self.google_search,
            r'[Yy]ou\'?re an? ': lambda s: self.send(s['channel'], 'o' * random.randint(5, 15))
        }

    def send(self, channel, message):
        slack.post_as_bot(
            channel,
            message,
            'Arrbot',
            # 'http://i.imgur.com/EuY3ao6.png',
            ':reul:',
        )

    def register_func(self, f, reg):
        self.functions[reg] = f

    def register_resp(self, f, reg):
        self.functions[reg] = f

    def morse(self, message):
        string = message['text']
        channel = message['channel']
        out = []
        morse = False
        for word in string.split():
            if word in morse_to_text:
                morse = True
                out.append(morse_to_text[word])
            else:
                out.append(word)
        print(out)
        for char in string:
            if char not in [' ', '.', '-', '/']:
                morse = False
        if morse:
            self.send(
                channel,
                "Translation: `" + ''.join(out).replace('/', ' ') + '`'
            )

    def to_morse(self, message):
        string = message['text']
        channel = message['channel']
        out = []
        content = ':'.join(string.split(':')[1:]).strip().lower()
        for char in content:
            if char in text_to_morse:
                out.append(text_to_morse[char])
            elif char is ' ':
                out.append('/')
            else:
                out.append(char)
        self.send(
            channel,
            "Morse: `" + ' '.join(out) + '`'
        )

    def google_search(self, message):
        channel = message['channel']
        query = ':'.join(message['text'].split(':')[1:]).strip().lower()
        r = requests.get("https://www.googleapis.com/customsearch/v1",
                         params={'key': google_key, 'cx': "011750264622141039810:mskvujvr5qm", 'q': query})
        items = r.json()['items']
        results = [
            "<" + x['link'] + "|" + x['title'] + "> (" + x["displayLink"] + "):\n>" + '\n>'.join(
                x['snippet'].split('\n'))
            for x in items[:(num_search_results if len(items) > num_search_results else len(items))]]
        self.send(channel, 'Google results for %s:\n%s' % (query, '\n'.join(results)))


arrbot = Arrbot()

initial_metadata = requests.get('https://slack.com/api/rtm.start', params={'token': slack_key}).json()
wss_url = initial_metadata['url']
timestamp = datetime.now().timestamp()

w = websocket.WebSocket()
w.connect(wss_url)

while True:
    n = w.next().replace('true', 'True').replace('false', 'False').replace('null', 'None')
    print(n)
    n = eval(n)
    if all([n['type'] == 'message', n['hidden'] if 'hidden' in n else True, 'bot_id' not in n,
            float(n['ts']) > timestamp if 'ts' in n else False]):
        print(n)
        if 'text' not in n:
            continue
        for function in arrbot.functions:
            if re.match(function, n['text']):
                arrbot.functions[function](n)
                continue
        for response in arrbot.responses:
            if re.match(response, n['text']):
                arrbot.send(n['channel'], arrbot.responses[response])
                continue
