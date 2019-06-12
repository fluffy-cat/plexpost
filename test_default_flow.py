import errno
import os
from unittest.mock import Mock, call

import pysftp
import pytest
from transmissionrpc import Torrent

import default_flow


@pytest.fixture(autouse=True)
def requests(monkeypatch):
    req = Mock()
    monkeypatch.setattr(default_flow, 'requests', req)
    return req


@pytest.fixture
def transmission():
    return Mock()


@pytest.fixture
def completed_torrents(transmission):
    return transmission.get_torrents


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(sftpserver.host, port=sftpserver.port, username='user', cnopts=cnopts) as sftp:
        yield default_flow.DefaultPostProcessor(transmission, sftpclient=sftp, sftp_remote_dir=remote_base_dir)


@pytest.fixture
def remote_base_dir(sftpserver):
    base = 'root'
    path = '/' + base
    with sftpserver.serve_content({base: {'.keep': ''}}):
        yield path


@pytest.fixture
def sftpclient(sftpserver):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(sftpserver.host, port=sftpserver.port, username='user', cnopts=cnopts) as sftpclient:
        yield sftpclient


def test_should_remove_torrent_when_they_are_completed(automator, transmission):
    torrents = [Torrent(None, {'id': 1, 'sizeWhenDone': 1, 'leftUntilDone': 0}),
                Torrent(None, {'id': 2, 'sizeWhenDone': 1, 'leftUntilDone': 1}),
                Torrent(None, {'id': 3, 'sizeWhenDone': 2, 'leftUntilDone': 0})]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_has_calls([call(1), call(3)], any_order=True)


def test_should_wake_htpc_when_torrent_is_complete(completed_torrents, automator, requests):
    torrents = [Torrent(None, {'id': 1, 'sizeWhenDone': 1, 'leftUntilDone': 0})]
    completed_torrents.return_value = torrents
    automator.assistant_url = '127.0.0.1'
    automator.assistant_token = '123123'
    automator.htpc_switch = 'htpc'
    automator.run()
    requests.post.assert_called_with('http://127.0.0.1:8123/api/services/switch/turn_on',
                                     json={'entity_id': 'switch.htpc'},
                                     headers={'Authorization': 'Bearer 123123'})


def test_should_not_wake_htpc_when_no_torrents_complete(completed_torrents, automator, requests):
    completed_torrents.return_value = []
    automator.run()
    requests.post.assert_not_called()


def test_should_cleanup_top_level_files_when_download_is_complete(completed_torrents, automator):
    prefix = 'tmp/cleanup_top_level_files_when_download_is_complete'
    top_level_file = 'top_level.txt'
    completed_torrents.return_value = [completed_torrent_with_data_files(prefix, [top_level_file])]
    automator.run()
    assert os.path.isdir(prefix)
    assert not os.path.isfile(prefix + '/' + top_level_file)


def test_should_cleanup_directory_when_download_is_complete(completed_torrents, automator):
    prefix = 'tmp/cleanup_directory_when_download_is_complete'
    file1 = 'dir1/dir2/file'
    file2 = 'dir1/dir2/dir3/file'
    completed_torrents.return_value = [completed_torrent_with_data_files(prefix, [file1, file2])]
    automator.run()
    assert os.path.isdir(prefix)
    assert not os.path.lexists(prefix + '/' + file1)
    assert not os.path.lexists(prefix + '/' + file2)
    assert not os.path.lexists(prefix + '/dir1/dir2')
    assert not os.path.lexists(prefix + '/dir1')


def test_should_only_cleanup_empty_directories(completed_torrents, automator):
    prefix = 'tmp/only_cleanup_empty_directories'
    torrent_file = 'dir1/dir2/torrent_file'
    external_file = 'dir1/external_file'
    touch(prefix, external_file)
    completed_torrents.return_value = [completed_torrent_with_data_files(prefix, [torrent_file])]
    automator.run()
    assert os.path.isfile(prefix + '/' + external_file)
    assert not os.path.isdir(prefix + '/dir1/dir2')


def test_should_copy_top_level_files_to_htpc(completed_torrents, automator, sftpclient, remote_base_dir):
    prefix = 'tmp/copy_top_level_files_to_htpc'
    single_file = 'single_file'
    completed_torrents.return_value = [completed_torrent_with_data_files(prefix, [single_file])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/' + single_file)


def test_should_copy_files_in_directories_to_htpc(completed_torrents, automator, sftpclient, remote_base_dir):
    prefix = 'tmp/copy_files_in_directories_to_htpc'
    nested_file = 'dir1/dir2/nested_file'
    completed_torrents.return_value = [completed_torrent_with_data_files(prefix, [nested_file])]
    automator.run()
    assert sftpclient.isdir(remote_base_dir + '/dir1/dir2')
    assert sftpclient.isfile(remote_base_dir + '/' + nested_file)


def completed_torrent_with_data_files(prefix, files=[]):
    tor = Mock()
    tor.progress = 100
    tor.id = 1
    tor.downloadDir = prefix
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
