# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /workspace

# Install build dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install agentbeats

# Stage 2: Runtime
FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/agentbeats/agentbeats" \
      org.opencontainers.image.description="GAIA Benchmark on AgentBeats - General AI Assistants evaluation" \
      org.opencontainers.image.version="1.0.0"

WORKDIR /workspace

# Copy build artifacts to runtime image
COPY --from=builder /usr/local /usr/local

# Copy scenario files
COPY . /workspace

# Environment variables
ENV SCENARIO_ROOT=/workspace \
    PYTHONUNBUFFERED=1 \
    AB_HOST=0.0.0.0 \
    AB_START_WAIT=1

# Health check (green agent on port 9001)
HEALTHCHECK CMD ["/bin/bash","-c","curl -fs http://localhost:${HEALTHCHECK_PORT:-9001}/health || exit 1"]

# Entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]
