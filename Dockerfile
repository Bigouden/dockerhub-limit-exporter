FROM alpine:3.15
LABEL maintainer="Thomas GUIRRIEC <thomas@guirriec.fr>"
ENV DOCKERHUB_LIMIT_EXPORTER_PORT=8123
ENV DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL='INFO'
ENV DOCKERHUB_LIMIT_EXPORTER_NAME='dockerhub-limit-exporter'
COPY requirements.txt /
COPY entrypoint.sh /
ENV VIRTUAL_ENV="/dockerhub-limit-exporter"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN apk add --no-cache --update \
         python3 \
    && python3 -m venv ${VIRTUAL_ENV} \
    && pip install --no-cache-dir --no-dependencies --no-binary :all: -r requirements.txt \
    && pip uninstall -y setuptools pip \
    && rm -rf \
        /root/.cache \
        /tmp/* \
        /var/cache/* \
    && chmod +x /entrypoint.sh
COPY dockerhub_limit_exporter.py ${VIRTUAL_ENV}
WORKDIR ${VIRTUAL_ENV}
HEALTHCHECK CMD nc -vz localhost ${DOCKERHUB_LIMIT_EXPORTER_PORT} || exit 1
ENTRYPOINT ["/entrypoint.sh"]
