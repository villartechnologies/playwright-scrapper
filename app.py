from flask import Flask, send_file, jsonify, request, send_from_directory
import subprocess
import os
import json
import threading
from config import config

app = Flask(__name__)

# Configuración basada en el entorno
config_name = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[config_name])

# Variable global para controlar ejecución
script_running = False
script_lock = threading.Lock()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/progress')
def progress():
    try:
        with open('progress.json', 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'progress': 0, 'current': 0, 'total': 100, 'error': str(e)}), 200

@app.route('/run-script', methods=['POST'])
def run_script():
    global script_running
    
    with script_lock:
        if script_running:
            return jsonify({'status': 'error', 'message': 'Script already running'}), 409
        
        script_running = True
    
    try:
        # Reset progress
        with open('progress.json', 'w') as f:
            json.dump({'progress': 0, 'current': 0, 'total': 100}, f)
        
        # Run script
        result = subprocess.run(['python3', 'scraper.py'], capture_output=True, text=True, check=True)
        
        books, elapsed = 0, 0
        for line in result.stdout.splitlines():
            if line.strip().startswith('{') and 'books' in line:
                stats = json.loads(line.strip())
                books = stats.get('books', 0)
                elapsed = stats.get('time', 0)
        
        return jsonify({'status': 'ok', 'books': books, 'time': elapsed})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        script_running = False

@app.route('/download')
def download():
    return send_file('books.xlsx', as_attachment=True)

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

if __name__ == '__main__':
    app.run(debug=True) 