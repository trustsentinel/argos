FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Reference consumer: logs every peer event for a given network.
ENTRYPOINT ["python", "argopro.py"]
CMD ["--network", "btc"]
