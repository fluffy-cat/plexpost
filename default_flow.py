import os

import requests


def path_traversals(path):
    dirs = [d for d in path.split('/') if len(d) > 0]
    paths = []
    for idx in range(0, len(dirs)):
        paths.append('/'.join(dirs[0:idx + 1]))  # List all paths with at least 1 directory
    return paths


def list_unique_directories_depth_first(torrents):
    dirs = set()
    for t in torrents:
        for f in t.files().values():
            dirname = os.path.dirname(f['name'])
            paths = [t.downloadDir + '/' + p for p in path_traversals(dirname)]
            dirs.update(paths)
    depth_first_dirs = sorted(list(dirs), reverse=True)
    return depth_first_dirs


def cleanup_files(torrents):
    for t in torrents:
        for f in t.files().values():
            os.remove(t.downloadDir + '/' + f['name'])


def cleanup_empty_dirs(torrents):
    dirs = list_unique_directories_depth_first(torrents)
    for d in dirs:
        try:
            os.rmdir(d)
        except OSError:
            pass  # Directory is not empty so we do not delete it


def cleanup_torrent_data(torrents):
    cleanup_files(torrents)
    cleanup_empty_dirs(torrents)


class DefaultPostProcessor:
    def __init__(self, transmission,
                 assistant_url='localhost', assistant_token='', htpc_switch='switch',
                 sftpclient=None, sftp_remote_dir='/', download_dir='/downloads'):
        self.htpc_switch = htpc_switch
        self.assistant_token = assistant_token
        self.assistant_url = assistant_url
        self.transmission = transmission
        self.sftpclient = sftpclient
        self.sftpclient.chdir(sftp_remote_dir)
        self.download_dir = download_dir

    def run(self):
        torrents = self.get_completed_torrents()
        torrents = [t for t in torrents if self.is_uncategorised(t)]
        if len(torrents) > 0:
            self.wake_htpc()
        self.transfer_to_htpc(torrents)
        cleanup_torrent_data(torrents)
        self.remove_torrents_from_client(torrents)

    def is_uncategorised(self, torrent):
        return torrent.downloadDir == self.download_dir

    def remove_torrents_from_client(self, torrents):
        for t in torrents:
            self.transmission.remove_torrent(t.id)

    def wake_htpc(self):
        requests.post('http://' + self.assistant_url + ':8123/api/services/switch/turn_on',
                      json={'entity_id': 'switch.' + self.htpc_switch},
                      headers={'Authorization': 'Bearer ' + self.assistant_token})

    def get_completed_torrents(self):
        torrents = [t for t in self.transmission.get_torrents() if t.progress >= 100.0]
        return torrents

    def transfer_to_htpc(self, torrents):
        for t in torrents:
            for f in t.files().values():
                filename = f['name']
                remote_dir = os.path.split(filename)[0]
                if len(remote_dir) > 0:
                    self.sftpclient.makedirs(remote_dir)
                self.sftpclient.put(t.downloadDir + '/' + filename, filename)
