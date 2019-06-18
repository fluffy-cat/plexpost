import requests


class HTPCSwitch:
    def __init__(self, url, token, switch_id):
        self.url = url
        self.token = token
        self.switch_id = switch_id

    def turn_on(self):
        requests.post('http://' + self.url + ':8123/api/services/switch/turn_on',
                      json={'entity_id': 'switch.' + self.switch_id},
                      headers={'Authorization': 'Bearer ' + self.token})
