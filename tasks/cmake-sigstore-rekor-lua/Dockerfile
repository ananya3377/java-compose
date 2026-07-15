FROM python:3.13-slim

# Install core compilation and runtime dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    lua5.3 \
    liblua5.3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Explicitly copy required folders into the image structure
COPY tools/ /app/tools/
COPY artifacts/ /app/artifacts/
COPY environment/ /app/environment/
COPY solution/solve.sh /app/solve.sh
COPY tests/ /app/tests/

RUN chmod +x /app/solve.sh

ENTRYPOINT ["/app/solve.sh"]
