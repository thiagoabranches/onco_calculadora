import os

# HTML ATUALIZADO (SEM ÍCONE DE LIVRO)
html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Limpo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .hidden { display: none !important; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Status e Cores */
        .safe { color: #059669; font-weight: 600; background: #ecfdf5; padding: 2px 6px; rounded: 4px; border: 1px solid #a7f3d0; font-size: 0.75rem; }
        .alert { color: #dc2626; font-weight: 600; background: #fef2f2; padding: 2px 6px; rounded: 4px; border: 1px solid #fecaca; font-size: 0.75rem; }
        .neutral { color: #64748b; font-size: 0.8rem; }
        .brand-pill { color: #047857; font-weight: 700; font-size: 0.85rem; }
        
        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 50; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 200px; }
        .ctx-item { padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f1f5f9; font-size: 0.9em; }
        .ctx-item:hover { background-color: #eff6ff; color: #1d4ed8; }
    </style>
</head>
<body onclick="document.getElementById('context-menu').style.display='none'">

    <div class="container mx-auto p-4 max-w-full">
        <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
                <div class="bg-blue-600 text-white p-2 rounded-lg">💊</div>
                <div>
                    <h1 class="text-2xl font-bold text-slate-800">OncoCalc Pro</h1>
                    <p class="text-xs text-slate-500 font-bold uppercase">Módulo 1: Visualização Limpa</p>
                </div>
            </div>
            <div class="flex gap-2">
                <button onclick="window.location.reload()" class="text-sm bg-slate-100 px-3 py-1 rounded hover:bg-slate-200">Atualizar</button>
            </div>
        </div>
        
        <div class="relative mb-6">
            <input type="text" id="search" class="w-full p-3 pl-10 border border-slate-200 rounded-lg shadow-sm outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar...">
            <span class="absolute left-3 top-3 text-slate-400">🔍</span>
        </div>

        <div class="bg-white shadow-md rounded-xl overflow-hidden border border-slate-200 overflow-x-auto">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs font-bold border-b border-slate-200">
                    <tr>
                        <th class="px-4 py-3 w-1/6">Nome Comercial</th>
                        <th class="px-4 py-3 w-1/6">Medicamento</th>
                        <th class="px-4 py-3 w-1/4">Apresentação</th>
                        <th class="px-4 py-3 text-blue-600 w-1/6">Faixa (mg/mL)</th>
                        <th class="px-2 py-3 text-center w-1/12">SG 5%</th>
                        <th class="px-2 py-3 text-center w-1/12">SF 0.9%</th>
                        <th class="px-4 py-3 text-center w-1/12">Ações</th>
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
                    
                    // 1. MARCA
                    let brand = m.brand_name || '-';
                    if (brand === '-') brand = '<span class="text-slate-300">-</span>';
                    else if (brand.includes('|')) {
                        let parts = brand.split('|');
                        brand = `<span title="${brand}" class="brand-pill">${parts[0].trim()} <span class="text-[10px] text-gray-400 font-normal">(+${parts.length-1})</span></span>`;
                    } else {
                        brand = `<span class="brand-pill">${brand}</span>`;
                    }

                    // 2. APRESENTAÇÃO (Visualização em lista)
                    let displayApres = m.concentration || m.concentration_display || '-';
                    if (displayApres.includes('|')) displayApres = displayApres.replace(/\|/g, '<br>');

                    // 3. LOGICA INTERAÇÃO (Mantém menu, remove ícone)
                    let isMulti = (m.has_multiple_presentations === 1) || (displayApres.includes('<br>'));
                    // Ícone removido conforme solicitado
                    let rowClass = "hover:bg-slate-50 transition";
                    let ctxEvent = isMulti ? `oncontextmenu="App.showCtx(event, ${m.id}); return false;"` : '';
                    
                    // 4. DILUENTES
                    const formatDiluent = (val) => {
                        if (!val || val === '-') return '<span class="neutral">-</span>';
                        val = val.toLowerCase();
                        if (val.includes('sim')) return '<span class="safe">Sim</span>';
                        if (val.includes('nao') || val.includes('não')) return '<span class="alert">Não</span>';
                        return `<span class="neutral">${val}</span>`;
                    };
                    let sg = formatDiluent(m.sg5);
                    let sf = formatDiluent(m.sf09);

                    // 5. FAIXA
                    let faixa = (m.concMin > 0 || m.concMax > 0) 
                        ? `${m.concMin} - ${m.concMax}` 
                        : '<span class="text-slate-300">-</span>';

                    tb.innerHTML += `
                    <tr class="${rowClass}" ${ctxEvent}>
                        <td class="px-4 py-3 align-top">${brand}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name}</td> <td class="px-4 py-3 align-top text-slate-600 text-xs leading-snug">${displayApres}</td>
                        <td class="px-4 py-3 align-top text-blue-600 font-medium text-xs">${faixa}</td>
                        <td class="px-2 py-3 align-top text-center">${sg}</td>
                        <td class="px-2 py-3 align-top text-center">${sf}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700 font-bold shadow-sm">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },
        
        showCtx: (e, id) => {
            // Mantemos o menu de contexto apenas como recurso extra se o usuário clicar com direito
            e.preventDefault();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            
            let content = '';
            try {
                const p = JSON.parse(m.presentations);
                if(p.length) {
                    content = p.map(pr => `<div class="ctx-item"><span class="font-bold text-slate-700">${pr.brand}</span> <span class="text-xs text-gray-500">${pr.description}</span></div>`).join('');
                }
            } catch(err) {}

            if (content) {
                menu.innerHTML = `<div class='p-2 bg-slate-100 font-bold text-xs uppercase border-b text-slate-600'>${m.name}</div>` + content;
                menu.style.display = 'block';
                let x = e.pageX; let y = e.pageY;
                if (x + 200 > window.innerWidth) x = window.innerWidth - 220;
                menu.style.left = `${x}px`; menu.style.top = `${y}px`;
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

print("[SUCESSO] Interface limpa: Ícone de livros removido.")
