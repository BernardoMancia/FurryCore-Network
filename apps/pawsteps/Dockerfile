FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/pawsteps/ .
COPY core_i18n.py .
COPY shared/ ./shared/

RUN mkdir -p /app/database /app/static/uploads /app/shared_data/cgrf /app/shared_data/shop

EXPOSE 20001

CMD ["gunicorn", "--bind", "0.0.0.0:20001", "--workers", "3", "--timeout", "120", "app:app"]
