import os

html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Tooltip / Modal Styles */
        .info-icon { cursor: pointer; color: #3b82f6; margin-left: 6px; font-size: 1.1em; vertical-align: middle; transition: color 0.2s; }
        .info-icon:hover { color: #1d4ed8; }
        
        .tooltip-box { 
            position: absolute; 
            background: #ffffff; 
            border: 1px solid #cbd5e1; 
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); 
            padding: 12px; 
            border-radius: 8px; 
            z-index: 1000; 
            width: 280px; 
            font-size: 0.85rem; 
            color: #334155; 
            line-height: 1.4;
            display: none;
            pointer-events: none; /* Deixa passar eventos quando só hover */
        }
        .tooltip-box.sticky {
            display: block !important;
            pointer-events: auto;
            border-color: #3b82f6;
            border-width: 2px;
        }
        .tooltip-header {
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 6px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 4px;
            display: flex;
            justify-content: space-between;
        }
        .close-btn { cursor: pointer; color: #94a3b8; font-size: 1.2em; line-height: 0.8; }
        .close-btn:hover { color: #ef4444; }

        /* Outros Estilos */
        .safe { color: #059669; font-weight: 600; background: #ecfdf5; padding: 2px 6px; rounded: 4px; border: 1px solid #a7f3d0; font-size: 0.75rem; }
        .alert { color: #dc2626; font-weight: 600; background: #fef2f2; padding: 2px 6px; rounded: 4px; border: 1px solid #fecaca; font-size: 0.75rem; }
        .neutral { color: #64748b; font-size: 0.8rem; }
        .brand-pill { color: #047857; font-weight: 700; font-size: 0.85rem; }
        .brand-multi { cursor: context-menu; color: #2563eb; font-weight: 700; font-size: 0.85rem; background: #eff6ff; padding: 2px 8px; rounded-full; border: 1px solid #dbeafe; }
        
        #context-menu { position: absolute; z-index: 2000; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 250px; }
        .ctx-item { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f8fafc; font-size: 0.9em; }
        .ctx-item:hover { background-color: #eff6ff; color: #2563eb; }
    </style>
</head>
<body onclick="App.closeAllPopups()">

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

    <div id="global-tooltip" class="tooltip-box">
        <div class="tooltip-header">
            <span>Observações</span>
            <span class="close-btn" onclick="App.closeSticky(event)">×</span>
        </div>
        <div id="tooltip-content"></div>
    </div>

    <div id="context-menu"></div>

    <script>
    const App = {
        data: [],
        stickyId: null, // ID do medicamento com tooltip fixo

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
                    // Marcas
                    let rawBrand = m.brand_name || '-';
                    let brandHtml = '<span class="text-slate-300">-</span>';
                    if (rawBrand !== '-') {
                        if (rawBrand.includes('|')) {
                            let safeBrand = rawBrand.replace(/'/g, "&#39;");
                            brandHtml = `<span class="brand-multi" oncontextmenu="App.openCtx(event, '${m.name}', '${safeBrand}'); return false;">📚 Vários</span>`;
                        } else {
                            brandHtml = `<span class="brand-pill">${rawBrand}</span>`;
                        }
                    }

                    // Apresentação
                    let displayApres = m.concentration || m.concentration_display || '-';
                    if (displayApres.includes('|')) displayApres = displayApres.replace(/\|/g, '<br>');

                    // Faixa + Modal
                    let faixa = (m.concMin > 0) ? `${m.concMin} - ${m.concMax}` : '-';
                    let infoIcon = '';
                    if (m.observations && m.observations.length > 5) {
                        let safeObs = m.observations.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                        // Eventos: MouseOver (mostra), MouseOut (esconde se não fixo), Click (trava)
                        infoIcon = `<span class="info-icon" 
                            onmouseenter="App.showTooltip(event, '${safeObs}', ${m.id})" 
                            onmouseleave="App.hideTooltip(${m.id})"
                            onclick="App.toggleSticky(event, ${m.id})">ℹ️</span>`;
                    }

                    // Diluentes
                    const formatDil = (v) => {
                        if (!v) return '-';
                        if (v.includes('Sim')) return '<span class="safe">Sim</span>';
                        if (v.includes('Não') || v.includes('Nao')) return '<span class="alert">Não</span>';
                        return v;
                    };

                    tb.innerHTML += `
                    <tr class="hover:bg-slate-50 relative">
                        <td class="px-4 py-3 align-top">${brandHtml}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name}</td>
                        <td class="px-4 py-3 align-top text-xs text-slate-600">${displayApres}</td>
                        <td class="px-4 py-3 align-top text-blue-600 font-medium text-xs whitespace-nowrap">
                            ${faixa} ${infoIcon}
                        </td>
                        <td class="px-2 py-3 align-top text-center text-xs">${formatDil(m.sg5)}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${formatDil(m.sf09)}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },

        // --- LÓGICA DO TOOLTIP ---
        showTooltip: (e, text, id) => {
            if (App.stickyId && App.stickyId !== id) return; // Não mostra se outro estiver travado
            if (App.stickyId === id) return; // Já está travado, não mexe

            const tt = document.getElementById('global-tooltip');
            document.getElementById('tooltip-content').innerHTML = text;
            tt.style.display = 'block';
            tt.classList.remove('sticky');
            
            // Posiciona ao lado do mouse
            App.positionElement(tt, e.pageX, e.pageY);
        },

        hideTooltip: (id) => {
            if (App.stickyId === id) return; // Não esconde se estiver travado
            document.getElementById('global-tooltip').style.display = 'none';
        },

        toggleSticky: (e, id) => {
            e.stopPropagation(); // Impede fechar imediato
            const tt = document.getElementById('global-tooltip');
            
            if (App.stickyId === id) {
                // Destravar
                App.stickyId = null;
                tt.classList.remove('sticky');
                tt.style.display = 'none';
            } else {
                // Travar
                App.stickyId = id;
                tt.classList.add('sticky');
                tt.style.display = 'block';
                // Reposiciona para garantir
                App.positionElement(tt, e.pageX, e.pageY);
            }
        },

        closeSticky: (e) => {
            if(e) e.stopPropagation();
            App.stickyId = null;
            const tt = document.getElementById('global-tooltip');
            tt.style.display = 'none';
            tt.classList.remove('sticky');
        },

        // --- UTILITÁRIOS ---
        positionElement: (el, x, y) => {
            // Ajuste inteligente para não sair da tela
            let posX = x + 15;
            let posY = y + 15;
            
            if (posX + 280 > window.innerWidth) posX = x - 300;
            
            el.style.left = posX + 'px';
            el.style.top = posY + 'px';
        },

        openCtx: (e, name, brandsStr) => {
            e.preventDefault();
            e.stopPropagation();
            const menu = document.getElementById('context-menu');
            let html = `<div class="p-2 bg-slate-100 font-bold text-xs uppercase border-b text-slate-600">${name}</div>`;
            brandsStr.split('|').forEach(b => {
                html += `<div class="ctx-item">🏷️ ${b.trim()}</div>`;
            });
            menu.innerHTML = html;
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
        },

        closeAllPopups: () => {
            document.getElementById('context-menu').style.display='none';
            // Fecha tooltip se clicar fora E estiver travado
            const tt = document.getElementById('global-tooltip');
            if (App.stickyId && tt.style.display === 'block') {
               // Verifica se clicou dentro do tooltip? (Opcional, aqui fecha direto para simplificar)
               // App.closeSticky(); 
               // Melhor: só fecha se clicar fora do tooltip. Mas o body onclick pega tudo.
               // Vamos deixar o closeSticky lidar apenas com o botão X ou clicar fora.
               // Aqui assumimos que clicar no body destrava.
               App.closeSticky();
            }
        }
    };
    
    // Previne que clicar DENTRO do tooltip feche ele
    document.getElementById('global-tooltip').addEventListener('click', e => e.stopPropagation());

    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
