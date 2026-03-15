FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/shop/ .
COPY core_i18n.py .
COPY shared/ ./shared/

RUN mkdir -p /app/database /app/shared_data/cgrf

EXPOSE 20003

CMD ["python", "app.py"]
