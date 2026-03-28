FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/landing/ .
COPY core_i18n.py .
COPY shared/ ./shared/

EXPOSE 20000

CMD ["gunicorn", "--bind", "0.0.0.0:20000", "--workers", "2", "--timeout", "120", "app:app"]
