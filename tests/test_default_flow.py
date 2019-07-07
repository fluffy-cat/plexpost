from unittest.mock import Mock

import pytest
from transmissionrpc import Torrent

import default_flow
import htpc_switch
import post_processor
from sftp_factory import SFTPFactory


@pytest.fixture(autouse=True)
def requests(monkeypatch):
    req = Mock()
    monkeypatch.setattr(htpc_switch, 'requests', req)
    return req


@pytest.fixture
def transmission():
    return Mock()


@pytest.fixture
def download_dir():
    return 'tmp'


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission,
                                        Mock(),
                                        SFTPFactory({'url': sftpserver.host,
                                                     'port': sftpserver.port,
                                                     'username': 'user',
                                                     'password': '',
                                                     'remote_dir': remote_base_dir}),
                                        default_flow.DefaultPostProcessor({'download_dir_tag': download_dir}))


@pytest.fixture
def remote_base_dir(sftpserver):
    base = 'root'
    path = '/' + base
    with sftpserver.serve_content({base: {'downloads': {'.keep': ''}}}):
        yield path


@pytest.mark.parametrize('download_dir', ['tmp/downloads'])
def test_should_only_process_uncategorised_torrents_when_they_are_in_the_downloads_folder(automator, transmission,
                                                                                          download_dir):
    torrents = [create_torrent(1, 0, 'tmp/downloads/movies'),
                create_torrent(2, 0, 'tmp/downloads')]
    transmission.get_torrents.return_value = torrents
    automator.download_dir = '/downloads'
    automator.run()
    transmission.remove_torrent.assert_called_once_with(2)


def create_torrent(id, size_left, download_dir):
    name = 'Torrent ' + str(id)
    fields = {'id': id, 'name': name, 'sizeWhenDone': 1, 'leftUntilDone': size_left, 'downloadDir': download_dir}
    return Torrent(None, fields)
