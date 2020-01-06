from unittest.mock import Mock

import pysftp
import pytest

from plexpost import htpc_switch


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
def completed_torrents(transmission):
    return transmission.get_torrents


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
    with pysftp.Connection(sftpserver.host, port=sftpserver.port, username='user', password='',
                           cnopts=cnopts) as sftpclient:
        yield sftpclient
