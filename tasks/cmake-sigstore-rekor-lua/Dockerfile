FROM python:3.13-slim

# Install system compilation setups
RUN apt-get update && apt-get install -y \
    cmake \
    lua5.3 \
    liblua5.3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the asset folders that we just moved into the task context folder
COPY tools/ /app/tools/
COPY artifacts/ /app/artifacts/
COPY environment/ /app/environment/
COPY tests/ /app/tests/
COPY environment/lua/ /app/lua/

# Position solve.sh at the expected root execution path
COPY environment/solve.sh /app/solve.sh
RUN chmod +x /app/solve.sh

ENTRYPOINT ["/app/solve.sh"]
