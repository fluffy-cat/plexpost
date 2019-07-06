#!/usr/bin/env sh

# Setup time zone
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
echo $TZ > /etc/timezone

python /app/plexpost.py /app/default_config.yml /config/config.yml