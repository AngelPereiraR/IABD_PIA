# Usamos una imagen base de Python 3.11
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias
# build-essential: compilar librerias
# texlive-full: LaTeX para compilar CVs a PDF (~5GB, pero cacheado en HF)
RUN apt-get update && apt-get install -y \
    build-essential \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero el requirements.txt para aprovechar la cache de Docker
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del codigo de la aplicacion
# Nota: NO copiamos .env, credentials.json ni token.json (ver .dockerignore)
COPY src/ src/
COPY data/ data/
COPY main.py .

# Copiamos el script de entrada que gestionara las credenciales
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Comando para ejecutar la aplicacion usando el script de entrada
ENTRYPOINT ["./entrypoint.sh"]