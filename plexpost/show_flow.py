from plexpost import file_mapper


def parse_show_name_from_download_dir(show):
    return show.downloadDir.split('/')[-2]


def parse_season_number_from_download_dir(show):
    return show.downloadDir.split('/')[-1]


class ShowPostProcessor:
    def __init__(self, conf):
        self.download_dir_tag = conf['download_dir_tag']
        self.type = 'show'

    def map_files(self, show):
        show_name = parse_show_name_from_download_dir(show)
        season = parse_season_number_from_download_dir(show)
        dest_dir = 'tv/' + show_name + '/' + season + '/'
        return file_mapper.map_single_video_download_with_subs(show, dest_dir)

    def filter(self, torrent):
        return torrent.downloadDir.startswith(self.download_dir_tag)
