import sys

import hiyapyco
import transmissionrpc
from apscheduler.schedulers.blocking import BlockingScheduler

import default_flow
import movies_flow
import sftp_factory


def main():
    confs = [sys.argv[1], sys.argv[2]]
    conf = hiyapyco.load(confs, method=hiyapyco.METHOD_MERGE, mergelists=False, failonmissingfiles=False)
    transmission = create_transmission(conf['transmission'])
    sftp = sftp_factory.SFTPFactory(conf['sftp'])
    scheduler = BlockingScheduler()
    default_proc = default_flow.DefaultPostProcessor(transmission=transmission,
                                                     assistant_url=conf['home_assistant']['url'],
                                                     assistant_token=conf['home_assistant']['token'],
                                                     htpc_switch=conf['home_assistant']['htpc_switch'],
                                                     sftp_factory=sftp,
                                                     download_dir_tag=conf['default_flow']['download_dir_tag'])
    scheduler.add_job(default_proc.run, 'interval', minutes=1)
    movie_proc = movies_flow.MoviePostProcessor(transmission=transmission,
                                                assistant_url=conf['home_assistant']['url'],
                                                assistant_token=conf['home_assistant']['token'],
                                                htpc_switch=conf['home_assistant']['htpc_switch'],
                                                sftp_factory=sftp,
                                                download_dir_tag=conf['movies_flow']['download_dir_tag'])
    scheduler.add_job(movie_proc.run, 'interval', minutes=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


def create_transmission(conf):
    return transmissionrpc.Client(conf['url'], conf['port'], conf['username'], conf['password'])


if __name__ == '__main__':
    main()
