FROM alpine:3.18
LABEL maintainer="Thomas GUIRRIEC <thomas@guirriec.fr>"
ENV DOCKERHUB_LIMIT_EXPORTER_PORT=8123
ENV DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL='INFO'
ENV DOCKERHUB_LIMIT_EXPORTER_NAME='dockerhub-limit-exporter'
ENV SCRIPT='dockerhub_limit_exporter.py'
ENV USERNAME="exporter"
ENV UID="1000"
ENV GID="1000"
COPY apk_packages /
COPY pip_packages /
ENV VIRTUAL_ENV="/dockerhub-limit-exporter"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN xargs -a /apk_packages apk add --no-cache --update \
    && python3 -m venv ${VIRTUAL_ENV} \
    && pip install --no-cache-dir --no-dependencies --no-binary :all: -r pip_packages \
    && pip uninstall -y setuptools pip \
    && useradd -l -u ${UID} -U -s /bin/sh ${USERNAME} \
    && rm -rf \
        /root/.cache \
        /tmp/* \
        /var/cache/*
COPY --chown=${USERNAME}:${USERNAME} --chmod=500 ${SCRIPT} ${VIRTUAL_ENV}
COPY --chown=${USERNAME}:${USERNAME} --chmod=500 entrypoint.sh /
USER ${USERNAME}
WORKDIR ${VIRTUAL_ENV}
EXPOSE ${DOCKERHUB_LIMIT_EXPORTER_PORT}
HEALTHCHECK CMD nc -vz localhost ${DOCKERHUB_LIMIT_EXPORTER_PORT} || exit 1 # nosemgrep
ENTRYPOINT ["/entrypoint.sh"]
