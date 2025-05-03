from flask import Flask, send_file, render_template, request, redirect
import qrcode
import socket
import os
import threading
import requests
from pathlib import Path

app = Flask(__name__)

# Configuration
DOWNLOAD_DIR = 'public'  # Directory to save downloaded files
PORT = 3000 
REMOTE_FILE_URL = 'https://drive.google.com/uc?export=download&id=1bcJMU44rpubCakeaIhkggISvUBDK-HQ2' # Decryption link

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '192.168.56.1'
    finally:
        s.close()
    return ip

@app.route('/')
def control_panel():
    current_url = REMOTE_FILE_URL if REMOTE_FILE_URL else "Not set"
    return render_template('index.html', current_url=current_url)

@app.route('/set-url', methods=['POST'])
def set_url():
    global REMOTE_FILE_URL
    REMOTE_FILE_URL = request.form['file_url']
    return redirect('/')

@app.route('/qrcode')
def serve_qr_code():
    url = f"http://{get_local_ip()}:{PORT}/trigger-download"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    if not os.path.exists('static'):
        os.makedirs('static')
    img.save('static/qrcode.png')
    return send_file('static/qrcode.png', mimetype='image/png')

@app.route('/trigger-download')
def trigger_download():
    if not REMOTE_FILE_URL:
        return "Error: No download URL set. Please set a URL first."
    
    threading.Thread(target=download_file_to_laptop).start()
    return "Download triggered on laptop!"

def download_file_to_laptop():
    try:
        Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
        filename = "downloaded_file.pdf"  # Force PDF extension
        save_path = os.path.join(DOWNLOAD_DIR, filename)
        
        print(f"Downloading PDF from {REMOTE_FILE_URL}...")
        response = requests.get(REMOTE_FILE_URL, stream=True)
        response.raise_for_status()  # Check for HTTP errors
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"PDF saved as {save_path}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def get_local_ip():
    # In production, return the host domain
    return os.environ.get('PYTHONANYWHERE_DOMAIN', '127.0.0.1')

def run_server():
    # This function is only used when running locally
    ip = get_local_ip()
    print(f"Access the control panel at: http://{ip}:{PORT}")
    app.run(host=ip, port=PORT, debug=False)  # Set debug to False in production
    
if __name__ == '__main__':
    run_server()
