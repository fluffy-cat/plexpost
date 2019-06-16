import sys

import hiyapyco
import transmissionrpc
from apscheduler.schedulers.blocking import BlockingScheduler

import default_flow
from sftp_factory import SFTPFactory


def main():
    confs = [sys.argv[1], sys.argv[2]]
    conf = hiyapyco.load(confs, method=hiyapyco.METHOD_MERGE, mergelists=False, failonmissingfiles=False)
    transmission = create_transmission(conf['transmission'])
    default_proc = default_flow.DefaultPostProcessor(transmission=transmission,
                                                     assistant_url=conf['home_assistant']['url'],
                                                     assistant_token=conf['home_assistant']['token'],
                                                     htpc_switch=conf['home_assistant']['htpc_switch'],
                                                     sftp_factory=SFTPFactory(conf['sftp']),
                                                     uncategorised_downloads_dir=conf['default_flow'][
                                                         'uncategorised_downloads_dir'])
    scheduler = BlockingScheduler()
    scheduler.add_job(default_proc.run, 'interval', minutes=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


def create_transmission(conf):
    return transmissionrpc.Client(conf['url'], conf['port'], conf['username'], conf['password'])


if __name__ == '__main__':
    main()
