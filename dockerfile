# Builder stage
FROM python:3.11@sha256:c5254471e6073d8942091227f469302f85b30d4b23077226f135360491f5226a as builder
WORKDIR /app

ENV RYE_HOME="/opt/rye"
ENV PATH="$RYE_HOME/shims:$PATH"
ENV RYE_INSTALL_OPTION="--yes"
ENV RYE_TOOLCHAIN="/usr/local/bin/python"
ENV RYE_VERSION=0.33.0

RUN curl -sSf https://rye.astral.sh/get > /tmp/get-rye.sh
RUN bash /tmp/get-rye.sh
RUN rm /tmp/get-rye.sh
RUN echo 'source "$HOME/.rye/env"' >> ~/.bashrc

RUN rye config --set-bool behavior.use-uv=true
RUN rye config --set-bool behavior.global-python=true

COPY pyproject.toml requirements.lock /app/
COPY /src/ /app/src
RUN rye build --wheel --clean

# Runner stage
FROM python:3.11-slim@sha256:80bcf8d243a0d763a7759d6b99e5bf89af1869135546698be4bf7ff6c3f98a59 as runner
WORKDIR /app
RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /app/dist /app/dist

# Install uv
RUN pip install uv
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir /app/dist/*.whl

USER appuser
ENTRYPOINT [ "r2s", "sync" ]