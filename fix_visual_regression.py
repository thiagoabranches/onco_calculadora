import sqlite3
import os
import re

# --- 1. DADOS DE BLINDAGEM (NOMES COMERCIAIS) ---
marcas_fixas = {
    "aflibercepte": "Zaltrap® Sanofi",
    "alfapeginterferona 2a": "Pegasys® Roche",
    "amivantamabe": "Rybrevant® Jansen Cilag",
    "atezolizumabe": "Tecentriq® Roche",
    "avelumabe": "Bavencio® Merck",
    "azacitidina": "Vidaza® United Medical | Winduza® Dr. Reddys",
    "bacilo de calmette guerin": "Urohipe® Uno Health Care",
    "belinostat": "Beleodaq® Pint Pharma",
    "bendamustina": "Ribomustin® Janssen-Cilag | Benalq® Jan",
    "betadinutuximabe": "Qarziba® Global",
    "bevacizumabe": "Avastin® Roche",
    "bleomicina": "Bonar® Biossintética | Bleomycin® Fresenius Kabi",
    "blinatumomabe": "Blincyto® Amgen",
    "bortezomibe": "Mielocade® Bergamo | Velcade® Janssen",
    "brentuximabe vedotina": "Adcetris® Takeda",
    "bussulfano": "Busilvex® Pierre Fabre",
    "cabazitaxel": "Jevtana® Sanofi | Caab® Accord",
    "carboplatina": "Fauldcarbo® Libbs | B-Platin® Blau",
    "carfilzomib": "Kyprolis® Amgen",
    "carmustina": "Bicnu® Emcure | Nibisnu® Dr. Reddys",
    "cemiplimabe": "Libtayo® Sanofi",
    "cetuximabe": "Erbitux® Merck",
    "ciclofosfamida": "Genuxal® Baxter",
    "cidofovir": "Vistide® Pharmacia Brasil",
    "cisplatina": "Faulcispla® Libbs",
    "citarabina": "Fauldcita® Libbs",
    "cladribina": "Leustatin® Janssen Cilag",
    "dacarbazina": "Fauldacar® Libbs | Dacarb® Eurofarma",
    "dactinomicina": "Dacilon® Celon Labs",
    "daratumumab": "Dalinvi® Janssen Cilag",
    "daunorrubicina": "Evoclass® Farmarin",
    "decitabina": "Dacogen® Janssen Cilag",
    "docetaxel": "Taxotere® Sanofi | Docetaxel® Accord",
    "dostarlimabe": "Jemperli® GSK",
    "doxorrubicina": "Rubidox® Bergamo | Fauldoxo® Libbs",
    "doxorrubicina lipossomal": "Doxopeg® Zodiac",
    "durvalumabe": "Imfinzi® AstraZeneca",
    "elotuzumabe": "Empliciti® Bristol-Myers",
    "elranatamabe": "Elrexfio® Pfizer",
    "enfortumabe vedotina": "Padcev® Zodiac",
    "epcoritamabe": "Epkinly® Abbvie",
    "epirrubicina": "Brecila® Accord | Farmorubicina® Pfizer",
    "eribulina": "Halaven® United Medical",
    "etoposideo": "Epósido® Blau | Evoposdo® Farmarin",
    "fludarabina": "Fludalibbs® Libbs",
    "fluorouracil": "Fauldfluor® Libbs | Flusan® Eurofarma",
    "foscarnet": "Sol. Foscavir® Clinigen",
    "fotemustine": "Muphoran® Servier",
    "ganciclovir": "Cymevene® Roche | Ganciclotrat® União Quimica"
}

def normalize(text):
    if not text: return ""
    text = re.sub(r'\s*\(.*?\)', '', text)
    text = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    text = text.replace('etoposideo', 'etoposide').replace('etoposide', 'etoposideo')
    return text

