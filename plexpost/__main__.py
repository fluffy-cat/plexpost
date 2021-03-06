import sys

import hiyapyco
import transmissionrpc
from apscheduler.schedulers.blocking import BlockingScheduler

from plexpost import post_processor, movies_flow, htpc_switch, sftp_factory, default_flow, show_flow


def main():
    confs = [sys.argv[1], sys.argv[2]]
    conf = hiyapyco.load(confs, method=hiyapyco.METHOD_MERGE, mergelists=False, failonmissingfiles=False)
    transmission = create_transmission(conf['transmission'])
    sftp = sftp_factory.SFTPFactory(conf['sftp'])
    switch = create_htpc_switch(conf['home_assistant'])
    scheduler = BlockingScheduler()
    if 'default_flow' in conf:
        create_schedule(scheduler, transmission, switch, sftp, default_flow.DefaultPostProcessor(conf['default_flow']))
    if 'movies_flow' in conf:
        create_schedule(scheduler, transmission, switch, sftp, movies_flow.MoviePostProcessor(conf['movies_flow']))
    if 'tv_flow' in conf:
        create_schedule(scheduler, transmission, switch, sftp, show_flow.ShowPostProcessor(conf['tv_flow']))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


def create_schedule(scheduler, transmission, htpc_switch, sftp, plugin):
    proc = post_processor.PostProcessor(transmission, htpc_switch, sftp, plugin)
    scheduler.add_job(proc.run, 'interval', minutes=1)


def create_htpc_switch(conf):
    return htpc_switch.HTPCSwitch(conf['url'], conf['token'], conf['htpc_switch'])


def create_transmission(conf):
    return transmissionrpc.Client(conf['url'], conf['port'], conf['username'], conf['password'])


if __name__ == '__main__':
    main()
