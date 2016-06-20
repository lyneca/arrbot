import requests
import websocket
import api
from datetime import datetime
import re

with open("google.apikey") as keyfile:
    google_key = keyfile.read()

with open("slack.apikey") as keyfile:
    slack_key = keyfile.read()

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


def send(channel, message):
    slack.post_as_bot(
        channel,
        message,
        'Arrbot',
        'http://i.imgur.com/EuY3ao6.png',
    )


def morse(message):
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
        send(
            channel,
            "Translation: `" + ''.join(out).replace('/', ' ') + '`'
        )


def to_morse(message):
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
    send(
        channel,
        "Morse: `" + ' '.join(out) + '`'
    )


def google_search(message):
    channel = message['channel']
    query = ':'.join(message['text'].split(':')[1:]).strip().lower()
    r = requests.get("https://www.googleapis.com/customsearch/v1", params={'key': google_key, 'cx': "011750264622141039810:mskvujvr5qm", 'q': query})
    items = r.json()['items']
    results = ["<" + x['link'] + "|" + x['title'] + "> (" + x["displayLink"] + ")" for x in
               items[:(10 if len(items) > 10 else len(items))]]
    send(channel, 'Google results for %s:\n%s' % (query, '\n'.join(results)))


responses = {}
functions = {
    r'': morse,
    r'morse:': to_morse,
    r'google:': google_search
}

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
        for function in functions:
            if re.match(function, n['text']):
                functions[function](n)
                continue
        for response in responses:
            if re.match(response, n['text']):
                send(n['channel'], responses[response])
                continue
