import os


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


class PostProcessor:
    def __init__(self,
                 transmission,
                 htpc_switch,
                 sftp_factory,
                 media_processor):
        self.transmission = transmission
        self.htpc = htpc_switch
        self.sftp_factory = sftp_factory
        self.media_processor = media_processor

    def run(self):
        completed_torrents = self.get_completed_torrents()
        torrents = [t for t in completed_torrents if self.media_processor.filter(t)]
        print('Found ' + str(len(torrents)) + ' ' + self.media_processor.type + '(s)')
        mappings = []
        for t in torrents:
            print('  ' + t.name)
            mappings.extend(self.media_processor.map_files(t))
        if len(torrents) > 0:
            print('Waking htpc')
            self.htpc.turn_on()
        self.transfer_to_htpc(mappings)
        cleanup_torrent_data(torrents)
        self.remove_torrents_from_client(torrents)

    def remove_torrents_from_client(self, torrents):
        for t in torrents:
            self.transmission.remove_torrent(t.id)

    def get_completed_torrents(self):
        torrents = [t for t in self.transmission.get_torrents() if t.progress >= 100.0]
        return torrents

    def transfer_to_htpc(self, mappings):
        if len(mappings) == 0:
            return
        with self.sftp_factory.await_connection() as sftp:
            for rule in mappings:
                file = rule['filename']
                dest_file = rule['dest']
                print('Transferring ' + file + ' to remote')
                remote_dir = os.path.dirname(dest_file)
                if len(remote_dir) > 0:
                    sftp.makedirs(remote_dir)
                sftp.put(rule['download_dir'] + '/' + file, dest_file)
                print('Completed transferring ' + file)
