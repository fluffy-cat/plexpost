import time

import pysftp
from paramiko import SSHException


class SFTPFactory:
    def __init__(self, config):
        self.url = config['url']
        self.port = config['port']
        self.username = config['username']
        self.private_key_path = config['key_path']
        self.remote_dir = config['remote_dir']

    def connect(self):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        connection = pysftp.Connection(self.url, port=self.port, username=self.username,
                                       private_key=self.private_key_path, cnopts=cnopts)
        connection.chdir(self.remote_dir)
        return connection

    def await_connection(self):
        for idx in range(0, 30):
            try:
                return self.connect()
            except SSHException:
                time.sleep(1)  # Wait for remote to awaken
