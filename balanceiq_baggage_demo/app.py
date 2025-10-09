from flask import Flask, render_template, redirect, send_from_directory
import os

app = Flask(__name__, static_folder='assets', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/supervisor')
def supervisor():
    return render_template('supervisor.html')

@app.route('/ramp')  # NEW: Ramp page route
def ramp():
    return render_template('ramp.html')

# Helpful redirects if someone types the .html filenames
@app.route('/index.html')
def index_html():
    return redirect('/', code=301)

@app.route('/supervisor.html')
def supervisor_html():
    return redirect('/supervisor', code=301)

@app.route('/ramp.html')  # NEW: Redirect to /ramp
def ramp_html():
    return redirect('/ramp', code=301)

# Serve assets from /assets/*
@app.route('/assets/<path:path>')
def assets(path):
    return send_from_directory('assets', path)

if __name__ == '__main__':
    # Change port=5050 if you want a different port
    app.run(debug=True, host='0.0.0.0', port=5050)
