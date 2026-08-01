FROM python:3.10-slim

# FFmpeg install
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Packages install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
