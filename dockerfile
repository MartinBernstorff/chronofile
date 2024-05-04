FROM python:3.12

RUN pip install uv
COPY requirements.lock pyproject.toml README.md ./
RUN uv venv
RUN uv pip install .
COPY . .
RUN uv pip install .
CMD ["python", "src/rescuetime_to_gcal/main.py"]
