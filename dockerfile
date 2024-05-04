FROM python:3.12

ENV UV_SYSTEM_PYTHON=1

RUN pip install uv
COPY requirements.lock pyproject.toml README.md ./
RUN uv pip install -r requirements.lock
COPY . ./
RUN uv pip install .
CMD ["python", "src/rescuetime_to_gcal/main.py"]
