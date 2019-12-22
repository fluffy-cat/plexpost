from unittest.mock import Mock

import pytest
from transmissionrpc import Torrent

from plexpost import post_processor, default_flow
from plexpost.sftp_factory import SFTPFactory


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission, Mock(), Mock(), SFTPFactory({'url': sftpserver.host,
                                                                                   'port': sftpserver.port,
                                                                                   'username': 'user',
                                                                                   'password': '',
                                                                                   'remote_dir': remote_base_dir}),
                                        default_flow.DefaultPostProcessor({'download_dir_tag': download_dir}))


@pytest.mark.parametrize('download_dir', ['tmp/downloads'])
def test_should_only_process_uncategorised_torrents_that_are_in_the_downloads_folder(automator, transmission,
                                                                                     download_dir):
    torrents = [create_torrent(1, 0, 'tmp/downloads/movies'),
                create_torrent(2, 0, 'tmp/downloads')]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_called_once_with(2)


def create_torrent(id, size_left, download_dir):
    name = 'Torrent ' + str(id)
    fields = {'id': id, 'name': name, 'sizeWhenDone': 1, 'leftUntilDone': size_left, 'downloadDir': download_dir}
    return Torrent(None, fields)
