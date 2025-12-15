from flask import Flask, render_template, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_NAME = 'farmacia_clinica.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return "<h1>Painel Administrativo</h1><p>Funcionalidade em desenvolvimento.</p><a href='/'>Voltar</a>"

@app.route('/api/medicamentos')
def get_medicamentos():
    try:
        conn = get_db_connection()
        medicamentos = conn.execute('SELECT * FROM medicamentos ORDER BY name').fetchall()
        conn.close()
        return jsonify([dict(row) for row in medicamentos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    print("Servidor rodando em http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
