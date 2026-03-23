<<<<<<< HEAD
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
=======
# Usa uma imagem Python leve e estável
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas o necessário primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código e o cache existente
COPY . .

# Expõe a porta que o Flask vai usar
EXPOSE 5000

# Adicionado --timeout 120 para dar tempo à IA de processar textos grandes
# --bind 0.0.0.0:5000 diz ao Gunicorn para escutar em todas as interfaces na porta 5000
# miles:app diz ao Gunicorn para procurar o objeto 'app' dentro do arquivo 'miles.py'
CMD ["gunicorn", "--timeout", "120", "--bind", "0.0.0.0:5000", "miles:app"]
>>>>>>> d10e5449e13c53935bbe0eba624404f25bc0ee3f
