FROM python:3.10.20-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-tk \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "landing_ai/src/main.py"]