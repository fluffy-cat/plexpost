import errno
import os
from unittest.mock import Mock, call

import pysftp
import pytest
from transmissionrpc import Torrent

import htpc_switch
import movies_flow
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
    return '/root'


@pytest.fixture
def completed_torrents(transmission):
    return transmission.get_torrents


@pytest.fixture
def automator(transmission, sftpserver, remote_base_dir, download_dir):
    return post_processor.PostProcessor(transmission,
                                        Mock(),
                                        SFTPFactory({'url': sftpserver.host,
                                                     'port': sftpserver.port,
                                                     'username': 'user',
                                                     'key_path': '',
                                                     'remote_dir': remote_base_dir}),
                                        movies_flow.MoviePostProcessor({'download_dir_tag': download_dir}))


@pytest.fixture
def remote_base_dir(sftpserver):
    base = 'root'
    path = '/' + base
    with sftpserver.serve_content({base: {'movies': {'.keep': ''}}}):
        yield path


@pytest.fixture
def sftpclient(sftpserver):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(sftpserver.host, port=sftpserver.port, username='user', cnopts=cnopts) as sftpclient:
        yield sftpclient


def test_should_only_remove_movies_when_they_are_completed(automator, transmission, download_dir):
    torrents = [create_torrent(1, 0, download_dir),
                create_torrent(2, 1, download_dir),
                create_torrent(3, 0, download_dir)]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_has_calls([call(1), call(3)], any_order=True)


@pytest.mark.parametrize('download_dir', ['/downloads/movies'])
def test_should_only_process_downloads_when_they_are_in_the_movies_folder(automator, transmission,
                                                                          download_dir):
    torrents = [create_torrent(1, 0, '/downloads/movies'),
                create_torrent(2, 0, '/downloads')]
    transmission.get_torrents.return_value = torrents
    automator.run()
    transmission.remove_torrent.assert_called_once_with(1)


def test_should_wake_htpc_when_movie_is_complete(completed_torrents, automator, requests, download_dir):
    torrents = [create_torrent(1, 0, download_dir)]
    completed_torrents.return_value = torrents
    automator.htpc = htpc_switch.HTPCSwitch('127.0.0.1', '123123', 'htpc')
    automator.run()
    requests.post.assert_called_with('http://127.0.0.1:8123/api/services/switch/turn_on',
                                     json={'entity_id': 'switch.htpc'},
                                     headers={'Authorization': 'Bearer 123123'})


def test_should_not_wake_htpc_when_no_movies_complete(completed_torrents, automator, requests):
    completed_torrents.return_value = []
    automator.run()
    requests.post.assert_not_called()


@pytest.mark.parametrize('download_dir', ['tmp/cleanup_top_level_files_when_download_is_complete'])
def test_should_cleanup_top_level_files_when_movie_is_complete(completed_torrents, automator, download_dir):
    top_level_file = 'top_level.avi'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [top_level_file])]
    automator.run()
    assert os.path.isdir(download_dir)
    assert not os.path.isfile(download_dir + '/' + top_level_file)


@pytest.mark.parametrize('download_dir', ['tmp/cleanup_directory_when_download_is_complete'])
def test_should_cleanup_directory_when_movie_is_complete(completed_torrents, automator, download_dir):
    file1 = 'dir1/dir2/file.avi'
    file2 = 'dir1/dir2/dir3/file.avi'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [file1, file2])]
    automator.run()
    assert os.path.isdir(download_dir)
    assert not os.path.lexists(download_dir + '/' + file1)
    assert not os.path.lexists(download_dir + '/' + file2)
    assert not os.path.lexists(download_dir + '/dir1/dir2')
    assert not os.path.lexists(download_dir + '/dir1')


@pytest.mark.parametrize('download_dir', ['tmp/only_cleanup_empty_directories'])
def test_should_only_cleanup_empty_directories(completed_torrents, automator, download_dir):
    torrent_file = 'dir1/dir2/torrent_file.avi'
    external_file = 'dir1/external_file.avi'
    touch(download_dir, external_file)
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [torrent_file])]
    automator.run()
    assert os.path.isfile(download_dir + '/' + external_file)
    assert not os.path.isdir(download_dir + '/dir1/dir2')


@pytest.mark.parametrize('download_dir', ['tmp/copy_top_level_files_to_htpc'])
def test_should_copy_top_level_files_to_htpc(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    single_file = 'single_file.avi'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [single_file])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + single_file)


@pytest.mark.parametrize('download_dir', ['tmp/copy_files_in_directories_to_htpc'])
def test_should_copy_files_in_directories_to_htpc(completed_torrents, automator, sftpclient, remote_base_dir,
                                                  download_dir):
    nested_file = 'dir1/dir2/nested_file.avi'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [nested_file])]
    automator.run()
    assert sftpclient.isdir(remote_base_dir + '/movies/dir1/dir2')
    assert sftpclient.isfile(remote_base_dir + '/movies/' + nested_file)


def test_should_copy_avi_video(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    avi_file = 'dir/video.avi'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [avi_file])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + avi_file)


