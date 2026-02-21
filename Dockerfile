FROM python:3.11-slim
LABEL authors="ryanshores"

WORKDIR /usr/src/app

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-m", "src.main"]