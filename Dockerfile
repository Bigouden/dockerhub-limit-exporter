# kics-scan disable=f2f903fb-b977-461e-98d7-b3e2185c6118,9513a694-aa0d-41d8-be61-3271e056f36b,d3499f6d-1651-41bb-a9a7-de925fea487b,ae9c56a6-3ed1-4ac0-9b54-31267f51151d,4b410d24-1cbe-4430-a632-62c9a931cf1c

ARG ALPINE_VERSION="3.22"

FROM alpine:${ALPINE_VERSION} AS builder
COPY --link apk_packages pip_packages /tmp/
# hadolint ignore=DL3018
RUN --mount=type=cache,id=builder_apk_cache,target=/var/cache/apk \
    apk add gettext-envsubst

FROM alpine:${ALPINE_VERSION}
LABEL maintainer="Thomas GUIRRIEC <thomas@guirriec.fr>"
ENV DOCKERHUB_LIMIT_EXPORTER_PORT=8123
ENV DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL='INFO'
ENV DOCKERHUB_LIMIT_EXPORTER_NAME='dockerhub-limit-exporter'
ENV SCRIPT='dockerhub_limit_exporter.py'
ENV USERNAME="exporter"
ENV UID="1000"
ENV GID="1000"
ENV VIRTUAL_ENV="/dockerhub-limit-exporter"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# hadolint ignore=DL3013,DL3018,DL3042,SC2006
RUN --mount=type=bind,from=builder,source=/usr/bin/envsubst,target=/usr/bin/envsubst \
    --mount=type=bind,from=builder,source=/usr/lib/libintl.so.8,target=/usr/lib/libintl.so.8 \
    --mount=type=bind,from=builder,source=/tmp,target=/tmp \
    --mount=type=cache,id=apk_cache,target=/var/cache/apk \
    --mount=type=cache,id=pip_cache,target=/root/.cache \
    apk --update add `envsubst < /tmp/apk_packages` \
    && python3 -m venv "${VIRTUAL_ENV}" \
    && pip install --no-dependencies --no-binary :all: `envsubst < /tmp/pip_packages` \
    && pip uninstall -y setuptools pip \
    && useradd -l -u "${UID}" -U -s /bin/sh "${USERNAME}" 
COPY --link --chmod=755 ${SCRIPT} ${VIRTUAL_ENV}
COPY --link --chmod=755 entrypoint.sh /
USER ${USERNAME}
WORKDIR ${VIRTUAL_ENV}
EXPOSE ${DOCKERHUB_LIMIT_EXPORTER_PORT}
HEALTHCHECK CMD nc -vz localhost "${DOCKERHUB_LIMIT_EXPORTER_PORT}" || exit 1 # nosemgrep
ENTRYPOINT ["/entrypoint.sh"]
