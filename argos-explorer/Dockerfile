FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Discover peers on a network and publish them to the broker.
# Override the flags via the compose `command:` (e.g. --network eth).
ENTRYPOINT ["python", "argosx.py"]
CMD ["--network", "btc", "--maxpeers", "20", "--maxdepth", "5"]
