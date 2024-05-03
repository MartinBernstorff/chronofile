FROM python:3.12
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY . .
RUN pip install -e .
CMD ["python", "src/rescuetime_to_gcal/main.py"]
