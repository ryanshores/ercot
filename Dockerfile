FROM python:3.11-slim
LABEL authors="ryanshores"

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-m", "src.main"]