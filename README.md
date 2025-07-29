# Python Playwright Scraper WebApp

Esta aplicación web permite scrapear todos los libros de https://books.toscrape.com usando Python, Playwright y Flask, y descargar los resultados en un archivo Excel directamente desde el navegador.

## Características
- Interfaz web moderna, bilingüe (español/inglés)
- Scraping rápido y eficiente usando multiprocessing y Playwright
- Descarga automática del archivo Excel generado, sin guardar archivos en el servidor
- Muestra el número de libros scrapeados y el tiempo total

---

## Requisitos
- Python 3.8+
- pip
- (Linux) Xvfb si quieres ejecutar Playwright en modo no-headless en un servidor sin entorno gráfico

---

## Instalación

1. **Clona el repositorio o descarga los archivos**

2. **Instala las dependencias**

```bash
pip install -r requirements.txt
python -m playwright install
```

3. **(Opcional, solo Linux sin entorno gráfico)**

Si tu servidor no tiene entorno gráfico, instala Xvfb:
```bash
sudo apt install xvfb
```
Y ejecuta la app con:
```bash
xvfb-run python app.py
```

---

## Uso local

1. Ejecuta el backend Flask:

```bash
python app.py
```

2. Abre tu navegador en:
```
http://127.0.0.1:5000/
```

3. Haz clic en "Ejecutar Script" / "Run Script". El scraping comenzará y, al finalizar, el archivo Excel se descargará automáticamente. Verás el número de libros y el tiempo empleado.

---

## Despliegue en producción

1. **Sube los archivos a tu servidor (VPS, cloud, etc.)**
2. **Instala las dependencias y navegadores como arriba**
3. **Usa un servidor de aplicaciones como gunicorn o waitress**

Ejemplo con gunicorn:
```bash
pip install gunicorn
python -m playwright install
# (opcional) Xvfb para headless en servidores Linux
xvfb-run gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

4. **(Opcional) Configura nginx como proxy inverso para servir en el puerto 80/443**

---

## Notas y recomendaciones
- El scraping abre navegadores reales, por lo que puede consumir recursos. Ajusta el número de procesos en `scraper.py` si tu servidor es limitado.
- El archivo Excel nunca se guarda en el servidor, solo se envía al usuario.
- Puedes cambiar la URL objetivo o los campos scrapeados editando `scraper.py`.
- Si tienes problemas con Playwright en servidores Linux, asegúrate de instalar todas las dependencias recomendadas por Playwright ([ver docs](https://playwright.dev/python/docs/installation)).

---

## Créditos
- [books.toscrape.com](https://books.toscrape.com) (sitio de prueba para scraping)
- Playwright, Flask, pandas

---

¡Disfruta tu scraper web automatizado! 🚀 