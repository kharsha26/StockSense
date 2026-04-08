FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Install numpy first
RUN pip install --no-cache-dir numpy==1.26.4

# Then install rest
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]