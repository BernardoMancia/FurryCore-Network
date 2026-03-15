FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./apps/admin-dash/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/admin-dash/ .

# Garante que o diretório de banco de dados exista dentro do container
RUN mkdir -p /app/database

EXPOSE 29999

CMD ["python", "app.py"]
