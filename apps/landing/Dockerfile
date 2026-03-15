FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/landing/ .
COPY core_i18n.py .
COPY shared/ ./shared/

EXPOSE 20000

CMD ["python", "app.py"]
