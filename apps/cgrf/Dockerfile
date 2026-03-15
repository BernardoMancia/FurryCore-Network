FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/cgrf/ .
COPY core_i18n.py .
COPY shared/ ./shared/

RUN mkdir -p /app/database /app/shared_data/pawsteps /app/shared_data/shop

EXPOSE 20002

CMD ["python", "app.py"]
