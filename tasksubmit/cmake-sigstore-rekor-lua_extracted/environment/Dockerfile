# Using Python 3.11 slim as base because it provides apt and allows installing Lua 5.4.
# This image standardizes the environment for both Python and CMake.
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        cmake \
        curl \
        lua5.4 \
        liblua5.4-dev \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        coreutils zsh \
        make \
    && rm -rf /var/lib/apt/lists/*

COPY verifier-requirements.lock /tmp/verifier-requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --require-hashes --no-deps --no-cache-dir \
      -r /tmp/verifier-requirements.lock

COPY CMakeLists.txt /app/CMakeLists.txt
COPY cmake-presets.yaml /app/cmake-presets.yaml
COPY release-attestations.toml /app/release-attestations.toml
COPY cmake /app/cmake
COPY lua /app/lua
COPY artifacts /app/artifacts
COPY docs /app/docs
COPY tools /app/tools

RUN chmod +x /app/tools/fetch_rekor_entry.sh

WORKDIR /app
