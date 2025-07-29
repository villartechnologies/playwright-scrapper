#!/bin/bash

echo "🚀 Iniciando despliegue de la aplicación Flask..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado. Por favor instálalo primero."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Instalar navegadores para Playwright
echo "🌐 Instalando navegadores para Playwright..."
playwright install

# Configurar variables de entorno para producción
export FLASK_ENV=production
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "✅ Despliegue completado!"
echo "🔑 Secret Key generado: $SECRET_KEY"
echo ""
echo "Para ejecutar la aplicación:"
echo "1. Activa el entorno virtual: source venv/bin/activate"
echo "2. Ejecuta: gunicorn wsgi:app --bind 0.0.0.0:8000"
echo ""
echo "Para ejecutar en desarrollo:"
echo "1. Activa el entorno virtual: source venv/bin/activate"
echo "2. Ejecuta: python app.py" 