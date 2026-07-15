FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    lua5.3 \
    liblua5.3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Safely copy every asset folder from the build context into the root /app layout
COPY tools/ /app/tools/
COPY artifacts/ /app/artifacts/
COPY environment/ /app/environment/
COPY tests/ /app/tests/

# Make sure the entry script is at /app/solve.sh exactly as expected
COPY environment/solve.sh /app/solve.sh
RUN chmod +x /app/solve.sh

ENTRYPOINT ["/app/solve.sh"]
