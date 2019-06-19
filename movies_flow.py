import os


def is_video(filename):
    return parse_extension(filename) in ['avi', 'mkv', 'mp4']


def is_subtitle(filename):
    return parse_extension(filename) in ['sub', 'idx', 'srt', 'smi', 'ssa', 'ass', 'vtt']


def parse_extension(filename):
    return os.path.splitext(filename)[1][1:]


def forward_main_videos(torrents):
    mappings = []
    for tor in torrents:
        videos = [file for file in tor.files().values() if is_video(file['name'])]
        videos_by_size = sorted(videos, key=lambda v: v['size'], reverse=True)
        if len(videos_by_size) > 0:
            main_video = videos_by_size[0]
            main_filename = main_video['name']
            rule = {'download_dir': tor.downloadDir, 'filename': main_filename, 'dest': 'movies/' + main_filename}
            mappings.append(rule)
    return mappings


def forward_subtitles(torrents):
    mappings = []
    for tor in torrents:
        for file in tor.files().values():
            if is_subtitle(file['name']):
                filename = file['name']
                rule = {'download_dir': tor.downloadDir, 'filename': filename, 'dest': 'movies/' + filename}
                mappings.append(rule)
    return mappings


def forward_files(torrents):
    mappings = []
    mappings.extend(forward_main_videos(torrents))
    mappings.extend(forward_subtitles(torrents))
    return mappings


class MoviePostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'movie'

    def run(self, torrents):
        movies = [t for t in torrents if self.is_movie(t)]
        mappings = forward_files(movies)
        return movies, mappings

    def is_movie(self, torrent):
        return torrent.downloadDir == self.download_dir_tag
