import os

# HTML focado APENAS na visualização correta das apresentações (Motor 1)
html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc - Módulo 1 (Motor de Apresentações)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .hidden { display: none; }
        
        /* Menu de Contexto (Visual Profissional) */
        #context-menu { 
            position: absolute; background: white; border: 1px solid #e2e8f0; z-index: 1000; display: none; 
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 220px; overflow: hidden;
        }
        .ctx-header { background: #f1f5f9; padding: 8px 12px; font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
        .ctx-item { padding: 10px 16px; cursor: pointer; border-bottom: 1px solid #f8fafc; font-size: 0.9rem; }
        .ctx-item:hover { background-color: #eff6ff; color: #2563eb; }
        
        /* Tabela */
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 12px 16px; text-transform: uppercase; font-size: 0.8rem; color: #475569; letter-spacing: 0.05em; }
        .row-multi { cursor: context-menu; }
        .row-multi:hover { background-color: #eff6ff; }
    </style>
</head>
<body onclick="document.getElementById('context-menu').style.display='none'">

    <div class="container mx-auto p-6 max-w-5xl">
        <div class="flex items-center gap-3 mb-6">
            <span class="text-3xl">💊</span>
            <div>
                <h1 class="text-2xl font-bold text-slate-800">OncoCalc Pro</h1>
                <p class="text-sm text-slate-500">Validação do Módulo 1: Medicamentos e Apresentações</p>
            </div>
        </div>
        
        <input type="text" id="search" class="w-full p-3 border border-slate-300 rounded-lg shadow-sm mb-6 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Buscar medicamento...">

        <div class="bg-white shadow-lg rounded-xl overflow-hidden border border-slate-200">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs font-bold">
                    <tr>
                        <th class="px-6 py-4 w-1/3">Medicamento</th>
                        <th class="px-6 py-4 w-1/3">Apresentação / Forma</th>
                        <th class="px-6 py-4 w-1/3 text-center">Status</th>
                    </tr>
                </thead>
                <tbody id="table-body" class="divide-y divide-slate-100"></tbody>
            </table>
        </div>
    </div>

    <div id="context-menu"></div>

    <script>
    const App = {
        data: [],
        init: async () => {
            try {
                const res = await fetch('/api/medicamentos');
                if(!res.ok) throw new Error('Falha na API');
                App.data = await res.json();
                App.render(App.data);
            } catch(e) {
                document.getElementById('table-body').innerHTML = '<tr><td colspan="3" class="p-4 text-center text-red-500">Erro ao carregar dados. Verifique o servidor.</td></tr>';
                console.error(e);
            }
            
            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(term)));
            });
        },
        
        render: (list) => {
            const tb = document.getElementById('table-body'); tb.innerHTML = '';
            
            if(list.length === 0) {
                tb.innerHTML = '<tr><td colspan="3" class="p-4 text-center text-gray-400">Nenhum resultado.</td></tr>';
                return;
            }

            // Agrupar
            const cats = {};
            list.forEach(m => {
                let c = m.category || 'Geral';
                if(!cats[c]) cats[c] = [];
                cats[c].push(m);
            });

            Object.keys(cats).sort().forEach(cat => {
                tb.innerHTML += `<tr><td colspan="3" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    
                    // LÓGICA DO MOTOR 1:
                    // has_multiple_presentations: 0 (Único) ou 1 (Múltiplo)
                    const isMulti = m.has_multiple_presentations === 1;
                    
                    let multiIcon = '';
                    let statusHtml = '<span class="text-gray-400 text-xs">Único</span>';
                    let rowClass = "hover:bg-gray-50 transition";
                    let ctxEvent = '';

                    if (isMulti) {
                        multiIcon = `<span class="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200 font-bold align-middle">📚 Opções</span>`;
                        statusHtml = `<span class="text-blue-600 text-xs font-bold">Clique botão direito</span>`;
                        rowClass = "row-multi";
                        ctxEvent = `oncontextmenu="App.showCtx(event, ${m.id}); return false;"`;
                    }

                    tb.innerHTML += `
                    <tr class="${rowClass}" ${ctxEvent}>
                        <td class="px-6 py-4 font-bold text-slate-700">${m.name} ${multiIcon}</td>
                        <td class="px-6 py-4 text-slate-600">${m.concentration_display || '-'}</td>
                        <td class="px-6 py-4 text-center">${statusHtml}</td>
                    </tr>`;
                });
            });
        },
        
        showCtx: (e, id) => {
            e.preventDefault();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            
            // Cabeçalho do menu
            let html = `<div class='ctx-header'>${m.name}</div>`;
            
            try {
                const p = JSON.parse(m.presentations);
                if (p && p.length > 0) {
                    p.forEach(pr => {
                        html += `<div class="ctx-item">
                            <span class="font-bold">${pr.brand}</span> 
                            <span class="text-gray-500 text-xs ml-1">${pr.description}</span>
                        </div>`;
                    });
                } else {
                    html += `<div class="p-3 text-sm text-gray-400">Sem dados detalhados</div>`;
                }
            } catch(e){
                html += `<div class="p-3 text-sm text-red-400">Erro de dados</div>`;
            }
            
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

# Garante que a pasta existe e salva o arquivo
if not os.path.exists("templates"):
    os.makedirs("templates")

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("[SUCESSO] HTML do Modulo 1 criado em 'templates/index.html'")
