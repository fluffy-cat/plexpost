import errno
import os
from unittest.mock import Mock

import pytest
from transmissionrpc import Torrent

import movies_flow
import post_processor
from sftp_factory import SFTPFactory


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission,
                                        Mock(),
                                        SFTPFactory({'url': sftpserver.host,
                                                     'port': sftpserver.port,
                                                     'username': 'user',
                                                     'password': '',
                                                     'remote_dir': remote_base_dir}),
                                        movies_flow.MoviePostProcessor({'download_dir_tag': download_dir}))


@pytest.mark.parametrize('download_dir', ['tmp/downloads/movies'])
def test_should_only_process_downloads_when_they_are_in_the_movies_folder(automator, transmission,
                                                                          download_dir):
    torrents = [create_torrent(1, 0, 'tmp/downloads/movies'),
                create_torrent(2, 0, 'tmp/downloads')]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_called_once_with(1)


def create_torrent(id, size_left, download_dir):
    name = 'Torrent ' + str(id)
    fields = {'id': id, 'name': name, 'sizeWhenDone': 1, 'leftUntilDone': size_left, 'downloadDir': download_dir}
    return Torrent(None, fields)


def completed_torrent_with_data_files(prefix, files):
    tor = Mock()
    tor.progress = 100
    tor.id = 1
    tor.downloadDir = prefix
    tor.name = 'Mock 1'
    data_files = {}
    for idx, f in enumerate(files):
        data_files[idx] = create_download_file(prefix, f)
    tor.files.return_value = data_files
    return tor


def create_download_file(prefix, filename):
    return {'selected': True, 'priority': 'normal', 'size': 1, 'name': touch(prefix, filename), 'completed': 1}


def touch(prefix, file):
    path = prefix + '/' + file
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(path, 'a'):
        os.utime(path)
    return file
