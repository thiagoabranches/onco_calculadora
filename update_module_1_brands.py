import sqlite3
import json
import os
import re

# --- 1. DADOS DE ENTRADA (SEU JSON) ---
# Estou embutindo os dados do seu arquivo aqui para garantir que não falhe por "arquivo não encontrado"
json_marcas = """
[
  {
    "farmaco": "aflibercepte",
    "nome_comercial": "Zaltrap® Sanofi",
    "apresentacao": "100mg/4ml, 200mg/8ml"
  },
  {
    "farmaco": "alfapeginterferona 2a recombinante",
    "nome_comercial": "Pegasys® Roche",
    "apresentacao": "Seringa preenchida 180μg/0,5mL"
  },
  {
    "farmaco": "amivantamabe",
    "nome_comercial": "Rybrevant® Jansen Cilag",
    "apresentacao": "FA 350mg/7ml"
  }
]
"""

# Lista base de medicamentos (Recuperada do nosso sucesso anterior para não perder nada)
lista_base_nomes = [
    "Aflibercepte", "Alfapeginterferona 2a", "Amivantamabe", "Atezolizumabe", "Avelumabe", 
    "Azacitidina", "Bacilo de Calmette Guérin", "Belinostat", "Bendamustina", "Betadinutuximabe", 
    "Bevacizumabe", "Bleomicina", "Blinatumomabe", "Bortezomibe", "Brentuximabe vedotina", 
    "Bussulfano", "Cabazitaxel", "Carboplatina", "Carfilzomib", "Carmustina", "Cemiplimabe", 
    "Cetuximabe", "Ciclofosfamida", "Cidofovir", "Cisplatina", "Citarabina", "Cladribina", 
    "Dacarbazina", "Dactinomicina", "Daratumumab", "Daunorrubicina", "Decitabina", "Docetaxel", 
    "Dostarlimabe", "Doxorrubicina", "Doxorrubicina Lipossomal", "Durvalumabe", "Elotuzumabe", 
    "Elranatamabe", "Enfortumabe vedotina", "Epcoritamabe", "Epirrubicina", "Eribulina", 
    "Etoposídeo", "Fludarabina", "Fluorouracil", "Foscarnet", "Fotemustine", "Ganciclovir", 
    "Gencitabina", "Gentuzumabe ozogamicina", "Idarrubicina", "Ifosfamida", "Inotuzumabe ozogamicina", 
    "Interleucina", "Ipilimumabe", "Irinotecano", "Isatuximabe", "Lurbinectedin", "Melfalano", 
    "Metotrexato", "Mitomicina", "Mitoxantrona", "Nab-paclitaxel", "Naxitamabe", "Nivolumabe", 
    "Nivolumabe + Relatlimabe", "Obinutuzumabe", "Oxaliplatina", "Paclitaxel", "Panitumumabe", 
    "Pegaspargase", "Pembrolizumabe", "Pemetrexede", "Pertuzumabe", "Pertuzumabe + Trastuzumabe", 
    "Polatuzumabe vedotina", "Ramucirumabe", "Rituximabe", "Sacituzumabe govitecano", "Tafasitamabe", 
    "Talquetamabe", "Tarlatamabe", "Tebentafusp", "Teclistamabe", "Temozolomida", "Tensirolimo", 
    "Tiotepa", "Topotecano", "Trabectedina", "Trastuzumabe", "Trastuzumabe deruxtecan", 
    "Trastuzumabe entansina", "Tremelimumabe", "Trióxido de arsênio", "Vedolizumabe", "Vimblastina", 
    "Vincristina", "Vinflunina", "Vinorelbina", "Zolbetuximabe"
]

def normalize(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def run():
    print("--- ATUALIZANDO MÓDULO 1: COLUNA NOME COMERCIAL ---")
    
    db_file = 'farmacia_clinica.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 1. Atualizar Estrutura do Banco (Adicionar coluna brand_name se não existir)
    try:
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN brand_name TEXT DEFAULT '-'")
    except:
        pass # Coluna já existe

    # 2. Processar JSON de Marcas
    marcas_data = json.loads(json_marcas)
    mapa_marcas = {}
    
    # Criar mapa de correspondência (Normalizado -> Nome Comercial)
    for item in marcas_data:
        key = normalize(item['farmaco'])
        # Tratamento especial para alfapeginterferona devido a diferenças de grafia
        if "alfapeg" in key: key = "alfapeginterferona2a" 
        mapa_marcas[key] = item['nome_comercial']

    # 3. Atualizar Registros
    updates = 0
    
    # Primeiro, garanta que todos da lista base existem
    # (Reutilizando logica de check_and_fill para segurança)
    cursor.execute("SELECT name FROM medicamentos")
    existentes = [normalize(row[0]) for row in cursor.fetchall()]
    
    # Inserção de faltantes (caso o banco tenha sido resetado acidentalmente)
    for nome_base in lista_base_nomes:
        if normalize(nome_base) not in existentes:
            # Tenta inferir categoria
            cat = "Geral"
            if "mabe" in nome_base or "mab" in nome_base: cat = "Anticorpos Monoclonais"
            elif "rubicina" in nome_base or "platina" in nome_base: cat = "Quimioterápicos Clássicos"
            
            cursor.execute("INSERT INTO medicamentos (name, category) VALUES (?, ?)", (nome_base, cat))
    
    # Agora atualiza as marcas
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    for row in rows:
        med_id = row[0]
        name = row[1]
        key = normalize(name)
        
        brand = mapa_marcas.get(key, "-")
        
        cursor.execute("UPDATE medicamentos SET brand_name = ? WHERE id = ?", (brand, med_id))
        if brand != "-":
            print(f" [MARCA] {name} -> {brand}")
            updates += 1

    # 4. Reforçar Correção de Categorias (Antibióticos)
    cursor.execute("UPDATE medicamentos SET category = 'Antibióticos' WHERE category LIKE 'Antibiotico%' OR category LIKE 'Antibiótico%'")
    cursor.execute("UPDATE medicamentos SET category = 'Antimetabólitos' WHERE category LIKE 'Antimetab%'")
    
    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"SUCESSO: {updates} nomes comerciais vinculados.")
    print("-" * 30)

