FROM python:3.11-slim-bookworm

LABEL maintainer="fahmula"

RUN adduser pythonapp

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chown -R pythonapp:pythonapp /app

ENV PYTHONUNBUFFERED=1

USER pythonapp

EXPOSE 5000

CMD ["python3", "main.py"]