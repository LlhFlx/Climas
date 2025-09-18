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

### 🔍 Explicación de Parámetros

| Parámetro | Descripción |
|----------|-------------|
| `-d` | Ejecuta el contenedor en **segundo plano** (modo *detached*), permitiendo que la terminal siga disponible para otros comandos. |
| `--name climas-app` | Asigna un nombre descriptivo al contenedor (`climas-app`) para facilitar su gestión, inspección y eliminación posterior. |
| `-p 8080:8000` | Mapea el puerto **8000 del contenedor** al puerto **8080 de la máquina anfitriona**. Esto permite acceder a la aplicación desde el navegador vía `http://localhost:8080`. |
| `--env-file .env` | Carga todas las variables de entorno definidas en el archivo `.env` ubicado en el directorio actual, asegurando que configuraciones sensibles (como claves, credenciales de DB, etc.) se inyecten sin exponerlas en la línea de comandos. |
| `--add-host=host.docker.internal:host-gateway` | Permite que el contenedor resuelva el nombre `host.docker.internal` y lo dirija hacia la **máquina anfitriona** (PC o servidor). Esto es esencial para que la app dentro del contenedor pueda conectarse a servicios externos (como una base de datos MariaDB) que corren en la máquina host. |
