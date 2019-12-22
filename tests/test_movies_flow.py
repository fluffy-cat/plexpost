from unittest.mock import Mock

import pytest
from transmissionrpc import Torrent

from plexpost import post_processor, movies_flow
from plexpost.sftp_factory import SFTPFactory


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission, Mock(), Mock(), SFTPFactory({'url': sftpserver.host,
                                                                                   'port': sftpserver.port,
                                                                                   'username': 'user',
                                                                                   'password': '',
                                                                                   'remote_dir': remote_base_dir}),
                                        movies_flow.MoviePostProcessor({'download_dir_tag': download_dir}))


@pytest.mark.parametrize('download_dir', ['tmp/movies'])
def test_should_only_process_downloads_when_they_are_in_the_movies_folder(automator, transmission,
                                                                          download_dir):
    torrents = [create_torrent(1, 0, 'tmp/movies'),
                create_torrent(2, 0, 'tmp')]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_called_once_with(1)


def create_torrent(id, size_left, download_dir):
    name = 'Torrent ' + str(id)
    fields = {'id': id, 'name': name, 'sizeWhenDone': 1, 'leftUntilDone': size_left, 'downloadDir': download_dir}
    return Torrent(None, fields)
