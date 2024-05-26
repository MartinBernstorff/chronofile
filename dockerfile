# Builder stage
FROM python:3.11 as builder
WORKDIR /app

ENV RYE_HOME="/opt/rye"
ENV PATH="$RYE_HOME/shims:$PATH"
ENV RYE_INSTALL_OPTION="--yes"
ENV RYE_TOOLCHAIN="/usr/local/bin/python"
ENV RYE_VERSION=0.33.0

RUN curl -sSf https://rye.astral.sh/get > /tmp/get-rye.sh && \
    bash /tmp/get-rye.sh && \
    rm /tmp/get-rye.sh && \
    echo 'source "$HOME/.rye/env"' >> ~/.bashrc

RUN rye config --set-bool behavior.use-uv=true && \
    rye config --set-bool behavior.global-python=true

COPY /src/ pyproject.toml requirements.lock /app/
RUN rye build --wheel --clean

# Runner stage
FROM python:3.11-slim as runner
WORKDIR /app

# RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /app/dist /app/dist

# USER appuser
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /app/dist/*.whl

# Add any additional commands for the runner stage, such as setting the entrypoint or command
