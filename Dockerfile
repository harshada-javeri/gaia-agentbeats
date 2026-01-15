FROM ghcr.io/astral-sh/uv:python3.12-trixie

RUN adduser agentbeats
USER agentbeats

RUN mkdir -p /home/agentbeats/.cache/uv
WORKDIR /home/agentbeats/gaia

COPY pyproject.toml uv.lock README.md ./
COPY src src

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN --mount=type=cache,target=/home/agentbeats/.cache/uv,uid=1000 \
    uv sync --no-dev --frozen

ENTRYPOINT ["uv", "run", "src/green_agent/agent.py"]
