FROM python:3.7.3-alpine3.10

COPY build/qemu-arm-static /usr/bin

WORKDIR /app

# Build requirements
COPY requirements.lock ./
RUN apk add --update --no-cache --virtual .build-deps build-base python3-dev libffi-dev openssl-dev || true && \
  pip install --no-cache-dir -r requirements.lock && \
  apk del .build-deps && \
  apk add --no-cache tzdata

COPY plexpost plexpost
COPY bin/run.sh default_config.yml ./
RUN chmod +x run.sh

VOLUME /config /downloads
ENV PYTHONUNBUFFERED=1
CMD /app/run.sh