FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app/.
RUN pip install --no-cache-dir -r requirements.txt


ENTRYPOINT ["python", "/app/main.py"]
