FROM python:3.10-slim as base

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    VENV_PATH="/opt/venv" \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git make \
        curl ca-certificates gnupg apt-transport-https \
        libssl-dev \
        libldap2-dev libsasl2-dev

ARG INCLUDE_DEV_DEPS=false

FROM base as builder

ARG INCLUDE_DEV_DEPS=false

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python-dev git

RUN --mount=type=bind,target=./pyproject.toml,src=./pyproject.toml \
    --mount=type=bind,target=./poetry.lock,src=./poetry.lock \
    --mount=type=cache,target=/root/.cache/pypoetry \
    python -m venv /opt/venv && \
    pip3 install --upgrade pip && \
    pip3 install poetry && \
    poetry install $(if [ $INCLUDE_DEV_DEPS = "false" ]; then echo "--only=main"; else echo "--with=dev"; fi)

COPY ./ /afs_tools
WORKDIR /afs_tools
RUN poetry install --only=root

FROM base

COPY --from=builder /opt/venv/ /opt/venv/
COPY --from=builder /afs_tools/ /afs_tools/
WORKDIR /
