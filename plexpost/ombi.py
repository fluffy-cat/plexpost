import requests


class Ombi:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def scan_plex(self):
        requests.post('http://' + self.url + ':3579/api/v1/Job/plexcontentcacher',
                      headers={'ApiKey': self.token})
