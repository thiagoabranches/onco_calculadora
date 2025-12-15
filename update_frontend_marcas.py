import os

html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Módulo 1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .hidden { display: none !important; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        .brand-pill { color: #047857; font-weight: 600; font-size: 0.9em; }
        .med-name { color: #1e293b; font-weight: 700; }
        
        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 50; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 200px; }
        .ctx-item { padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f1f5f9; font-size: 0.9em; }
        .ctx-item:hover { background-color: #eff6ff; color: #1d4ed8; }
    </style>
</head>
<body onclick="document.getElementById('context-menu').style.display='none'">

    <div class="container mx-auto p-4 max-w-7xl">
        <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
                <div class="bg-blue-600 text-white p-2 rounded-lg">💊</div>
                <div>
                    <h1 class="text-2xl font-bold text-slate-800">OncoCalc Pro</h1>
                    <p class="text-xs text-slate-500 font-bold uppercase">Módulo 1: Identificação</p>
                </div>
            </div>
            <a href="/admin" class="text-sm text-slate-400 hover:text-slate-600">Admin</a>
        </div>
        
        <div class="relative mb-6">
            <input type="text" id="search" class="w-full p-4 pl-12 border border-slate-200 rounded-xl shadow-sm outline-none focus:ring-2 focus:ring-blue-500 text-lg" placeholder="Buscar medicamento, marca ou apresentação...">
            <span class="absolute left-4 top-4 text-slate-400">🔍</span>
        </div>

        <div class="bg-white shadow-md rounded-xl overflow-hidden border border-slate-200">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs font-bold border-b border-slate-200">
                    <tr>
                        <th class="px-6 py-4 w-1/4">Nome Comercial</th>
                        <th class="px-6 py-4 w-1/4">Fármaco</th>
                        <th class="px-6 py-4 w-1/3">Apresentação</th>
                        <th class="px-6 py-4 w-1/6 text-center">Opções</th>
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
                App.data = await res.json();
                App.render(App.data);
            } catch(e) { console.error(e); }
            
            document.getElementById('search').addEventListener('input', e => {
                const term = e.target.value.toLowerCase();
                App.render(App.data.filter(m => 
                    JSON.stringify(m).toLowerCase().includes(term)
                ));
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
                tb.innerHTML += `<tr><td colspan="4" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    const isMulti = m.has_multiple_presentations === 1;
                    
                    // Coluna Marca
                    let brands = m.brand_name || '-';
                    if (brands.includes('|')) {
                        // Se tiver muitas, mostra a primeira e "..."
                        let parts = brands.split('|');
                        brands = `<span title="${brands}">${parts[0].trim()} <span class="text-xs text-gray-400">(+${parts.length-1})</span></span>`;
                    }
                    
                    // Status / Botão
                    let statusHtml = '<span class="text-slate-300">-</span>';
                    let rowClass = "hover:bg-slate-50 transition";
                    let ctxEvent = '';

                    if (isMulti) {
                        statusHtml = `<button class="text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-xs font-bold border border-blue-100 hover:bg-blue-100">📚 Ver Frascos</button>`;
                        rowClass = "cursor-context-menu hover:bg-blue-50/50";
                        ctxEvent = `oncontextmenu="App.showCtx(event, ${m.id}); return false;" onclick="App.showCtx(event, ${m.id})"`; // Click também abre para facilitar
                    }

                    tb.innerHTML += `
                    <tr class="${rowClass}" ${ctxEvent}>
                        <td class="px-6 py-4 brand-pill">${brands}</td>
                        <td class="px-6 py-4 med-name">${m.name}</td>
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
            
            let html = `<div class='p-3 bg-slate-100 font-bold text-xs uppercase border-b text-slate-600'>${m.name}</div>`;
            try {
                const p = JSON.parse(m.presentations);
                if (p.length > 0) {
                    p.forEach(pr => {
                        html += `<div class="ctx-item">
                            <div class="font-bold text-slate-700">${pr.brand}</div>
                            <div class="text-xs text-slate-500">${pr.description}</div>
                        </div>`;
                    });
                } else {
                    html += `<div class="p-4 text-sm text-gray-400">Sem dados detalhados</div>`;
                }
            } catch(err) {
                html += `<div class="p-4 text-sm text-red-400">Erro de dados</div>`;
            }
            
            menu.innerHTML = html;
            menu.style.display = 'block';
            
            // Ajuste de posição para não sair da tela
            let x = e.pageX;
            let y = e.pageY;
            if (x + 200 > window.innerWidth) x = window.innerWidth - 220;
            
            menu.style.left = `${x}px`;
            menu.style.top = `${y}px`;
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
