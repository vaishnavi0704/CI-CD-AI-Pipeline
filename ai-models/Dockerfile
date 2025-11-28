FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy models and code
COPY models/ models/
COPY training/ training/
COPY serving/ serving/

WORKDIR /app/serving

EXPOSE 5000

CMD ["python", "model_server.py"]