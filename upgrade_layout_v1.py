import os

html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OncoCalc Pro | Farmácia Clínica</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    
    <style>
        body { 
            background-color: #f1f5f9; /* Slate-100 */
            color: #334155; 
            font-family: 'Inter', sans-serif; 
            -webkit-font-smoothing: antialiased;
        }
        
        /* Scrollbar Elegante */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

        /* Cabeçalho de Categoria */
        .category-header { 
            background: linear-gradient(to right, #e2e8f0, #f8fafc);
            color: #475569;
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 12px 20px;
            border-bottom: 1px solid #e2e8f0;
            position: sticky;
            left: 0;
        }

        /* Linhas da Tabela */
        tr.hover-row:hover td { background-color: #f8fafc; }
        
        /* Citotóxico */
        .row-cytotoxic { background-color: #fff1f2 !important; }
        .row-cytotoxic td:first-child { border-left: 4px solid #f43f5e; }
        .cyto-badge { color: #e11d48; font-size: 0.9em; margin-left: 6px; cursor: help; }

        /* Ícones e Botões */
        .icon-btn { 
            cursor: pointer; 
            font-size: 1.25rem; 
            transition: all 0.2s ease;
            opacity: 0.85;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 6px;
        }
        .icon-btn:hover { transform: translateY(-1px); opacity: 1; background-color: rgba(0,0,0,0.05); }
        
        .phys-icon { color: #3b82f6; } 
        .stab-icon { color: #d97706; }
        .clin-icon { color: #db2777; }
        .calc-btn {
            background-color: #2563eb; color: white;
            padding: 6px 12px; border-radius: 6px;
            font-size: 0.75rem; font-weight: 600;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
            transition: background 0.2s;
        }
        .calc-btn:hover { background-color: #1d4ed8; }

        /* Badges de Texto */
        .brand-pill { 
            background: #ecfdf5; color: #047857; 
            padding: 4px 8px; border-radius: 6px; 
            font-weight: 600; font-size: 0.75rem; border: 1px solid #d1fae5;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; display: inline-block;
        }
        .brand-multi { 
            background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe;
            cursor: context-menu; padding: 4px 8px; border-radius: 6px;
            font-weight: 600; font-size: 0.75rem;
        }
        .via-badge {
            background: #f3e8ff; color: #7e22ce; 
            padding: 2px 8px; border-radius: 12px;
            font-weight: 700; font-size: 0.7rem; border: 1px solid #e9d5ff;
        }

        /* Tooltip */
        .tooltip-box { 
            position: absolute; background: white; border: 1px solid #e2e8f0; 
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; 
            z-index: 50; width: 320px; font-size: 0.85rem; color: #334155; display: none; line-height: 1.5;
        }
        .tooltip-header { font-weight: 700; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; margin-bottom: 8px; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;}

        /* Modais */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.4); z-index: 60; display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
        .modal-content { background: white; border-radius: 16px; width: 95%; max-width: 800px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); overflow: hidden; animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
        
        .modal-header { background: white; padding: 20px 24px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 24px; overflow-y: auto; background: #fafafa; }
        
        /* Tabela Interna Modal */
        .data-table { width: 100%; border-collapse: separate; border-spacing: 0; background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
        .data-table td { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
        .data-table tr:last-child td { border-bottom: none; }
        .data-table td:first-child { font-weight: 600; color: #64748b; width: 35%; background: #f8fafc; border-right: 1px solid #f1f5f9; }
        
        /* Cards Clínicos */
        .clin-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .clin-title { font-weight: 700; color: #334155; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
        .clin-text { font-size: 0.9rem; color: #475569; line-height: 1.6; }
        .alert-box { background: #fef2f2; border-color: #fecaca; }
        .alert-box .clin-title { color: #b91c1c; }
        .alert-box .clin-text { color: #7f1d1d; }

        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 70; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 260px; overflow: hidden; }
        .ctx-header { background: #f8fafc; padding: 10px 14px; font-weight: 700; color: #64748b; font-size: 0.7rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; letter-spacing: 0.05em; }
        .ctx-item { padding: 10px 14px; font-size: 0.85rem; border-bottom: 1px solid #f8fafc; color: #334155; cursor: default; }
        .ctx-label { display: block; font-size: 0.7rem; color: #94a3b8; margin-bottom: 2px; font-weight: 600; }
        
        /* Diluentes */
        .dil-badge { font-weight: 600; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; display: inline-block; min-width: 40px; text-align: center; }
        .dil-sim { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .dil-nao { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .dil-dash { color: #cbd5e1; }
    </style>
</head>
<body onclick="App.closeAll()" class="h-screen flex flex-col overflow-hidden">

    <header class="bg-white border-b border-slate-200 shadow-sm z-20 flex-shrink-0 h-16 flex items-center justify-between px-6">
        <div class="flex items-center gap-3">
            <div class="bg-blue-600 text-white p-2 rounded-lg shadow-lg shadow-blue-600/20">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
            </div>
            <div>
                <h1 class="text-xl font-bold text-slate-800 tracking-tight leading-tight">OncoCalc <span class="text-blue-600">Pro</span></h1>
                <p class="text-[0.65rem] font-bold text-slate-400 uppercase tracking-widest">Farmácia Clínica Oncológica</p>
            </div>
        </div>
        
        <div class="flex gap-4 items-center">
            <div class="relative group">
                <input type="text" id="search" class="w-80 pl-10 pr-4 py-2 bg-slate-100 border border-transparent rounded-lg text-sm focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all outline-none" placeholder="Buscar medicamento, marca ou via...">
                <svg class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button onclick="window.location.reload()" class="p-2 text-slate-400 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition" title="Atualizar">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            </button>
        </div>
    </header>

    <main class="flex-1 overflow-hidden relative bg-slate-50 p-6">
        <div class="bg-white shadow-xl shadow-slate-200/50 rounded-xl border border-slate-200 overflow-hidden h-full flex flex-col">
            
            <div class="overflow-y-auto custom-scrollbar flex-1">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-slate-50 text-slate-500 text-xs font-bold uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th class="px-6 py-4 w-1/6 border-b border-slate-200 bg-slate-50">Nome Comercial</th>
                            <th class="px-6 py-4 w-1/6 border-b border-slate-200 bg-slate-50">Medicamento</th>
                            <th class="px-6 py-4 w-1/5 border-b border-slate-200 bg-slate-50">Apresentação</th>
                            <th class="px-4 py-4 border-b border-slate-200 bg-slate-50">Via</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50" title="Farmacotécnica">Farm.</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50" title="Físico-Químico">Fís-Q</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50" title="Estabilidade">Estab.</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50" title="Clínica">Clín.</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">SG 5%</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">SF 0.9%</th>
                            <th class="px-6 py-4 text-center border-b border-slate-200 bg-slate-50">Ações</th>
                        </tr>
                    </thead>
                    <tbody id="table-body" class="divide-y divide-slate-100 text-sm text-slate-600">
                        </tbody>
                </table>
            </div>
        </div>
    </main>

    <div id="tooltip" class="tooltip-box">
        <div id="tooltip-header" class="tooltip-header"></div>
        <div id="tooltip-content"></div>
    </div>

    <div id="context-menu"></div>

    <div id="info-modal" class="modal-overlay" onclick="App.closeModal(event, 'info-modal')">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="text-lg font-bold text-slate-800" id="modal-title">Detalhes</h3>
                <button onclick="document.getElementById('info-modal').style.display='none'" class="text-slate-400 hover:text-red-500 transition text-2xl">&times;</button>
            </div>
            <div class="modal-body">
                <table class="data-table">
                    <tbody id="modal-table-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <div id="clin-modal" class="modal-overlay" onclick="App.closeModal(event, 'clin-modal')">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="text-lg font-bold text-slate-800" id="clin-modal-title">Informações Clínicas</h3>
                <button onclick="document.getElementById('clin-modal').style.display='none'" class="text-slate-400 hover:text-red-500 transition text-2xl">&times;</button>
            </div>
            <div class="modal-body" id="clin-modal-body"></div>
        </div>
    </div>

    <script>
    const App = {
        data: [],

        init: async () => {
            try {
                const res = await fetch('/api/medicamentos');
                App.data = await res.json();
                App.render(App.data);
            } catch(e) { console.error("Erro ao carregar dados", e); }
            
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
                // Cabeçalho de Categoria
                tb.innerHTML += `<tr><td colspan="11" class="category-header sticky top-[53px] z-0">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    let rowClass = "hover-row transition duration-75";
                    let cytoBadge = "";
                    
                    if (m.is_cytotoxic === 1) {
                        rowClass = "row-cytotoxic hover:bg-red-50 transition duration-75";
                        cytoBadge = '<span class="cyto-badge" title="Citotóxico (Fonte: NIOSH)">☣️</span>';
                    }

                    // Marca
                    let brandHtml = '<span class="text-slate-300 font-light">-</span>';
                    let brand = m.brand_name || '-';
                    if (brand !== '-') {
                        if (brand.includes('|') || brand.length > 25) {
                             let safe = brand.replace(/'/g, "&#39;");
                             brandHtml = `<span class="brand-multi" oncontextmenu="App.ctxBrands(event, '${safe}'); return false;" onclick="App.ctxBrands(event, '${safe}')">📚 Vários</span>`;
                        } else {
                            brandHtml = `<span class="brand-pill">${brand}</span>`;
                        }
                    }

                    // Apresentação
                    let pres = m.concentration || m.concentration_display || '-';
                    if (pres.includes('|')) pres = pres.replace(/\|/g, '<br>');

                    // Ícones
                    let paramIcon = `<span class="icon-btn text-slate-500 hover:text-blue-600" onclick="App.modalParams(${m.id})" oncontextmenu="App.quickParams(event, ${m.id}); return false;" title="Farmacotécnica">📋</span>`;
                    let physIcon = `<span class="icon-btn phys-icon" onclick="App.modalPhys(${m.id})" oncontextmenu="App.quickPhys(event, ${m.id}); return false;" title="Físico-Químico">ℹ️</span>`;
                    
                    let stabContent = `Rec: ${m.stability_reconst}<br>Dil: ${m.stability_diluted}`;
                    let safeStab = stabContent.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                    let stabIcon = `<span class="icon-btn stab-icon" onclick="App.modalStab(${m.id})" onmouseenter="App.showTip(event, '${safeStab}', 'Estabilidade')" onmouseleave="App.hideTip()" title="Estabilidade">⏳</span>`;
                    
                    let clinIcon = `<span class="icon-btn clin-icon" onclick="App.modalClin(${m.id})" title="Dados Clínicos">🏥</span>`;

                    // Diluentes
                    const fmtDil = (v) => {
                        if (!v || v === '-') return '<span class="dil-dash">-</span>';
                        if (v.toUpperCase().includes('SIM')) return '<span class="dil-badge dil-sim">Sim</span>';
                        if (v.toUpperCase().includes('NÃO') || v.toUpperCase().includes('NAO')) return '<span class="dil-badge dil-nao">Não</span>';
                        return `<span class="text-xs text-slate-500">${v}</span>`;
                    };

                    tb.innerHTML += `
                    <tr class="${rowClass} border-b border-slate-100 last:border-0">
                        <td class="px-6 py-4 align-top">${brandHtml}</td>
                        <td class="px-6 py-4 align-top font-bold text-slate-800 text-[0.9rem] leading-snug">
                            ${m.name} ${cytoBadge}
                        </td>
                        <td class="px-6 py-4 align-top text-xs text-slate-500 leading-relaxed">${pres}</td>
                        <td class="px-4 py-4 align-top"><span class="via-badge">${m.via_admin || 'IV'}</span></td>
                        
                        <td class="px-2 py-4 align-top text-center">${paramIcon}</td>
                        <td class="px-2 py-4 align-top text-center">${physIcon}</td>
                        <td class="px-2 py-4 align-top text-center">${stabIcon}</td>
                        <td class="px-2 py-4 align-top text-center">${clinIcon}</td>
                        
                        <td class="px-2 py-4 align-top text-center">${fmtDil(m.sg5)}</td>
                        <td class="px-2 py-4 align-top text-center">${fmtDil(m.sf09)}</td>
                        <td class="px-6 py-4 align-top text-center">
                            <button class="calc-btn">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },

        // --- LÓGICA DE MODAIS E INTERAÇÃO (MANTIDA 100%) ---
        modalParams: (id) => {
            const m = App.data.find(x => x.id === id);
            App.showModal(`${m.name} - Farmacotécnica`, [
                ['Vol. Reconst.', m.param_vol_reconst],
                ['Conc. Produto', m.param_conc_prod],
                ['Diluentes', m.param_diluentes_raw],
                ['Conc. Máx.', m.param_conc_max_raw],
                ['Diluição Padrão', m.param_diluicao_padrao],
                ['Volume Padrão', m.param_vol_padrao],
                ['Tempo Infusão', m.param_tempo_infusao]
            ]);
        },
        modalPhys: (id) => {
            const m = App.data.find(x => x.id === id);
            App.showModal(`${m.name} - Físico-Químico`, [
                ['Incompatibilidade', m.phys_incomp],
                ['Fotossensibilidade', m.phys_foto],
                ['Caráter', m.phys_carater],
                ['Filtro', m.phys_filtro],
                ['Poder Emetogênico', m.phys_emeto],
                ['<span class="text-red-500 font-bold">Risco (NIOSH)</span>', `<span class="text-red-600 font-bold">${m.risk_source || '-'}</span>`]
            ]);
        },
        modalStab: (id) => {
            const m = App.data.find(x => x.id === id);
            App.showModal(`${m.name} - Estabilidade`, [
                ['Após Reconstituição', m.stability_reconst],
                ['Após Diluição', m.stability_diluted]
            ]);
        },
        modalClin: (id) => {
            const m = App.data.find(x => x.id === id);
            document.getElementById('clin-modal-title').innerText = `${m.name} - Clínica`;
            let content = '';
            if(m.toxicity && m.toxicity.length > 5) {
                content += `<div class="clin-card alert-box"><div class="clin-title">☣️ Toxicidade</div><div class="clin-text">${m.toxicity}</div></div>`;
            }
            if(m.nursing_care && m.nursing_care.length > 5) {
                content += `<div class="clin-card"><div class="clin-title">👩‍⚕️ Enfermagem</div><div class="clin-text">${m.nursing_care}</div></div>`;
            }
            if(m.particularities && m.particularities.length > 5) {
                content += `<div class="clin-card"><div class="clin-title">💡 Particularidades</div><div class="clin-text">${m.particularities}</div></div>`;
            }
            if(!content) content = '<div class="text-center text-gray-400 py-10">Sem dados clínicos adicionais.</div>';
            document.getElementById('clin-modal-body').innerHTML = content;
            document.getElementById('clin-modal').style.display = 'flex';
        },
        showModal: (title, rows) => {
            document.getElementById('modal-title').innerText = title;
            let html = '';
            rows.forEach(r => html += `<tr><td>${r[0]}</td><td class="text-slate-600 font-medium">${r[1] || '-'}</td></tr>`);
            document.getElementById('modal-table-body').innerHTML = html;
            document.getElementById('info-modal').style.display = 'flex';
        },
        closeModal: (e, id) => {
            if (e.target.id === id) document.getElementById(id).style.display = 'none';
        },
        showTip: (e, text, title) => {
            const t = document.getElementById('tooltip');
            document.getElementById('tooltip-header').innerText = title;
            document.getElementById('tooltip-content').innerHTML = text;
            t.style.display = 'block';
            let x = e.pageX + 15; let y = e.pageY + 15;
            if (x + 320 > window.innerWidth) x = e.pageX - 330;
            t.style.left = x + 'px'; t.style.top = y + 'px';
        },
        hideTip: () => { document.getElementById('tooltip').style.display = 'none'; },
        
        // Menus Rápidos (Direito)
        quickParams: (e, id) => {
            e.preventDefault(); e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            App.showCtx(e, `${m.name}`, [['Conc. Produto', m.param_conc_prod], ['Tempo', m.param_tempo_infusao]]);
        },
        quickPhys: (e, id) => {
            e.preventDefault(); e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            App.showCtx(e, `Segurança`, [['Filtro', m.phys_filtro], ['Caráter', m.phys_carater]]);
        },
        ctxBrands: (e, brands) => {
            e.preventDefault(); e.stopPropagation();
            const m = document.getElementById('context-menu');
            let html = '<div class="ctx-header">MARCAS</div>';
            brands.split('|').forEach(b => html += `<div class="ctx-item">${b}</div>`);
            m.innerHTML = html;
            App.posCtx(e, m);
        },
        showCtx: (e, title, rows) => {
            const m = document.getElementById('context-menu');
            let html = `<div class="ctx-header">${title}</div>`;
            rows.forEach(r => { if(r[1] && r[1] !== '-') html += `<div class="ctx-item"><span class="ctx-label">${r[0]}</span>${r[1]}</div>`; });
            m.innerHTML = html;
            App.posCtx(e, m);
        },
        posCtx: (e, el) => {
            el.style.display = 'block';
            let x = e.pageX;
            if (x + 260 > window.innerWidth) x = window.innerWidth - 270;
            el.style.left = x + 'px'; el.style.top = e.pageY + 'px';
        },
        closeAll: () => {
            document.getElementById('context-menu').style.display='none';
        }
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
print("Layout V1 aplicado com sucesso!")
