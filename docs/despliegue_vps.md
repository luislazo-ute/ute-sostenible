# Despliegue en un VPS y CI/CD

Para publicar el proyecto en un VPS y hacerlo accesible desde internet, sigue estos pasos.

## 1. Preparación del VPS

1. **Adquirir un VPS**: Puedes usar proveedores como DigitalOcean, AWS, Linode, Contabo, etc. Se recomienda un VPS con al menos 2GB de RAM (ideal 4GB para Odoo) y un sistema operativo basado en Linux (Ubuntu 22.04 LTS o superior).
2. **Instalar Docker y Docker Compose**:
   Sigue las instrucciones oficiales de Docker para instalar el motor de Docker y Docker Compose en tu VPS.
   ```bash
   sudo apt-get update
   sudo apt-get install docker.io docker-compose-v2 git -y
   ```

## 2. Configurar el proyecto en el VPS

1. **Clonar el repositorio**:
   Conéctate por SSH a tu VPS y clona el proyecto en el directorio que prefieras (por ejemplo, `/var/www/ute-sostenible` o `/opt/ute-sostenible`).
   ```bash
   cd /opt
   git clone <URL_DEL_REPOSITORIO> ute-sostenible
   cd ute-sostenible
   ```
2. **Configurar variables de entorno**:
   Copia el archivo de ejemplo y configura contraseñas seguras.
   ```bash
   cp .env.example .env
   nano .env
   ```
3. **Levantar los contenedores**:
   ```bash
   docker compose up -d
   ```

## 3. Publicar en internet (Proxy Inverso y SSL)

Para exponer Odoo de forma segura (con HTTPS), es recomendable usar un proxy inverso como Nginx y obtener un certificado SSL con Let's Encrypt.

1. **Instalar Nginx y Certbot**:
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx -y
   ```
2. **Configurar Nginx**:
   Crea un archivo de configuración para tu dominio:
   ```bash
   sudo nano /etc/nginx/sites-available/ute-sostenible
   ```
   Agrega la siguiente configuración (reemplaza `tu_dominio.com` por tu dominio real):
   ```nginx
   server {
       listen 80;
       server_name tu_dominio.com;

       location / {
           proxy_pass http://localhost:8069;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. **Habilitar el sitio y reiniciar Nginx**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ute-sostenible /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```
4. **Obtener el certificado SSL**:
   ```bash
   sudo certbot --nginx -d tu_dominio.com
   ```

---

# Implementación de CI/CD (Integración y Despliegue Continuo)

Para automatizar el despliegue de las nuevas versiones al VPS, configuraremos un flujo de CI/CD utilizando **GitHub Actions**. Esto permitirá que cada vez que subas cambios a la rama principal (`main`), el VPS automáticamente descargue los cambios y reinicie el servicio.

## Paso a paso para implementar CI/CD en el VPS y GitHub

### 1. Crear un par de llaves SSH en el VPS
Para que GitHub Actions pueda conectarse a tu VPS de forma segura sin contraseña, necesitamos crear llaves SSH.

1. Conéctate a tu VPS por SSH.
2. Genera una nueva llave SSH específicamente para el proyecto (usando un nombre y comentario personalizados para no sobreescribir las existentes):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "ute-sostenible-deploy" -f ~/.ssh/id_rsa_ute_sostenible
   ```
   *Presiona Enter cuando te pida la contraseña (passphrase) para dejarla vacía.*
3. Agrega la llave pública a la lista de llaves autorizadas del servidor:
   ```bash
   cat ~/.ssh/id_rsa_ute_sostenible.pub >> ~/.ssh/authorized_keys
   ```
4. Muestra la llave privada en la pantalla (la necesitaremos para GitHub):
   ```bash
   cat ~/.ssh/id_rsa_ute_sostenible
   ```
   *Copia todo el contenido, incluyendo `-----BEGIN OPENSSH PRIVATE KEY-----` y `-----END OPENSSH PRIVATE KEY-----`.*

### 2. Configurar los Secretos en GitHub
Ve a tu repositorio en GitHub, y navega a **Settings** -> **Secrets and variables** -> **Actions**.
Haz clic en **New repository secret** y añade los siguientes secretos:

- **`VPS_HOST`**: La dirección IP o dominio de tu VPS.
- **`VPS_PORT`**: El puerto SSH de tu VPS (usualmente `22`).
- **`VPS_USER`**: El usuario con el que te conectas al VPS (ej. `root` o `ubuntu`).
- **`VPS_SSH_KEY`**: Pega aquí el contenido de la llave privada (`id_rsa_ute_sostenible`) que copiaste en el paso anterior.
- **`PROJECT_PATH`**: La ruta absoluta donde clonaste el proyecto en el VPS (ej. `/opt/ute-sostenible`).

### 3. Crear el flujo de trabajo (Workflow) en el proyecto
En tu código local, debes crear la carpeta `.github/workflows` y dentro un archivo llamado `deploy.yml`.

1. Crea las carpetas y el archivo (en la raíz de tu proyecto):
   ```bash
   mkdir -p .github/workflows
   touch .github/workflows/deploy.yml
   ```
2. Agrega el siguiente contenido al archivo `deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches:
      - main # Cambia a 'master' si tu rama principal se llama así

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to Server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_PORT }}
          script: |
            cd ${{ secrets.PROJECT_PATH }}
            git pull origin main
            
            # Actualizar el módulo de Odoo por consola (opcional)
            # docker compose exec -T odoo odoo -d ute_sostenible -u ute_sostenible --stop-after-init --no-http
            
            docker compose restart odoo
```

### 4. Probar el CI/CD
Una vez que hayas guardado el archivo `deploy.yml`, haz un commit y súbelo a GitHub:

```bash
git add .github/workflows/deploy.yml
git commit -m "Configurar CI/CD con GitHub Actions"
git push origin main
```

Ve a la pestaña **Actions** en tu repositorio de GitHub. Verás que un nuevo flujo de trabajo se ha ejecutado. Si configuraste todo correctamente, el indicador se pondrá verde, lo que significa que GitHub Actions se conectó a tu VPS, hizo `git pull` de los últimos cambios y reinició el contenedor de Odoo con éxito.
