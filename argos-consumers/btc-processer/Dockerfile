FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Consume btc peer events, probe each node, and index findings in Elasticsearch.
CMD ["python", "argobtc.py"]
