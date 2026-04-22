FROM python:3.12-slim

# Camoufox requires additional browser deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 \
    libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 \
    libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 xdg-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY shared ./shared
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m camoufox fetch

# ENTRY_POINT controls which service to start:
#   discovery | worker | merge
ENV ENTRY_POINT=worker
ENV PORT=8080

COPY discovery.py worker.py merge.py ./

CMD ["sh", "-c", "uvicorn ${ENTRY_POINT}:app --host 0.0.0.0 --port 8080"]
