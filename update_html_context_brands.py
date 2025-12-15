import os

html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .hidden { display: none !important; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 100; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 250px; }
        .ctx-header { background: #f1f5f9; padding: 8px 12px; font-weight: bold; font-size: 0.75rem; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
        .ctx-item { padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f8fafc; font-size: 0.9em; color: #334155; }
        .ctx-item:hover { background-color: #eff6ff; color: #2563eb; }
        
        /* Estilos de Célula */
        .brand-single { color: #059669; font-weight: 600; font-size: 0.85rem; }
        .brand-multi { cursor: context-menu; color: #2563eb; font-weight: 700; font-size: 0.85rem; background: #eff6ff; padding: 2px 8px; rounded-full; border: 1px solid #dbeafe; }
    </style>
</head>
<body onclick="document.getElementById('context-menu').style.display='none'">

    <nav class="bg-white shadow p-4 mb-6 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <span class="text-2xl">💊</span>
            <h1 class="text-xl font-bold text-slate-800">OncoCalc Pro</h1>
        </div>
        <button onclick="window.location.reload()" class="text-sm bg-slate-100 px-3 py-1 rounded">Atualizar</button>
    </nav>

    <div class="container mx-auto px-4 overflow-x-auto">
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar...">

        <div class="bg-white shadow rounded overflow-hidden">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 uppercase text-xs font-bold text-slate-500 border-b">
                    <tr>
                        <th class="px-4 py-3 w-1/5">Nome Comercial</th>
                        <th class="px-4 py-3 w-1/5">Medicamento</th>
                        <th class="px-4 py-3 w-1/4">Apresentação</th>
                        <th class="px-4 py-3 text-blue-600">Faixa (mg/mL)</th>
                        <th class="px-2 py-3 text-center">SG 5%</th>
                        <th class="px-2 py-3 text-center">SF 0.9%</th>
                        <th class="px-4 py-3 text-center">Ações</th>
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
            } catch(e) {}
            
            document.getElementById('search').addEventListener('input', e => {
                App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(e.target.value.toLowerCase())));
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
                    
                    // --- 1. LÓGICA DE MARCAS (REQ: Ícone 📚 se > 1) ---
                    let rawBrand = m.brand_name || '-';
                    let brandHtml = '<span class="text-slate-300">-</span>';
                    
                    if (rawBrand !== '-') {
                        if (rawBrand.includes('|')) {
                            // Múltiplas: Ícone + Evento ContextMenu
                            // Passamos a lista de marcas para a função via data attribute ou direto no onclick (simplificado aqui)
                            // A string rawBrand contém "Marca A|Marca B".
                            // Escapamos as aspas para o JS
                            let safeBrandStr = rawBrand.replace(/'/g, "&#39;");
                            brandHtml = `<span class="brand-multi" oncontextmenu="App.openBrandMenu(event, '${m.name}', '${safeBrandStr}'); return false;" onclick="App.openBrandMenu(event, '${m.name}', '${safeBrandStr}')">📚 Vários</span>`;
                        } else {
                            // Única: Texto direto
                            brandHtml = `<span class="brand-single">${rawBrand}</span>`;
                        }
                    }

                    // --- 2. APRESENTAÇÃO ---
                    let displayApres = m.concentration || m.concentration_display || '-';
                    if (displayApres.includes('|')) displayApres = displayApres.replace(/\|/g, '<br>');

                    // --- 3. DEMAIS COLUNAS ---
                    let sg = (m.sg5 && m.sg5.toLowerCase().includes('sim')) ? '<span class="text-emerald-600 font-bold">Sim</span>' : ((m.sg5 && m.sg5.includes('Nao')) ? '<span class="text-red-500 font-bold">Não</span>' : '-');
                    let sf = (m.sf09 && m.sf09.toLowerCase().includes('sim')) ? '<span class="text-emerald-600 font-bold">Sim</span>' : ((m.sf09 && m.sf09.includes('Nao')) ? '<span class="text-red-500 font-bold">Não</span>' : '-');
                    let faixa = (m.concMin > 0) ? `${m.concMin} - ${m.concMax}` : '-';

                    tb.innerHTML += `
                    <tr class="hover:bg-slate-50">
                        <td class="px-4 py-3 align-top">${brandHtml}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name}</td>
                        <td class="px-4 py-3 align-top text-xs text-slate-600">${displayApres}</td>
                        <td class="px-4 py-3 align-top text-blue-600 font-medium text-xs">${faixa}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${sg}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${sf}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },
        
        openBrandMenu: (e, medName, brandString) => {
            e.preventDefault();
            e.stopPropagation(); // Impede fechar imediato
            
            const menu = document.getElementById('context-menu');
            const brands = brandString.split('|');
            
            let html = `<div class="ctx-header">${medName} - Marcas</div>`;
            brands.forEach(b => {
                html += `<div class="ctx-item">🏷️ ${b.trim()}</div>`;
            });
            
            menu.innerHTML = html;
            menu.style.display = 'block';
            
            let x = e.pageX; let y = e.pageY;
            if (x + 250 > window.innerWidth) x = window.innerWidth - 260;
            menu.style.left = `${x}px`; menu.style.top = `${y}px`;
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
