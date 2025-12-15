from flask import Flask, render_template, jsonify
from flask import Flask, jsonify, request
import sqlite3
import os
import json

app = Flask(__name__)

@app.route('/api/medicamentos')
def api_meds():
    try:
        conn = get_db()
        data = conn.execute("SELECT * FROM medicamentos ORDER BY category, name").fetchall()
        conn.close()
        return jsonify([dict(row) for row in data])
    except:
        return jsonify([])

@app.route('/api/protocolos')
def get_protocolos():
    conn = sqlite3.connect('farmacia_clinica.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM protocolos")
    protocolos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(protocolos)


DB_NAME = 'farmacia_clinica.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
@app.route('/')
def index():
    return render_template('index.html')

if not os.path.exists('templates'): os.makedirs('templates')