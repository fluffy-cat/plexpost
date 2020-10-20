FROM python:3.6.9-alpine3.10

COPY build/qemu-arm-static /usr/bin

WORKDIR /app

# Build requirements
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && \
  apk add --update --no-cache --virtual .build-deps build-base python3-dev libffi-dev openssl-dev || true && \
  pipenv install --system --deploy --ignore-pipfile && \
  apk del .build-deps && \
  pip uninstall pipenv -y && \
  apk add --no-cache tzdata

COPY plexpost plexpost
COPY bin/run.sh default_config.yml ./
RUN chmod +x run.sh

VOLUME /config /downloads
ENV PYTHONUNBUFFERED=1
CMD /app/run.sh