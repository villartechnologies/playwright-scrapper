# Guía de Despliegue - Aplicación Flask

## Opciones de Despliegue

### 1. Servidor VPS/Dedicado (Recomendado)

#### Requisitos del Servidor:
- Ubuntu 20.04+ o CentOS 7+
- Python 3.8+
- Nginx (opcional, para proxy reverso)
- Supervisor (opcional, para gestión de procesos)

#### Pasos de Despliegue:

1. **Clonar el repositorio:**
```bash
git clone <tu-repositorio>
cd Miniproyecto
```

2. **Ejecutar el script de despliegue:**
```bash
chmod +x deploy.sh
./deploy.sh
```

3. **Ejecutar la aplicación:**
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar en producción
gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4

# O ejecutar en desarrollo
python app.py
```

### 2. Heroku

1. **Instalar Heroku CLI**
2. **Login a Heroku:**
```bash
heroku login
```

3. **Crear aplicación:**
```bash
heroku create tu-app-name
```

4. **Configurar variables de entorno:**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

5. **Desplegar:**
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 3. Railway

1. **Conectar repositorio a Railway**
2. **Configurar variables de entorno:**
   - `FLASK_ENV=production`
   - `SECRET_KEY=<tu-secret-key>`
3. **Deploy automático**

### 4. DigitalOcean App Platform

1. **Conectar repositorio**
2. **Configurar build command:**
```bash
pip install -r requirements.txt && playwright install
```
3. **Configurar run command:**
```bash
gunicorn wsgi:app
```

## Configuración de Nginx (Opcional)

Si quieres usar Nginx como proxy reverso:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Configuración de Supervisor (Opcional)

Crear archivo `/etc/supervisor/conf.d/flask-app.conf`:

```ini
[program:flask-app]
command=/ruta/a/tu/proyecto/venv/bin/gunicorn wsgi:app --bind 127.0.0.1:8000
directory=/ruta/a/tu/proyecto
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/flask-app.log
```

## Variables de Entorno

Configura estas variables en tu servidor:

- `FLASK_ENV=production`
- `SECRET_KEY=<tu-secret-key-seguro>`

## Monitoreo y Logs

- **Logs de Gunicorn:** Se guardan automáticamente
- **Monitoreo:** Considera usar herramientas como Sentry para errores
- **Métricas:** Puedes agregar Prometheus para métricas

## Seguridad

1. **Cambiar SECRET_KEY** en producción
2. **Configurar firewall** (solo puertos necesarios)
3. **Usar HTTPS** con Let's Encrypt
4. **Actualizar dependencias** regularmente

## Troubleshooting

### Error: "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Playwright browsers not found"
```bash
playwright install
```

### Error: "Permission denied"
```bash
chmod +x deploy.sh
```

## Contacto

Si tienes problemas con el despliegue, revisa los logs y asegúrate de que todas las dependencias estén instaladas correctamente. 