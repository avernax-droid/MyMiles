FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .
EXPOSE 5000
CMD ["python", "miles.py"]