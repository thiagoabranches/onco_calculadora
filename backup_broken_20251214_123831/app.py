from flask import Flask, render_template, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_NAME = 'farmacia_clinica.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/medicamentos')
def api_meds():
    try:
        conn = get_db()
        data = conn.execute("SELECT * FROM medicamentos ORDER BY category, name").fetchall()
        conn.close()
        return jsonify([dict(row) for row in data])
    except:
        return jsonify([])

if __name__ == '__main__':
    if not os.path.exists('templates'): os.makedirs('templates')
    app.run(debug=True, port=5000)
