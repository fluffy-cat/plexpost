class MoviePostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'movie'

    def run(self, torrents):
        movies = [t for t in torrents if self.is_movie(t)]
        mappings = self.forward_all_files(movies)
        return movies, mappings

    def forward_all_files(self, torrents):
        mappings = []
        for t in torrents:
            for f in t.files().values():
                filename = f['name']
                rule = {'download_dir': t.downloadDir, 'filename': filename, 'dest': 'movies/' + filename}
                mappings.append(rule)
        return mappings

    def is_movie(self, torrent):
        return torrent.downloadDir == self.download_dir_tag
