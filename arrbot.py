import requests

with open("keys.db") as keyfile:
    api_key = keyfile.read()

api_key = "AIzaSyAFeZTJRg2Bj6TDbwAVdyocPHkMyoi6Kus"


def google_search(query):
    r = requests.get("https://www.googleapis.com/customsearch/v1",
                     params={'key': api_key, 'cx': "011750264622141039810:mskvujvr5qm", 'q': query})
    items = r.json()['items']
    results = ["<" + x['link'] + "|" + x['title'] + "> (" + x["displayLink"] + ")" for x in
               items[:(10 if len(items) > 10 else len(items))]]
    return '\n'.join(results)
