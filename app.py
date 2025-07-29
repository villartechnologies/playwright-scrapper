from flask import Flask, send_file, jsonify, request, send_from_directory
import subprocess
import os
from config import config

app = Flask(__name__)

# Configuración basada en el entorno
config_name = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[config_name])

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/progress')
def progress():
    try:
        with open('progress.json', 'r') as f:
            data = f.read()
        return data, 200, {'Content-Type': 'application/json'}
    except Exception:
        return '{"progress": 0}', 200, {'Content-Type': 'application/json'}

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        with open('progress.json', 'w') as f:
            f.write('{"progress": 0}')
        result = subprocess.run(['python3', 'scraper.py'], capture_output=True, text=True, check=True)
        books, elapsed = 0, 0
        import json
        for line in result.stdout.splitlines():
            if line.strip().startswith('{') and 'books' in line:
                stats = json.loads(line.strip())
                books = stats.get('books', 0)
                elapsed = stats.get('time', 0)
        return jsonify({'status': 'ok', 'books': books, 'time': elapsed})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download')
def download():
    return send_file('books.xlsx', as_attachment=True)

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

if __name__ == '__main__':
    app.run(debug=True) 