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


class MoviePostProcessor:
    def __init__(self, transmission,
                 assistant_url='localhost', assistant_token='', htpc_switch='switch',
                 sftp_factory=None, download_dir_tag='/downloads'):
        self.htpc_switch = htpc_switch
        self.assistant_token = assistant_token
        self.assistant_url = assistant_url
        self.transmission = transmission
        self.sftp_factory = sftp_factory
        self.download_dir_tag = download_dir_tag

    def run(self):
        print('Looking for movies')
        torrents = self.get_completed_torrents()
        torrents = [t for t in torrents if self.is_movie(t)]
        print('Found ' + str(len(torrents)) + ' movies')
        for t in torrents:
            print('  ' + t.name)
        if len(torrents) > 0:
            print('Waking htpc')
            self.wake_htpc()
        self.transfer_to_htpc(torrents)
        cleanup_torrent_data(torrents)
        self.remove_torrents_from_client(torrents)

    def is_movie(self, torrent):
        return torrent.downloadDir == self.download_dir_tag

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
        if (len(torrents) == 0):
            return
        with self.sftp_factory.await_connection() as sftp:
            sftp.chdir('movies')
            for t in torrents:
                print('Transferring ' + t.name + ' to remote')
                for f in t.files().values():
                    filename = f['name']
                    remote_dir = os.path.split(filename)[0]
                    if len(remote_dir) > 0:
                        sftp.makedirs(remote_dir)
                    sftp.put(t.downloadDir + '/' + filename, filename)
                print('Completed transferring ' + t.name)
