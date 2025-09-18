#!/bin/bash

# Exit immediately if a command fails
set -e

# Build the Docker image
echo "Construyendo la imagen climas-app..."
docker build -t climas-app .

# Stop and remove any previous container with the same name
if [ "$(docker ps -aq -f name=climas-app)" ]; then
    echo "Eliminando contenedor existente climas-app..."
    docker stop climas-app || true
    docker rm climas-app || true
fi

# Run the container
echo "Iniciando contenedor climas-app..."
docker run -d \
  --name climas-app \
  -p 8080:8000 \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  climas-app

echo "Contenedor climas-app está corriendo en http://localhost:8080"

echo "Aplicando migraciones..."
docker exec -it climas-app python manage.py migrate

echo "La aplicación está disponible en: http://localhost:8080"

#docker exec -it climas-app python manage.py migrate
#docker exec -it climas-app python manage.py createsuperuser
