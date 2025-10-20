#!/bin/bash

# Exit immediately if a command fails
set -e

# Verify .env exists
if [ ! -f .env ]; then
    echo "ERROR: Archivo .env no encontrado."
    echo "Por favor ejecute: cp .env.example .env && nano .env"
    exit 1
fi

# Check for example/placeholder values (basic safety)
if grep -q "your_database_name" .env; then
    echo "ERROR: .env contiene valores de ejemplo. Por favor, edite el archivo y asigne valores reales."
    exit 1
fi

if grep -q "mydomain.mysite.com" .env; then
    echo "ADVERTENCIA: Se está usando un dominio de ejemplo. Asegúrese de que esto es intencional."
fi

# Secure file permissions
chmod 600 .env

# Build the Docker image
echo "Construyendo la imagen climas-app..."
docker build -t climas-app .

# Stop and remove any previous container with the same name
if [ "$(docker ps -aq -f name=climas-app)" ]; then
    echo "Eliminando contenedor existente climas-app..."
    docker stop climas-app || true
    docker rm climas-app || true
fi

# Create volume
docker create volume climashub
# Run the container
echo "Iniciando contenedor climas-app..."
docker run -d \
  --name climas-app \
  -p 8220:8000 \
  --env-file .env \
  -v climashub:/app/staticfiles:rw \
  climas-app

echo "Contenedor climas-app está corriendo en http://localhost:8220"

echo "Aplicando migraciones..."
docker exec -it climas-app python manage.py migrate

echo "La aplicación está disponible en: http://localhost:8220"

#docker exec -it climas-app python manage.py migrate
#docker exec -it climas-app python manage.py createsuperuser
