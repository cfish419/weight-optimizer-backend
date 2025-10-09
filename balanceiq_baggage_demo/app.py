from flask import Flask, render_template, redirect, send_from_directory, jsonify
import os
import requests
from config import Config

app = Flask(__name__, static_folder='assets', template_folder='templates')
app.config.from_object(Config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/supervisor')
def supervisor():
    return render_template('supervisor.html')

# Helpful redirects if someone types the .html filenames
@app.route('/index.html')
def index_html():
    return redirect('/', code=301)

@app.route('/supervisor.html')
def supervisor_html():
    return redirect('/supervisor', code=301)

# Serve assets from /assets/*
@app.route('/assets/<path:path>')
def assets(path):
    return send_from_directory('assets', path)

@app.route('/api/proxy/<path:path>')
def api_proxy(path):
    """Proxy API calls to backend"""
    try:
        backend_url = Config.get_api_endpoint(path)
        response = requests.get(backend_url, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": "Backend unavailable", "details": str(e)}), 503

if __name__ == '__main__':
    print(f"Frontend starting on port 5050")
    print(f"Backend API URL: {Config.BACKEND_API_URL}")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5050)