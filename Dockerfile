FROM denoland/deno:alpine-2.9.7 AS deno-stage

FROM python:3.13-alpine AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --root-user-action ignore -r requirements.txt

FROM python:3.13-alpine

LABEL maintainer="dx616b"
LABEL version="2.9.0"
LABEL description="Self-hosted Spotify downloader with slskd and Navidrome sync"

LABEL org.opencontainers.image.title="Downtify" \
      org.opencontainers.image.description="Self-hosted Spotify downloader with slskd and Navidrome sync." \
      org.opencontainers.image.version="2.9.0" \
      org.opencontainers.image.authors="dx616b" \
      org.opencontainers.image.url="https://github.com/dx616b/downtify" \
      org.opencontainers.image.source="https://github.com/dx616b/downtify" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.documentation="https://github.com/dx616b/downtify#readme" \
      org.opencontainers.image.vendor="dx616b" \
      org.opencontainers.image.base.name="python:3.13-alpine"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHON_COLORS=0 \
    DOWNTIFY_LOG_LEVEL=info \
    DOWNTIFY_PORT=8000 \
    UID=1000 \
    GID=1000 \
    UMASK=022

WORKDIR /downtify

# Deno for yt-dlp JS (glibc binary); wrapper avoids breaking Alpine ffmpeg via LD_LIBRARY_PATH.
COPY --from=deno-stage /bin/deno /usr/local/lib/deno-bin
COPY --from=deno-stage /usr/local/lib/ /usr/local/lib/glibc-deno/
RUN mkdir -p /lib64 && \
    ln -snf /usr/local/lib/glibc-deno/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2
RUN printf '%s\n' \
    '#!/bin/sh' \
    'export LD_LIBRARY_PATH=/usr/local/lib/glibc-deno' \
    'exec /usr/local/lib/deno-bin "$@"' \
    > /usr/local/bin/deno && chmod +x /usr/local/bin/deno

RUN apk add --no-cache \
    ffmpeg \
    shadow \
    su-exec \
    tini

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY main.py entrypoint.sh ./
COPY downtify ./downtify
COPY frontend/dist ./frontend/dist

RUN sed -i 's/\r$//g' entrypoint.sh && \
    chmod +x entrypoint.sh

ENV PATH="/home/downtify/.local/bin:${PATH}"

VOLUME /downloads
VOLUME /data

EXPOSE ${DOWNTIFY_PORT}

ENTRYPOINT ["/sbin/tini", "-g", "--", "./entrypoint.sh"]
