FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY shared ./shared
COPY collectors/it_market/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY collectors/it_market/main.py collectors/it_market/scraper.py ./
ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
