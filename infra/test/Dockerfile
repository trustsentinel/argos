FROM python:3.12-slim

WORKDIR /test

RUN pip install --no-cache-dir pika==1.3.2 elasticsearch==8.15.1

COPY e2e.py mock_btc_node.py ./

ENV PYTHONUNBUFFERED=1
