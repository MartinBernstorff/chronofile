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

COPY pyproject.toml requirements.lock /app/
COPY /src/ /app/src
RUN rye build --wheel --clean

# Runner stage
FROM python:3.11-slim as runner
WORKDIR /app
RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /app/dist /app/dist

# Install uv
RUN pip install uv
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir /app/dist/*.whl

USER appuser
ENTRYPOINT [ "r2s", "sync" ]