# --- GERAR NOVO HTML COM 4 COLUNAS ---
html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Módulo 1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 12px 16px; text-transform: uppercase; font-size: 0.8rem; color: #475569; letter-spacing: 0.05em; }
        .brand-text { color: #059669; font-weight: 600; } /* Verde para marca */
    </style>
</head>
<body>
    <div class="container mx-auto p-6 max-w-6xl">
        <div class="flex items-center gap-3 mb-6">
            <span class="text-3xl">💊</span>
            <div>
                <h1 class="text-2xl font-bold text-slate-800">OncoCalc Pro</h1>
                <p class="text-sm text-slate-500">Módulo 1: Identificação Comercial e Apresentação</p>
            </div>
        </div>
        
        <input type="text" id="search" class="w-full p-3 border border-slate-300 rounded-lg shadow-sm mb-6 outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar medicamento ou marca...">

        <div class="bg-white shadow-lg rounded-xl overflow-hidden border border-slate-200">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs font-bold">
                    <tr>
                        <th class="px-6 py-4 w-1/4">Nome Comercial</th> <th class="px-6 py-4 w-1/4">Medicamento</th>
                        <th class="px-6 py-4 w-1/3">Apresentação / Forma</th>
                        <th class="px-6 py-4 w-1/6 text-center">Status</th>
                    </tr>
                </thead>
                <tbody id="table-body" class="divide-y divide-slate-100"></tbody>
            </table>
        </div>
    </div>

    <div id="context-menu" class="absolute hidden bg-white border shadow-lg rounded-lg z-50 min-w-[200px]" onclick="this.style.display='none'"></div>

    <script>
    const App = {
        data: [],
        init: async () => {
            const res = await fetch('/api/medicamentos');
            App.data = await res.json();
            App.render(App.data);
            
            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => 
                    JSON.stringify(m).toLowerCase().includes(term)
                ));
            });
            
            document.body.addEventListener('click', () => document.getElementById('context-menu').style.display='none');
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
                tb.innerHTML += `<tr><td colspan="4" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    const isMulti = m.has_multiple_presentations === 1;
                    
                    let statusHtml = '<span class="text-gray-400 text-xs">Único</span>';
                    let rowClass = "hover:bg-gray-50 transition";
                    let ctxEvent = '';

                    if (isMulti) {
                        statusHtml = `<span class="text-blue-600 text-xs font-bold cursor-pointer">📚 Opções</span>`;
                        rowClass = "cursor-context-menu hover:bg-blue-50";
                        ctxEvent = `oncontextmenu="App.showCtx(event, ${m.id}); return false;"`;
                    }

                    // Verifica se tem marca definida
                    let brandHtml = m.brand_name && m.brand_name !== '-' ? 
                        `<span class="brand-text">${m.brand_name}</span>` : 
                        `<span class="text-gray-300">-</span>`;

                    tb.innerHTML += `
                    <tr class="${rowClass}" ${ctxEvent}>
                        <td class="px-6 py-4">${brandHtml}</td>
                        <td class="px-6 py-4 font-bold text-slate-700">${m.name}</td>
                        <td class="px-6 py-4 text-slate-600">${m.concentration_display || '-'}</td>
                        <td class="px-6 py-4 text-center">${statusHtml}</td>
                    </tr>`;
                });
            });
        },
        
        showCtx: (e, id) => {
            e.preventDefault();
            e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            
            let html = `<div class='p-2 bg-slate-100 font-bold text-xs uppercase border-b text-slate-500'>${m.name}</div>`;
            try {
                const p = JSON.parse(m.presentations);
                p.forEach(pr => {
                    html += `<div class="p-3 hover:bg-blue-50 cursor-pointer border-b border-slate-50 text-sm">
                        <div class="font-bold text-slate-700">${pr.brand}</div>
                        <div class="text-xs text-slate-500">${pr.description}</div>
                    </div>`;
                });
            } catch(e) {}
            
            menu.innerHTML = html;
            menu.style.display = 'block';
            menu.style.left = `${e.pageX}px`;
            menu.style.top = `${e.pageY}px`;
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

if __name__ == '__main__':
    run()
