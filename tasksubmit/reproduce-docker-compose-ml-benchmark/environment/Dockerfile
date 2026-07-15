# Justification: This is a Java 21 task. Since no canonical Java/JDK base image exists on the approved list yet, eclipse-temurin:21-jdk-jammy is used as a proposed addition.
FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        tmux \
        asciinema \
        make \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY verifier-requirements.lock /tmp/verifier-requirements.lock
RUN python3 -m venv --system-site-packages /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --require-hashes --no-deps --no-cache-dir \
      -r /tmp/verifier-requirements.lock

COPY data /app/data
COPY docs /app/docs
COPY src /app/src

WORKDIR /app
