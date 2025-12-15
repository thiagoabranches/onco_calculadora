import os

html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Completo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Estilos */
        .info-icon { cursor: pointer; color: #3b82f6; margin-left: 4px; font-size: 1.1em; vertical-align: middle; }
        .info-icon:hover { color: #1d4ed8; }
        
        .tooltip-box { 
            position: absolute; background: white; border: 1px solid #cbd5e1; 
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; 
            z-index: 1000; width: 300px; font-size: 0.85rem; color: #334155; display: none;
        }
        .tooltip-box.sticky { display: block !important; border-color: #3b82f6; border-width: 2px; }
        .close-btn { float: right; cursor: pointer; color: #94a3b8; font-size: 1.2em; margin-top: -5px; }
        .close-btn:hover { color: #ef4444; }

        .safe { color: #059669; font-weight: 600; background: #ecfdf5; padding: 2px 6px; rounded: 4px; font-size: 0.75rem; }
        .alert { color: #dc2626; font-weight: 600; background: #fef2f2; padding: 2px 6px; rounded: 4px; font-size: 0.75rem; }
        .neutral { color: #94a3b8; font-size: 0.8rem; }
        
        .brand-pill { color: #047857; font-weight: 700; font-size: 0.85rem; }
        .brand-multi { cursor: context-menu; color: #2563eb; font-weight: 700; font-size: 0.85rem; background: #eff6ff; padding: 2px 8px; rounded-full; border: 1px solid #dbeafe; }
        
        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 2000; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 8px; min-width: 200px; }
        .ctx-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f8fafc; font-size: 0.9em; }
        .ctx-item:hover { background-color: #eff6ff; color: #2563eb; }
    </style>
</head>
<body onclick="App.closeAll()">

    <nav class="bg-white shadow p-4 mb-6 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <span class="text-2xl">💊</span>
            <h1 class="text-xl font-bold text-slate-800">OncoCalc Pro</h1>
        </div>
        <button onclick="window.location.reload()" class="text-sm bg-slate-100 px-3 py-1 rounded hover:bg-slate-200">Atualizar</button>
    </nav>

    <div class="container mx-auto px-4 overflow-x-auto pb-20">
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar...">

        <div class="bg-white shadow rounded overflow-visible">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 uppercase text-xs font-bold text-slate-500 border-b">
                    <tr>
                        <th class="px-4 py-3">Nome Comercial</th>
                        <th class="px-4 py-3">Medicamento</th>
                        <th class="px-4 py-3">Apresentação</th>
                        <th class="px-4 py-3 text-purple-600">Via</th> <th class="px-4 py-3 text-blue-600">Faixa (mg/mL)</th>
                        <th class="px-2 py-3 text-center">SG 5%</th>
                        <th class="px-2 py-3 text-center">SF 0.9%</th>
                        <th class="px-4 py-3 text-center">Ações</th>
                    </tr>
                </thead>
                <tbody id="table-body" class="divide-y divide-slate-100"></tbody>
            </table>
        </div>
    </div>

    <div id="tooltip" class="tooltip-box">
        <span class="close-btn" onclick="App.closeSticky(event)">×</span>
        <div id="tooltip-content"></div>
    </div>

    <div id="context-menu"></div>

    <script>
    const App = {
        data: [],
        stickyId: null,

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
                tb.innerHTML += `<tr><td colspan="8" class="category-header">${cat}</td></tr>`; // Colspan 8 agora
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    // Marcas
                    let brand = m.brand_name || '-';
                    let brandHtml = '<span class="text-slate-300">-</span>';
                    if (brand !== '-') {
                        if (brand.includes('|') || brand.length > 25) { // Lógica simples para detectar multi
                             // Se tiver pipe, usa menu
                             if(brand.includes('|')) {
                                let safe = brand.replace(/'/g, "&#39;");
                                brandHtml = `<span class="brand-multi" oncontextmenu="App.ctx(event, '${safe}'); return false;" onclick="App.ctx(event, '${safe}')">📚 Vários</span>`;
                             } else {
                                brandHtml = `<span class="brand-pill">${brand}</span>`;
                             }
                        } else {
                            brandHtml = `<span class="brand-pill">${brand}</span>`;
                        }
                    }

                    // Apresentação
                    let pres = m.concentration || m.concentration_display || '-';
                    if (pres.includes('|')) pres = pres.replace(/\|/g, '<br>');

                    // Via (NOVO)
                    let via = m.via_admin || '-';
                    
                    // Faixa + Obs
                    let faixa = (m.concMin > 0) ? `${m.concMin} - ${m.concMax}` : '-';
                    let icon = '';
                    if (m.observations && m.observations.length > 5) {
                        let safeObs = m.observations.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                        icon = `<span class="info-icon" onmouseenter="App.showTip(event, '${safeObs}', ${m.id})" onclick="App.stickTip(event, ${m.id})">ℹ️</span>`;
                    }

                    // Diluentes
                    const fmt = (v) => {
                        if (!v) return '-';
                        if (v.toUpperCase().includes('SIM')) return '<span class="safe">Sim</span>';
                        if (v.toUpperCase().includes('NÃO') || v.toUpperCase().includes('NAO')) return '<span class="alert">Não</span>';
                        return `<span class="neutral">${v}</span>`;
                    };

                    tb.innerHTML += `
                    <tr class="hover:bg-slate-50 relative">
                        <td class="px-4 py-3 align-top">${brandHtml}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name}</td>
                        <td class="px-4 py-3 align-top text-xs text-slate-600">${pres}</td>
                        <td class="px-4 py-3 align-top text-purple-700 font-bold text-xs">${via}</td> <td class="px-4 py-3 align-top text-blue-600 font-medium text-xs whitespace-nowrap">${faixa} ${icon}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sg5)}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sf09)}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },

        // Tooltip Lógica
        showTip: (e, text, id) => {
            if (App.stickyId && App.stickyId !== id) return;
            if (App.stickyId === id) return;
            const t = document.getElementById('tooltip');
            document.getElementById('tooltip-content').innerHTML = text;
            t.style.display = 'block';
            t.classList.remove('sticky');
            t.style.left = (e.pageX + 15) + 'px';
            t.style.top = (e.pageY + 15) + 'px';
        },
        stickTip: (e, id) => {
            e.stopPropagation();
            const t = document.getElementById('tooltip');
            if (App.stickyId === id) { App.stickyId = null; t.style.display = 'none'; }
            else { App.stickyId = id; t.classList.add('sticky'); }
        },
        closeSticky: (e) => {
            e.stopPropagation();
            App.stickyId = null;
            document.getElementById('tooltip').style.display = 'none';
        },
        
        // Menu Lógica
        ctx: (e, brands) => {
            e.preventDefault(); e.stopPropagation();
            const m = document.getElementById('context-menu');
            let html = '<div class="p-2 bg-slate-100 font-bold text-xs border-b">MARCAS</div>';
            brands.split('|').forEach(b => html += `<div class="ctx-item">${b}</div>`);
            m.innerHTML = html;
            m.style.display = 'block';
            m.style.left = e.pageX + 'px';
            m.style.top = e.pageY + 'px';
        },
        
        closeAll: () => {
            document.getElementById('context-menu').style.display='none';
            if (!App.stickyId) document.getElementById('tooltip').style.display='none';
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
