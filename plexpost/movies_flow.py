from plexpost import file_mapper


class MoviePostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'movie'

    def map_files(self, movie):
        return file_mapper.map_single_video_download_with_subs(movie, 'movies/')

    def filter(self, torrent):
        return torrent.downloadDir == self.download_dir_tag
