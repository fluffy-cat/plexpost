import errno
import os
from unittest.mock import Mock, call

import pytest
from transmissionrpc import Torrent

from plexpost import post_processor, show_flow
from plexpost.sftp_factory import SFTPFactory


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission,
                                        Mock(),
                                        SFTPFactory({'url': sftpserver.host,
                                                     'port': sftpserver.port,
                                                     'username': 'user',
                                                     'password': '',
                                                     'remote_dir': remote_base_dir}),
                                        show_flow.ShowPostProcessor({'download_dir_tag': download_dir}))


@pytest.mark.parametrize('download_dir', ['tmp/tv'])
def test_should_process_any_download_when_they_are_under_the_shows_folder(automator, transmission,
                                                                          download_dir):
    torrents = [create_torrent(1, 0, 'tmp/tv/The Simpsons/1'),
                create_torrent(2, 0, 'tmp'),
                create_torrent(3, 0, 'tmp/tv/Another Show')]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_has_calls([call(1), call(3)], any_order=True)


@pytest.mark.parametrize('download_dir', ['tmp/Show Name/2'])
def test_should_put_in_show_name_season_subdirectory(completed_torrents,
                                                     automator,
                                                     sftpclient,
                                                     remote_base_dir,
                                                     download_dir):
    video = 'show.mkv'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [video])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/tv/Show Name/2/' + video)


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
