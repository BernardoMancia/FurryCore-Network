FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apps/cgrf/ .

EXPOSE 20002

CMD ["python", "app.py"]
