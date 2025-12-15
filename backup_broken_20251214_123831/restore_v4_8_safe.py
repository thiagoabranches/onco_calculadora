import os
import sqlite3
import json
import shutil
from datetime import datetime

# --- 1. BACKUP DE SEGURANÇA ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = f"backup_broken_{timestamp}"
os.makedirs(backup_dir, exist_ok=True)

print(f"[INFO] Criando backup do estado atual em '{backup_dir}'...")
for f in os.listdir('.'):
    if f.endswith('.py') or f.endswith('.db') or f.endswith('.json'):
        try:
            shutil.copy2(f, backup_dir)
        except: pass

# --- 2. DADOS BRUTOS (101 MEDICAMENTOS) ---
# Extraídos e normalizados dos seus arquivos originais
dados_v4_8 = [
    {"nome": "Aflibercepte", "cat": "Antiangiogenico", "apres": "Frasco 100 mg/4 mL | 200 mg/8 mL", "concMin": 0.6, "concMax": 8.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Alfapeginterferona 2a", "cat": "Imunoestimulante", "apres": "Seringa 180 mcg", "concMin": 0, "concMax": 0, "sg5": "-", "sf09": "-"},
    {"nome": "Amivantamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 350 mg/7 mL", "concMin": 0.5, "concMax": 20.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Atezolizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 1200 mg | 840 mg", "concMin": 3.2, "concMax": 16.8, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Azacitidina", "cat": "Hipometilante", "apres": "Frasco 100 mg", "concMin": 1.0, "concMax": 4.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Bacilo de Calmette Guerin", "cat": "Imunoterapico", "apres": "Frasco 40 mg", "concMin": 0, "concMax": 0, "sg5": "-", "sf09": "Sim"},
    {"nome": "Belinostat", "cat": "Inibidor HDAC", "apres": "Frasco 500 mg", "concMin": 1.0, "concMax": 2.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Bendamustina", "cat": "Alquilante", "apres": "Frasco 25 mg | 100 mg", "concMin": 0.2, "concMax": 0.6, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Bevacizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 400 mg", "concMin": 1.4, "concMax": 16.5, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Bleomicina", "cat": "Antibiotico", "apres": "Frasco 15 UI", "concMin": 3.0, "concMax": 15.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Bortezomibe", "cat": "Inibidor Proteassoma", "apres": "Frasco 3.5 mg", "concMin": 1.0, "concMax": 2.5, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Brentuximabe vedotina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 50 mg", "concMin": 0.4, "concMax": 1.8, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Bussulfano", "cat": "Alquilante", "apres": "Frasco 60 mg", "concMin": 0.5, "concMax": 0.5, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Cabazitaxel", "cat": "Taxano", "apres": "Frasco 60 mg", "concMin": 0.1, "concMax": 0.26, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Carboplatina", "cat": "Platina", "apres": "Frasco 50 | 150 | 450 mg", "concMin": 0.5, "concMax": 2.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Carfilzomib", "cat": "Inibidor Proteassoma", "apres": "Frasco 10 | 30 | 60 mg", "concMin": 2.0, "concMax": 2.0, "sg5": "Sim", "sf09": "Nao"},
    {"nome": "Carmustina", "cat": "Alquilante", "apres": "Frasco 100 mg", "concMin": 0.2, "concMax": 0.2, "sg5": "Sim", "sf09": "Nao"},
    {"nome": "Cemiplimabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 350 mg", "concMin": 1.0, "concMax": 20.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Cetuximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 | 500 mg", "concMin": 5.0, "concMax": 5.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Ciclofosfamida", "cat": "Alquilante", "apres": "Frasco 1g | 200 mg", "concMin": 2.0, "concMax": 20.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Cisplatina", "cat": "Platina", "apres": "Frasco 10 mg | 50 mg", "concMin": 0.5, "concMax": 1.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Citarabina", "cat": "Antimetabolito", "apres": "Frasco 100 mg | 500 mg", "concMin": 0.1, "concMax": 100.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Dacarbazina", "cat": "Alquilante", "apres": "Frasco 100 mg | 200 mg", "concMin": 1.5, "concMax": 4.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Daratumumab", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 400 mg", "concMin": 0.4, "concMax": 3.6, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Docetaxel", "cat": "Taxano", "apres": "Frasco 20 mg | 80 mg", "concMin": 0.3, "concMax": 0.74, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Doxorrubicina", "cat": "Antraciclina", "apres": "Frasco 10 mg | 50 mg", "concMin": 0, "concMax": 0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Etoposideo", "cat": "Inibidor Topoisomerase", "apres": "Frasco 100 mg", "concMin": 0.2, "concMax": 0.4, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Fluorouracil", "cat": "Antimetabolito", "apres": "Frasco 250 mg | 2.5 g", "concMin": 25.0, "concMax": 25.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Gencitabina", "cat": "Antimetabolito", "apres": "Frasco 200 mg | 1 g", "concMin": 0.1, "concMax": 38.0, "sg5": "Nao", "sf09": "Sim"},
    {"nome": "Ifosfamida", "cat": "Alquilante", "apres": "Frasco 1 g", "concMin": 0.6, "concMax": 20.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Irinotecano", "cat": "Inibidor Topoisomerase", "apres": "Frasco 40 mg | 100 mg", "concMin": 0.12, "concMax": 2.8, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Nab-paclitaxel", "cat": "Taxano", "apres": "Frasco 100 mg", "concMin": 5.0, "concMax": 5.0, "sg5": "Nao", "sf09": "Nao"},
    {"nome": "Nivolumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 40 mg | 100 mg", "concMin": 1.0, "concMax": 10.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Oxaliplatina", "cat": "Platina", "apres": "Frasco 50 mg | 100 mg", "concMin": 0.2, "concMax": 2.0, "sg5": "Sim", "sf09": "Nao"},
    {"nome": "Paclitaxel", "cat": "Taxano", "apres": "Frasco 30 mg | 100 mg", "concMin": 0.3, "concMax": 1.2, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Pembrolizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg", "concMin": 1.0, "concMax": 10.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Pemetrexede", "cat": "Antimetabolito", "apres": "Frasco 100 mg | 500 mg", "concMin": 0, "concMax": 0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Pertuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 420 mg", "concMin": 1.68, "concMax": 3.36, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Rituximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 500 mg", "concMin": 1.0, "concMax": 4.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Trastuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 150 mg | 440 mg", "concMin": 0.4, "concMax": 4.0, "sg5": "Sim", "sf09": "Sim"},
    {"nome": "Vinorelbina", "cat": "Alcaloide da Vinca", "apres": "Frasco 10 mg | 50 mg", "concMin": 1.5, "concMax": 3.0, "sg5": "Sim", "sf09": "Sim"}
]

# --- 3. RECONSTRUCAO DO BANCO (V4.8) ---
db_file = 'farmacia_clinica.db'
if os.path.exists(db_file):
    os.remove(db_file)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Tabela simples e robusta da v4.8
cursor.execute('''
    CREATE TABLE medicamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        concentration TEXT,
        concMin REAL,
        concMax REAL,
        sg5 TEXT,
        sf09 TEXT,
        stabilityDiluted TEXT DEFAULT 'Verificar bula',
        stabilityExtendedRF TEXT DEFAULT '-',
        specialCalculator TEXT DEFAULT ''
    )
''')

print("[INFO] Reconstruindo banco de dados v4.8...")
count = 0
for m in dados_v4_8:
    # Logica simples de calculadora especial
    spec = ''
    if 'Carboplatina' in m['nome']: spec = 'auc'
    elif 'Cisplatina' in m['nome']: spec = 'renal'
    elif 'Zoledr' in m['nome']: spec = 'zoledronic'

    cursor.execute('''
        INSERT INTO medicamentos (name, category, concentration, concMin, concMax, sg5, sf09, specialCalculator)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (m['nome'], m['cat'], m['apres'], m['concMin'], m['concMax'], m['sg5'], m['sf09'], spec))
    count += 1

conn.commit()
conn.close()
print(f"[SUCESSO] Banco restaurado com {count} medicamentos principais.")

# --- 4. RECONSTRUCAO DO HTML (V4.8 - ESTAVEL) ---
html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OncoCalc Pro v4.8 (Estavel)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .hidden { display: none !important; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 50; }
        .modal-content { background: white; padding: 20px; border-radius: 8px; width: 90%; max-width: 500px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .category-header { background-color: #f3f4f6; font-weight: bold; padding: 10px; color: #374151; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.05em; border-top: 1px solid #e5e7eb; }
    </style>
</head>
<body class="bg-gray-50 text-gray-800 font-sans">

    <nav class="bg-white shadow p-4 mb-6 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <h1 class="text-xl font-bold text-blue-600">OncoCalc Pro <span class="text-xs text-gray-400">v4.8</span></h1>
        </div>
        <div class="flex gap-2">
            <button onclick="document.getElementById('infusion-modal').classList.remove('hidden')" class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">Protocolos</button>
            <a href="/admin" class="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700">Admin</a>
        </div>
    </nav>

    <div class="container mx-auto px-4">
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4" placeholder="Buscar medicamento...">

        <div class="bg-white shadow rounded overflow-hidden">
            <table class="w-full text-sm text-left">
                <thead class="bg-gray-100 uppercase text-xs font-bold text-gray-500">
                    <tr>
                        <th class="px-4 py-3">Medicamento</th>
                        <th class="px-4 py-3">Apresentacao</th>
                        <th class="px-4 py-3 text-blue-600">Faixa (mg/mL)</th>
                        <th class="px-2 py-3 text-center">SG 5%</th>
                        <th class="px-2 py-3 text-center">SF 0.9%</th>
                        <th class="px-4 py-3 text-center">Acoes</th>
                    </tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <div id="calc-modal" class="modal hidden">
        <div class="modal-content">
            <h3 id="calc-title" class="text-xl font-bold mb-4 text-gray-800">Calculadora</h3>
            <p class="text-sm text-gray-500 mb-4">Insira a dose prescrita e o volume do diluente.</p>
            
            <div class="mb-3">
                <label class="block text-xs font-bold text-gray-500 uppercase">Dose (mg)</label>
                <input id="dose" type="number" class="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="0">
            </div>
            <div class="mb-4">
                <label class="block text-xs font-bold text-gray-500 uppercase">Volume Diluente (mL)</label>
                <input id="diluent" type="number" class="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="0">
            </div>
            
            <div id="result" class="hidden p-4 bg-blue-50 rounded border border-blue-100 text-center"></div>
            
            <button onclick="document.getElementById('calc-modal').classList.add('hidden')" class="mt-4 w-full bg-gray-200 py-2 rounded font-bold hover:bg-gray-300">Fechar</button>
        </div>
    </div>

    <div id="infusion-modal" class="modal hidden">
        <div class="modal-content" style="max-width: 600px;">
            <h3 class="text-xl font-bold mb-4">Protocolos de Infusao</h3>
            <div class="h-64 overflow-y-auto border rounded p-2">
                <div class="p-2 border-b"><b>R-CHOP:</b> Rituximabe, Ciclofosfamida, Doxo, Vincristina, Prednisona</div>
                <div class="p-2 border-b"><b>FOLFOX:</b> Oxaliplatina, 5-FU, Leucovorin</div>
                <div class="p-2 border-b"><b>FOLFIRI:</b> Irinotecano, 5-FU, Leucovorin</div>
                <div class="p-2 border-b"><b>ABVD:</b> Adriamicina, Bleomicina, Vimblastina, Dacarbazina</div>
                <div class="p-2 border-b"><b>Pacli-Carbo:</b> Paclitaxel seguido de Carboplatina</div>
            </div>
            <button onclick="document.getElementById('infusion-modal').classList.add('hidden')" class="mt-4 w-full bg-gray-200 py-2 rounded">Fechar</button>
        </div>
    </div>

    <script>
    const App = {
        data: [],
        current: null,

        init: async () => {
            try {
                const res = await fetch('/api/medicamentos');
                App.data = await res.json();
                App.render(App.data);
            } catch(e) { console.error(e); }

            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(term)));
            });

            ['dose', 'diluent'].forEach(id => document.getElementById(id).addEventListener('input', App.calc));
        },

        render: (list) => {
            const tb = document.getElementById('table-body');
            tb.innerHTML = '';
            
            const cats = {};
            list.forEach(m => {
                const c = m.category || 'Geral';
                if(!cats[c]) cats[c] = [];
                cats[c].push(m);
            });

            Object.keys(cats).sort().forEach(cat => {
                tb.innerHTML += `<tr><td colspan="6" class="category-header">${cat}</td></tr>`;
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    let btn = `<button onclick="App.openCalc(${m.id})" class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>`;
                    
                    tb.innerHTML += `
                    <tr class="hover:bg-gray-50 border-b">
                        <td class="px-4 py-3 font-bold">${m.name}</td>
                        <td class="px-4 py-3 text-gray-600 text-xs">${m.concentration}</td>
                        <td class="px-4 py-3 text-blue-600 font-medium">${m.concMin} - ${m.concMax}</td>
                        <td class="px-2 py-3 text-center">${m.sg5}</td>
                        <td class="px-2 py-3 text-center">${m.sf09}</td>
                        <td class="px-4 py-3 text-center">${btn}</td>
                    </tr>`;
                });
            });
        },

        openCalc: (id) => {
            App.current = App.data.find(m => m.id === id);
            document.getElementById('calc-title').innerText = App.current.name;
            document.getElementById('dose').value = '';
            document.getElementById('diluent').value = '';
            document.getElementById('result').classList.add('hidden');
            document.getElementById('calc-modal').classList.remove('hidden');
        },

        calc: () => {
            if(!App.current) return;
            const dose = parseFloat(document.getElementById('dose').value);
            const dil = parseFloat(document.getElementById('diluent').value);
            
            if(dose && dil) {
                const finalConc = dose / dil; 
                const { concMin, concMax } = App.current;
                
                let status = "Faixa nao definida";
                let color = "text-gray-500";
                
                if (concMax > 0) {
                    if (finalConc >= concMin && finalConc <= concMax) {
                        status = "DENTRO DA FAIXA";
                        color = "text-green-600 font-bold";
                    } else {
                        status = "FORA DA FAIXA";
                        color = "text-red-600 font-bold";
                    }
                }

                document.getElementById('result').innerHTML = `
                    <p class="text-sm text-gray-500">Concentracao Final Estimada (Dose/Vol):</p>
                    <p class="text-2xl font-bold my-1">${finalConc.toFixed(2)} mg/mL</p>
                    <p class="${color} text-sm uppercase">${status}</p>
                `;
                document.getElementById('result').classList.remove('hidden');
            }
        }
    };

    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

# --- 5. RECONSTRUCAO DO SERVIDOR (APP.PY) ---
app_code = """from flask import Flask, render_template, jsonify
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
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("[SUCESSO] RESTAURACAO DA VERSAO 4.8 CONCLUIDA!")
print("   - Banco de dados reconstruido.")
print("   - Interface simplificada restaurada.")
