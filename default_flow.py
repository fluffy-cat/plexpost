import os

import requests


class DefaultPostProcessor:
    def __init__(self, transmission,
                 assistant_url='localhost', assistant_token='', htpc_switch='switch'):
        self.htpc_switch = htpc_switch
        self.assistant_token = assistant_token
        self.assistant_url = assistant_url
        self.transmission = transmission

    def run(self):
        torrents = self.get_completed_torrents()
        self.wake_htpc()
        self.cleanup_torrent_data(torrents)
        self.remove_torrents_from_client(torrents)

    def remove_torrents_from_client(self, torrents):
        for t in torrents:
            self.transmission.remove_torrent(t.id)

    def cleanup_torrent_data(self, torrents):
        self.cleanup_files(torrents)
        self.cleanup_empty_dirs(torrents)

    def cleanup_empty_dirs(self, torrents):
        dirs = self.list_unique_directories_depth_first(torrents)
        for d in dirs:
            try:
                os.rmdir(d)
            except OSError:
                pass  # Directory is not empty so we do not delete it

    def cleanup_files(self, torrents):
        for t in torrents:
            for f in t.files().values():
                os.remove(t.downloadDir + '/' + f['name'])

    def wake_htpc(self):
        requests.post('http://' + self.assistant_url + ':8123/api/services/switch/turn_on',
                      json={'entity_id': 'switch.' + self.htpc_switch},
                      headers={'Authorization': 'Bearer ' + self.assistant_token})

    def get_completed_torrents(self):
        torrents = [t for t in self.transmission.get_torrents() if t.progress >= 100.0]
        return torrents

    def list_unique_directories_depth_first(self, torrents):
        dirs = set()
        for t in torrents:
            for f in t.files().values():
                dirname = os.path.dirname(t.downloadDir + '/' + f['name'])
                if dirname != t.downloadDir:
                    dirs.add(dirname)
        depth_first_dirs = sorted(list(dirs), reverse=True)
        return depth_first_dirs
