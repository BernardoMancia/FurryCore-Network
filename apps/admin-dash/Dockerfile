FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY ./apps/admin-dash/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/admin-dash/ .
COPY shared/ ./shared/

RUN mkdir -p /app/database

EXPOSE 29999

CMD ["gunicorn", "--bind", "0.0.0.0:29999", "--workers", "2", "--timeout", "120", "app:app"]
