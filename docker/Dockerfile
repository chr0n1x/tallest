FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV SRC=/app
WORKDIR $SRC

COPY requirements.txt $SRC
RUN pip install --no-cache-dir -r requirements.txt

COPY . $SRC

ENTRYPOINT python main.py
