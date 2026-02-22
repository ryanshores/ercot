FROM python:3.11-slim
LABEL authors="ryanshores"

WORKDIR /usr/src/app

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

#COPY . .
COPY alembic ./alembic
COPY alembic.ini .
COPY entrypoint.sh .
COPY src ./src
COPY templates ./templates

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]