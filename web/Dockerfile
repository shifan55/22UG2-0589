FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Default port the app listens on
EXPOSE 8000

# Run the app
CMD ["python", "app.py"]
