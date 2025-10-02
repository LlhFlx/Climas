# Climas App

Aplicación contenida en **Docker** lista para ejecutarse de forma sencilla.  
Este repositorio incluye todo lo necesario para construir y correr la aplicación en un contenedor aislado.

---

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) instalado en el servidor.
- Archivo `.env` con las variables de entorno necesarias (se debe ubicar en la raíz del proyecto).

---

## Construcción de la imagen

Para construir la imagen Docker de la aplicación, ejecutar en la raíz del proyecto:

```bash
docker build -t climas-app .
```
---
## Ejecución del contenedor

Una vez construida la imagen, ejecutar la aplicación con:
```bash
docker run -d \
  --name climas-app \
  -p 8080:8000 \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  climas-app

```

### Explicación de Parámetros

| Parámetro | Descripción |
|----------|-------------|
| `-d` | Ejecuta el contenedor en **segundo plano** (modo *detached*), permitiendo que la terminal siga disponible para otros comandos. |
| `--name climas-app` | Asigna un nombre descriptivo al contenedor (`climas-app`) para facilitar su gestión, inspección y eliminación posterior. |
| `-p 8080:8000` | Mapea el puerto **8000 del contenedor** al puerto **8080 de la máquina anfitriona**. Esto permite acceder a la aplicación desde el navegador vía `http://localhost:8080`. |
| `--env-file .env` | Carga todas las variables de entorno definidas en el archivo `.env` ubicado en el directorio actual, asegurando que configuraciones sensibles (como claves, credenciales de DB, etc.) se inyecten sin exponerlas en la línea de comandos. |
| `--add-host=host.docker.internal:host-gateway` | Permite que el contenedor resuelva el nombre `host.docker.internal` y lo dirija hacia la **máquina anfitriona** (PC o servidor). Esto es esencial para que la app dentro del contenedor pueda conectarse a servicios externos (como una base de datos MariaDB) que corren en la máquina host. |


## Script de ayuda: `run-django.sh`

Este repositorio incluye un script para automatizar la construcción, ejecución y aplicación de migraciones en el contenedor.

### Ejecutar el script

```bash
./run-django.sh
```

Este comando hará lo siguiente:

1. Construir la imagen `climas-app`.  
2. Detener y eliminar cualquier contenedor previo llamado `climas-app`.  
3. Iniciar un nuevo contenedor.  
4. Ejecutar las migraciones de Django (`python manage.py migrate`).  

La aplicación quedará disponible en:  
[http://localhost:8080](http://localhost:8080)

---

## Crear un superusuario en Django

Para crear un superusuario y poder acceder a **Django Admin**, se debe ejecutar:

```bash
docker exec -it climas-app python manage.py createsuperuser
```

---


## Detener y eliminar el contenedor

```bash
docker stop climas-app
docker rm climas-app
```

---

## Notas

- El puerto **8080** no debe estar ocupado por otro servicio en la máquina, en caso de estar, se puede cambiar el puerto del contenedor manualmente.  
- Para reconstruir la imagen tras cambios en el código, usar:

```bash
docker build -t climas-app .
```

y luego volver a ejecutar el contenedor o el script `run-django.sh`.
- Hay emoticones en el archivo
`/myenv/lib64/python3.10/site-packages/pip/_vendor/rich/_emoji_codes.py`

---
