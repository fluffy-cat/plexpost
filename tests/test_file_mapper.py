import errno
import os
from unittest.mock import Mock

import pytest

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
