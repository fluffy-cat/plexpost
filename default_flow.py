class DefaultPostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'uncategorised download'

    def run(self, torrents):
        downloads = [t for t in torrents if self.is_uncategorised(t)]
        mappings = self.forward_all_files(downloads)
        return downloads, mappings

    def is_uncategorised(self, torrent):
        return torrent.downloadDir == self.download_dir_tag

    def forward_all_files(self, torrents):
        mappings = []
        for t in torrents:
            for f in t.files().values():
                filename = f['name']
                rule = {'download_dir': t.downloadDir, 'filename': filename, 'dest': 'downloads/' + filename}
                mappings.append(rule)
        return mappings
