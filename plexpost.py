import sys

import hiyapyco
import pysftp
import transmissionrpc
from apscheduler.schedulers.blocking import BlockingScheduler

import default_flow


def main():
    confs = [sys.argv[1], sys.argv[2]]
    conf = hiyapyco.load(confs, method=hiyapyco.METHOD_MERGE, mergelists=False, failonmissingfiles=False)
    transmission = create_transmission(conf['transmission'])
    sftp = create_sftp(conf['sftp'])
    default_processor = default_flow.DefaultPostProcessor(transmission=transmission,
                                                          assistant_url=conf['home_assistant']['url'],
                                                          assistant_token=conf['home_assistant']['token'],
                                                          htpc_switch=conf['home_assistant']['htpc_switch'],
                                                          sftpclient=sftp,
                                                          sftp_remote_dir=conf['sftp']['remote_dir'],
                                                          download_dir=conf['download_dir'])
    scheduler = BlockingScheduler()
    scheduler.add_job(default_processor.run, 'interval', minutes=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    sftp.close()


def create_transmission(conf):
    return transmissionrpc.Client(conf['url'], conf['port'], conf['username'], conf['password'])


def create_sftp(conf):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    return pysftp.Connection(conf['url'], port=conf['port'], username=conf['username'], private_key=conf['key_path'],
                             cnopts=cnopts)


if __name__ == '__main__':
    main()