def fix_backend():
    print("--- 1. RESTAURANDO BACKEND (SEM TOCAR COLUNAS TRAVADAS) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # Garante coluna brand_name
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN brand_name TEXT DEFAULT '-'")
    except: pass

    # Aplica nomes comerciais (cirúrgico)
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    count = 0
    for r in rows:
        key = normalize(r[1])
        for k_dict, v_dict in marcas_fixas.items():
            if normalize(k_dict) in key or key in normalize(k_dict):
                cursor.execute("UPDATE medicamentos SET brand_name = ? WHERE id = ?", (v_dict, r[0]))
                count += 1
                break
    conn.commit()
    conn.close()
    print(f"   Backend: {count} marcas vinculadas. Outras colunas INTACTAS.")

def fix_frontend():
    print("--- 2. RESTAURANDO FRONTEND (VISUAL COMPLETO) ---")
    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Restaurado</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .hidden { display: none !important; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px; text-transform: uppercase; font-size: 0.8rem; color: #475569; border-top: 1px solid #cbd5e1; }
        /* Cores de status */
        .safe { color: #059669; font-weight: 600; }
        .alert { color: #dc2626; font-weight: 600; }
        .brand { color: #047857; font-size: 0.85rem; font-weight: 600; }
        /* Menu */
        #context-menu { position: absolute; z-index: 50; display: none; background: white; border: 1px solid #ccc; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 6px; min-width: 200px; }
        .ctx-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f0f0f0; font-size: 0.9em; }
        .ctx-item:hover { background-color: #eff6ff; }
    </style>
</head>
<body onclick="document.getElementById('context-menu').style.display='none'">

    <nav class="bg-white shadow p-4 mb-6 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <span class="text-2xl">💊</span>
            <h1 class="text-xl font-bold text-slate-800">OncoCalc Pro <span class="text-xs text-slate-400">Módulo 1 + Travas</span></h1>
        </div>
        <button onclick="alert('Funcionalidade em desenvolvimento')" class="text-sm bg-slate-100 px-3 py-1 rounded">Admin</button>
    </nav>

    <div class="container mx-auto px-4 max-w-full">
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar...">

        <div class="bg-white shadow rounded overflow-hidden overflow-x-auto">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 uppercase text-xs font-bold text-slate-500 border-b">
                    <tr>
                        <th class="px-4 py-3 w-1/5">Nome Comercial</th> <th class="px-4 py-3 w-1/5">Medicamento</th>
                        <th class="px-4 py-3 w-1/5">Apresentação</th>
                        <th class="px-4 py-3 text-blue-600">Faixa (mg/mL)</th> <th class="px-2 py-3 text-center">SG 5%</th> <th class="px-2 py-3 text-center">SF 0.9%</th> <th class="px-4 py-3 text-center">Ações</th> </tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <div id="context-menu"></div>

    <script>
    const App = {
        data: [],
        init: async () => {
            const res = await fetch('/api/medicamentos');
            App.data = await res.json();
            App.render(App.data);
            
            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(term)));
            });
        },
        
        render: (list) => {
            const tb = document.getElementById('table-body'); tb.innerHTML = '';
            const cats = {};
            list.forEach(m => {
                let c = m.category || 'Geral';
                if(!cats[c]) cats[c] = [];
                cats[c].push(m);
            });

            Object.keys(cats).sort().forEach(cat => {
                tb.innerHTML += `<tr><td colspan="7" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    // Logica Motor 1
                    const isMulti = m.has_multiple_presentations === 1;
                    let icon = isMulti ? '<span class="cursor-pointer ml-1 text-blue-500">📚</span>' : '';
                    let ctx = isMulti ? `oncontextmenu="App.ctx(event, ${m.id}); return false;"` : '';
                    
                    // Tratamento Marca (Mostra primeira se houver pipe)
                    let brand = m.brand_name || '-';
                    if(brand.includes('|')) brand = brand.split('|')[0].trim() + '...';
                    if(brand === '-') brand = '<span class="text-slate-300">-</span>';
                    else brand = `<span class="brand">${brand}</span>`;

                    // Tratamento Visual Colunas Travadas
                    let sg = m.sg5 === 'Sim' ? '<span class="safe">Sim</span>' : (m.sg5 === 'Nao' || m.sg5 === 'Não' ? '<span class="alert">Não</span>' : '-');
                    let sf = m.sf09 === 'Sim' ? '<span class="safe">Sim</span>' : (m.sf09 === 'Nao' || m.sf09 === 'Não' ? '<span class="alert">Não</span>' : '-');

                    tb.innerHTML += `
                    <tr class="hover:bg-slate-50 border-b transition" ${ctx}>
                        <td class="px-4 py-3">${brand}</td>
                        <td class="px-4 py-3 font-bold text-slate-700">${m.name} ${icon}</td>
                        <td class="px-4 py-3 text-slate-600">${m.concentration_display || '-'}</td>
                        <td class="px-4 py-3 text-blue-600 font-medium">${m.concMin} - ${m.concMax}</td>
                        <td class="px-2 py-3 text-center">${sg}</td>
                        <td class="px-2 py-3 text-center">${sf}</td>
                        <td class="px-4 py-3 text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },
        
        ctx: (e, id) => {
            e.preventDefault();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            let html = `<div class="p-2 bg-slate-100 font-bold text-xs uppercase border-b">${m.name}</div>`;
            try {
                JSON.parse(m.presentations).forEach(p => {
                    html += `<div class="ctx-item">${p.brand} <span class="text-xs text-gray-500">${p.description}</span></div>`;
                });
            } catch(e) {}
            menu.innerHTML = html;
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
        f.write(html)
    print("   Frontend: Tabela com 7 colunas restaurada.")

if __name__ == '__main__':
    fix_backend()
    fix_frontend()
