FROM python:3.10-slim

# System level par sqlite3 packages install karna
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies copy aur install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot code copy karna
COPY . .

# Bot run karna
CMD ["python", "bot.py"]
