FROM python:3.11-slim

WORKDIR /app

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
