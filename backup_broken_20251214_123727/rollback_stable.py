import os

# 1. RESTAURA O SERVIDOR (APP.PY) SIMPLES E FUNCIONAL
app_code = """from flask import Flask, render_template, jsonify
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
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

# 2. RESTAURA O HTML DA VERSÃO ESTÁVEL (TABELA LIMPA + BOTÃO CALC SIMPLES)
html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OncoCalc Pro - Estável</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 50; }
        .modal-content { background: white; padding: 20px; border-radius: 8px; max-width: 500px; width: 90%; }
        .hidden { display: none; }
        
        /* Menu Contexto Simples */
        #context-menu { position: absolute; background: white; border: 1px solid #ccc; z-index: 1000; display: none; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); min-width: 200px; }
        .ctx-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee; }
        .ctx-item:hover { background-color: #f0f0f0; color: #000; }
        .ctx-header { background: #e2e8f0; padding: 5px 10px; font-weight: bold; font-size: 0.8em; }
        
        .category-header { background-color: #f1f5f9; font-weight: bold; padding: 10px; text-transform: uppercase; font-size: 0.8em; color: #475569; }
    </style>
</head>
<body class="bg-gray-50 text-gray-800" onclick="document.getElementById('context-menu').style.display='none'">

    <nav class="bg-white shadow p-4 mb-6 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-600">OncoCalc Pro <span class="text-xs text-gray-400">v5.0 Stable</span></h1>
        <a href="/admin" class="bg-gray-200 px-3 py-1 rounded text-sm hover:bg-gray-300">Admin</a>
    </nav>

    <div class="container mx-auto px-4">
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4" placeholder="Buscar medicamento...">

        <div class="bg-white shadow rounded overflow-hidden">
            <table class="w-full text-sm text-left">
                <thead class="bg-gray-100 uppercase text-xs">
                    <tr>
                        <th class="px-4 py-3">Medicamento</th>
                        <th class="px-4 py-3">Apresentação</th>
                        <th class="px-4 py-3 text-blue-600">Faixa (mg/mL)</th>
                        <th class="px-4 py-3 text-center">SG 5%</th>
                        <th class="px-4 py-3 text-center">SF 0.9%</th>
                        <th class="px-4 py-3">Estabilidade</th>
                        <th class="px-4 py-3 text-center">Ações</th>
                    </tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <div id="context-menu"></div>

    <div id="calc-modal" class="modal">
        <div class="modal-content">
            <h3 id="calc-title" class="text-xl font-bold mb-4">Calculadora</h3>
            <p class="text-sm text-gray-500 mb-2">Apresentação Base: <span id="calc-base-conc" class="font-bold"></span></p>
            
            <label class="block text-xs font-bold mt-2">DOSE (mg)</label>
            <input id="dose" type="number" class="w-full p-2 border rounded mb-2">
            
            <label class="block text-xs font-bold mt-2">DILUENTE (mL)</label>
            <input id="diluent" type="number" class="w-full p-2 border rounded mb-4">
            
            <div id="result" class="hidden p-3 bg-blue-50 text-center rounded border border-blue-200"></div>
            
            <button onclick="document.getElementById('calc-modal').style.display='none'" class="mt-4 w-full bg-gray-200 py-2 rounded">Fechar</button>
        </div>
    </div>

    <script>
    const App = {
        data: [],
        current: null,

        init: async () => {
            try {
                const res = await fetch('/api/medicamentos');
                if(res.ok) {
                    App.data = await res.json();
                    App.render(App.data);
                }
            } catch(e) { console.error(e); }

            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(term)));
            });

            ['dose', 'diluent'].forEach(id => document.getElementById(id).addEventListener('input', App.calc));
        },

        render: (list) => {
            const tb = document.getElementById('table-body'); tb.innerHTML = '';
            
            // Agrupar
            const cats = {};
            list.forEach(m => {
                let c = m.category || 'Geral';
                if(!cats[c]) cats[c] = [];
                cats[c].push(m);
            });

            Object.keys(cats).sort().forEach(cat => {
                tb.innerHTML += `<tr><td colspan="7" class="category-header">${cat}</td></tr>`;
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    
                    // Lógica Visual Simples (Módulo 1)
                    let multiIcon = (m.has_multiple_presentations === 1) ? '📚' : '';
                    let ctxEvent = (m.has_multiple_presentations === 1) ? `oncontextmenu="App.ctx(event, ${m.id}); return false;"` : '';
                    let cursor = (m.has_multiple_presentations === 1) ? 'cursor-context-menu' : '';

                    let row = `
                    <tr class="hover:bg-gray-50 border-b">
                        <td class="px-4 py-3 font-bold ${cursor}" ${ctxEvent}>${m.name} ${multiIcon}</td>
                        <td class="px-4 py-3 text-gray-600">${m.concentration_display || '-'}</td>
                        <td class="px-4 py-3 text-blue-600 font-medium">${m.concMin} - ${m.concMax}</td>
                        <td class="px-4 py-3 text-center">${m.sg5}</td>
                        <td class="px-4 py-3 text-center">${m.sf09}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">${m.stabilityDiluted}</td>
                        <td class="px-4 py-3 text-center">
                            <button onclick="App.openCalc(${m.id})" class="bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                    tb.innerHTML += row;
                });
            });
        },

        openCalc: (id) => {
            App.current = App.data.find(m => m.id === id);
            document.getElementById('calc-title').innerText = App.current.name;
            document.getElementById('calc-base-conc').innerText = App.current.concentration_display;
            document.getElementById('dose').value = '';
            document.getElementById('diluent').value = '';
            document.getElementById('result').classList.add('hidden');
            document.getElementById('calc-modal').style.display = 'flex';
        },

        calc: () => {
            if(!App.current) return;
            const dose = parseFloat(document.getElementById('dose').value);
            const dil = parseFloat(document.getElementById('diluent').value);
            if(!dose || !dil) return;

            // Usa concentração padrao (1 mg/mL se não definido) para cálculo básico
            const conc = App.current.concentracaoPadrao || 1; 
            const vol = dose / conc;
            const finalConc = dose / (vol + dil);
            
            document.getElementById('result').innerHTML = `
                <p class="text-sm">Volume a Aspirar: <b>${vol.toFixed(2)} mL</b></p>
                <p class="text-xs mt-1">Conc. Final: ${finalConc.toFixed(2)} mg/mL</p>
            `;
            document.getElementById('result').classList.remove('hidden');
        },

        ctx: (e, id) => {
            e.preventDefault();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            menu.innerHTML = `<div class="ctx-header">${m.name}</div>`;
            
            try {
                const p = JSON.parse(m.presentations);
                p.forEach(x => {
                    menu.innerHTML += `<div class="ctx-item">${x.brand} - ${x.description}</div>`;
                });
            } catch(err) {
                menu.innerHTML += `<div class="p-2 text-red-500">Erro dados</div>`;
            }
            
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("[ROLLBACK] Sistema restaurado para a versão estável.")
