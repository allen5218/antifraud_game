FROM postgres:17-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        python3 \
        python3-jsonschema \
    && rm -rf /var/lib/apt/lists/*
