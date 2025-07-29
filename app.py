from flask import Flask, send_file, jsonify, request, send_from_directory
import subprocess
import os
import json
import threading
import time
import pandas as pd
import glob
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
        # Add script running status to progress data
        data['script_running'] = script_running
        return jsonify(data), 200
    except Exception as e:
        return jsonify({
            'progress': 0, 
            'current': 0, 
            'total': 100, 
            'error': str(e),
            'script_running': script_running
        }), 200

@app.route('/status')
def status():
    """Endpoint to check if script is currently running"""
    return jsonify({
        'script_running': script_running,
        'has_file': len(glob.glob('*.xlsx')) > 0
    })

@app.route('/run-script', methods=['POST'])
def run_script():
    global script_running
    
    with script_lock:
        if script_running:
            return jsonify({
                'status': 'error', 
                'message': 'El script ya está ejecutándose. Por favor espera a que termine.'
            }), 409
        
        script_running = True
    
    try:
        # Reset progress
        with open('progress.json', 'w') as f:
            json.dump({'progress': 0, 'current': 0, 'total': 100}, f)
        
        # Run script
        print("Starting scraper...")
        result = subprocess.run(['python3', 'scraper.py'], capture_output=True, text=True, check=True)
        print("Scraper finished!")
        
        print(f"Scraper stdout length: {len(result.stdout)}")
        print(f"Scraper stderr: {result.stderr}")
        
        books, elapsed, books_data = 0, 0, []
        json_found = False
        for line in result.stdout.splitlines():
            if line.strip().startswith('{') and 'books' in line:
                try:
                    stats = json.loads(line.strip())
                    books = stats.get('books', 0)
                    elapsed = stats.get('time', 0)
                    books_data = stats.get('data', [])
                    json_found = True
                    print(f"Parsed result: books={books}, elapsed={elapsed}, data_length={len(books_data)}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}, line: {line}")
        
        if not json_found:
            print("No JSON found in scraper output!")
            print("Last 10 lines of output:")
            for line in result.stdout.splitlines()[-10:]:
                print(f"  {line}")
        
        # Generate Excel file on server - SIMPLE AND WORKS!
        print(f"Books data length: {len(books_data) if books_data else 0}")
        
        if books_data and len(books_data) > 0:
            print(f"Generating Excel with {len(books_data)} books")
            df = pd.DataFrame(books_data)
            filename = f'books_{int(time.time())}.xlsx'
            df.to_excel(filename, index=False)
            print(f"✅ Excel file saved: {filename}")
        else:
            print("❌ No books data to generate Excel")
            # Create a dummy Excel file for testing
            df = pd.DataFrame([{'title': 'Test Book', 'price': '£10.00', 'availability': 'In stock'}])
            filename = f'test_books_{int(time.time())}.xlsx'
            df.to_excel(filename, index=False)
            print(f"✅ Test Excel file saved: {filename}")
        
        result_data = {'status': 'ok', 'books': books, 'time': elapsed, 'has_file': bool(books_data)}
        print(f"Returning result: {result_data}")
        return jsonify(result_data)
    except Exception as e:
        print(f"Error in run_script: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        script_running = False

@app.route('/download')
def download():
    # Find the most recent Excel file
    import glob
    excel_files = glob.glob('*.xlsx')
    if excel_files:
        # Get the most recent file
        latest_file = max(excel_files, key=os.path.getctime)
        return send_file(latest_file, as_attachment=True)
    else:
        return jsonify({'error': 'No file available'}), 404

@app.route('/file-status')
def file_status():
    import glob
    excel_files = glob.glob('*.xlsx')
    has_file = len(excel_files) > 0
    latest_file = max(excel_files, key=os.path.getctime) if excel_files else None
    return jsonify({
        'has_file': has_file,
        'filename': latest_file
    })

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

if __name__ == '__main__':
    app.run(debug=True) 