import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from parser import decode_serial

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/decode', methods=['GET'])
def api_decode():
    serial = request.args.get('serial', '').strip()
    if not serial:
        return jsonify({"error": "No serial number provided"}), 400
    try:
        decoded = decode_serial(serial)
        return jsonify(decoded)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server on http://localhost:{port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
