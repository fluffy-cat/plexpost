# Plexpost
This is an automation script to organize downloaded media files.

## Usage
The script is distributed as a docker image for Raspberry Pi. Start the service by running `docker run fluffycat/plexpost`.

## Parameters
`-v <path/to/plexpost/config>:/config`
The path where you wish to your config file

`-v <path/to/completed/downloads>:/downloads`
Directory for completed media file. Plexpost will organize media files from this base directory. 

`-v <path/to/ssh/keys/for/sftp>:/keys:ro`
Sftp keys to the remote storage go here.

`-e TZ=<your local time zone>`
Set this environment variable to configure your time zone.