def test_should_copy_mkv_video(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    avi_file = 'dir/video.mkv'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [avi_file])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + avi_file)


def test_should_copy_mp4_video(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    avi_file = 'dir/video.mp4'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [avi_file])]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + avi_file)


def test_should_not_copy_garbage_files(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    info_file = 'dir/release.nfo'
    exec_file = 'dir/release.exe'
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, [info_file, exec_file])]
    automator.run()
    assert not sftpclient.exists(remote_base_dir + '/movies/' + info_file)
    assert not sftpclient.exists(remote_base_dir + '/movies/' + exec_file)


def test_should_copy_only_largest_video_file_when_multiple_are_present(completed_torrents, automator, sftpclient,
                                                                       remote_base_dir, download_dir):
    sample_video = 'dir/sample.avi'
    main_video = 'dir/video.mkv'
    tor = completed_torrent_with_data_files(download_dir, [sample_video, main_video])
    files = tor.files()
    files[0]['size'] = 1
    files[1]['size'] = 2
    tor.files.return_value = files
    completed_torrents.return_value = [tor]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + main_video)
    assert not sftpclient.exists(remote_base_dir + '/movies/' + sample_video)


def test_should_copy_subtitles(completed_torrents, automator, sftpclient, remote_base_dir, download_dir):
    sub = 'dir/file.sub'
    idx = 'dir/file.idx'
    srt = 'dir/dir2/file.srt'
    smi = 'dir/file.smi'
    ssa = 'dir/file.ssa'
    ass = 'dir/file.ass'
    vtt = 'dir/file.vtt'
    subtitles = [sub, idx, srt, smi, ssa, ass, vtt]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, subtitles)]
    automator.run()
    for path in subtitles:
        assert sftpclient.isfile(remote_base_dir + '/movies/' + path)


def test_should_do_nothing_when_there_are_sidecar_subs_present(completed_torrents, automator, sftpclient,
                                                               remote_base_dir, download_dir):
    sidecar = 'dir/subtitles.srt'
    main_video = 'dir/video.mkv'
    other_sub = 'dir/sub/sub.sub'
    files = [sidecar, main_video, other_sub]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, files)]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + sidecar)
    assert sftpclient.isfile(remote_base_dir + '/movies/' + other_sub)
    assert not sftpclient.exists(remote_base_dir + '/movies/dir/sub.sub')


def test_should_sidecar_vobsub_when_there_is_no_sidecar(completed_torrents, automator, sftpclient, remote_base_dir,
                                                        download_dir):
    main_video = 'dir/video.mkv'
    vob = 'dir/sub/sub.idx'
    sub = 'dir/sub/sub.sub'
    other_sub = 'dir/sub/sub.srt'
    files = [main_video, vob, sub, other_sub]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, files)]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/' + vob)
    assert sftpclient.isfile(remote_base_dir + '/movies/' + sub)
    assert sftpclient.isfile(remote_base_dir + '/movies/' + other_sub)
    assert sftpclient.isfile(remote_base_dir + '/movies/dir/sub.idx')
    assert sftpclient.isfile(remote_base_dir + '/movies/dir/sub.sub')
    assert not sftpclient.exists(remote_base_dir + '/movies/dir/sub.srt')


def test_should_sidecar_english_subtitle_when_there_are_non_vobsub_files_and_no_sidecar(completed_torrents,
                                                                                        automator,
                                                                                        sftpclient,
                                                                                        remote_base_dir,
                                                                                        download_dir):
    main_video = 'dir/video.mkv'
    eng_sub = 'dir/sub/sub.en.srt'
    other_sub = 'dir/sub/sub.ch.srt'
    files = [main_video, eng_sub, other_sub]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, files)]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/dir/sub.en.srt')
    assert not sftpclient.exists(remote_base_dir + '/movies/dir/sub.ch.srt')


def test_should_prefer_non_sdh_english_subtitle_when_there_are_multiple_subs(completed_torrents,
                                                                             automator,
                                                                             sftpclient,
                                                                             remote_base_dir,
                                                                             download_dir):
    main_video = 'dir/video.mkv'
    eng_sub = 'dir/sub/English.srt'
    sdh_sub = 'dir/sub/English (SDH).srt'
    files = [main_video, eng_sub, sdh_sub]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, files)]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/dir/English.srt')
    assert not sftpclient.exists(remote_base_dir + '/movies/dir/English (SDH).srt')


def test_should_consider_only_complete_words_when_finding_language_in_subtitle_filename(completed_torrents,
                                                                                        automator,
                                                                                        sftpclient,
                                                                                        remote_base_dir,
                                                                                        download_dir):
    main_video = 'dir/video.mkv'
    unknown_sub = 'dir/sub/engineer.srt'
    sdh_sub = 'dir/sub/English (sdh).srt'
    files = [main_video, unknown_sub, sdh_sub]
    completed_torrents.return_value = [completed_torrent_with_data_files(download_dir, files)]
    automator.run()
    assert sftpclient.isfile(remote_base_dir + '/movies/dir/English (sdh).srt')
    assert not sftpclient.exists(remote_base_dir + '/movies/dir/engineer.srt')


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
