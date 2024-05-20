FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app
COPY . /app

RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl