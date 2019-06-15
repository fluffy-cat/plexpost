FROM python:3.7.3-alpine3.9

WORKDIR /app

# Build requirements
COPY requirements.lock .
RUN apk add --update --no-cache --virtual .build-deps build-base python3-dev libffi-dev openssl-dev && \
  pip install --no-cache-dir -r requirements.lock && \
  apk del .build-deps

COPY *.py default_config.yml ./

VOLUME /config /downloads

CMD ["/usr/local/bin/python", "plexpost.py", "default_config.yml", "/config/config.yml"]