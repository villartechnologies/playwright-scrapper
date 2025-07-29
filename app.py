from flask import Flask, send_file, jsonify, request, send_from_directory
import subprocess
import os
import json
import threading
import time
import pandas as pd
from io import BytesIO
from config import config

app = Flask(__name__)

# Configuración basada en el entorno
config_name = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[config_name])

# Variable global para controlar ejecución
script_running = False
script_lock = threading.Lock()

# Variables para almacenar datos del Excel en memoria
app.excel_data = None
app.excel_filename = None

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
        
        print(f"Scraper stdout: {result.stdout}")
        print(f"Scraper stderr: {result.stderr}")
        
        books, elapsed, books_data = 0, 0, []
        for line in result.stdout.splitlines():
            if line.strip().startswith('{') and 'books' in line:
                try:
                    stats = json.loads(line.strip())
                    books = stats.get('books', 0)
                    elapsed = stats.get('time', 0)
                    books_data = stats.get('data', [])
                    print(f"Parsed result: books={books}, elapsed={elapsed}, data_length={len(books_data)}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}, line: {line}")
        
        # Generate Excel in memory
        if books_data:
            print(f"Generating Excel with {len(books_data)} books")
            df = pd.DataFrame(books_data)
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            # Store in memory for download
            app.excel_data = excel_buffer.getvalue()
            app.excel_filename = f'books_{int(time.time())}.xlsx'
            print(f"Excel file generated: {app.excel_filename}")
        else:
            print("No books data to generate Excel")
        
        return jsonify({'status': 'ok', 'books': books, 'time': elapsed, 'has_file': bool(books_data)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        script_running = False

@app.route('/download')
def download():
    if hasattr(app, 'excel_data') and app.excel_data:
        return send_file(
            BytesIO(app.excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=app.excel_filename
        )
    else:
        return jsonify({'error': 'No file available'}), 404

@app.route('/file-status')
def file_status():
    has_file = hasattr(app, 'excel_data') and app.excel_data is not None
    return jsonify({
        'has_file': has_file,
        'filename': app.excel_filename if has_file else None
    })

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

if __name__ == '__main__':
    app.run(debug=True) 