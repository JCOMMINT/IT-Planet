FROM python:3.12-slim
WORKDIR /app
COPY shared ./shared
COPY crs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY crs/main.py .
ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
