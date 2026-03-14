# Usa uma imagem Python leve e estável
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas o necessário primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código e o cache existente
COPY . .

# Expõe a porta que o FastAPI vai usar
EXPOSE 5000

# --bind 0.0.0.0:5000 diz ao Gunicorn para escutar em todas as interfaces na porta 5000
# miles:app diz ao Gunicorn para procurar o objeto 'app' dentro do arquivo 'miles.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "miles:app"]