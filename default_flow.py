class DefaultPostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'uncategorised download'

    def map_files(self, download):
        mappings = []
        for f in download.files().values():
            filename = f['name']
            rule = {'download_dir': download.downloadDir, 'filename': filename, 'dest': 'downloads/' + filename}
            mappings.append(rule)
        return mappings

    def filter(self, torrent):
        return torrent.downloadDir == self.download_dir_tag
