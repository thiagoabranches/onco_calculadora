from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('farmacia_clinica.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/medicamentos')
def api_medicamentos():
    conn = get_db_connection()
    medicamentos = conn.execute('SELECT * FROM medicamentos').fetchall()
    conn.close()
    return jsonify([dict(row) for row in medicamentos])

if __name__ == '__main__':
    app.run(debug=True, port=5000)