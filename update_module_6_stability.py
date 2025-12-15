import pandas as pd
import sqlite3
import glob
import os

db_file = "farmacia_clinica.db"

# --- FUNÇÕES DE SUPORTE ---
def find_excel_file():
    files = glob.glob("*PAMC*.xlsx")
    if not files: files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '', 'nan']: return "-"
    return str(val).replace('\n', ' ').strip()

def run_backend():
    print("--- ATUALIZANDO BANCO: ESTABILIDADES (R-S) ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    print(f"Lendo: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        target_sheet = None
        for sheet in xls.sheet_names:
            df_check = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            cols = [str(c) for c in df_check.columns]
            if any('Fármaco' in c for c in cols) or any('Farmaco' in c for c in cols):
                target_sheet = sheet
                break
        
        if not target_sheet: return

        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Garantir colunas
    try: 
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN stability_reconst TEXT DEFAULT '-'")
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN stability_diluted TEXT DEFAULT '-'")
    except: pass

    # Mapear colunas do Excel
    all_cols = df.columns.tolist()
    def find_col(keywords):
        for c in all_cols:
            if all(k in str(c).lower() for k in keywords): return c
        return None

    col_farmaco = find_col(['farmaco']) or find_col(['fármaco'])
    # Coluna R: Reconstituído / Frasco Aberto
    col_stab_rec = find_col(['reconstitu', 'aberto']) 
    # Coluna S: Diluição
    col_stab_dil = find_col(['dilui', 'após'])

    print("Importando estabilidades...")
    count = 0
    
    for _, row in df.iterrows():
        raw_name = clean_text(row.get(col_farmaco))
        if raw_name == '-' or 'Toxicidade' in raw_name: continue
        
        name_db = raw_name.capitalize()
        
        val_rec = clean_text(row.get(col_stab_rec))
        val_dil = clean_text(row.get(col_stab_dil))

        cursor.execute('''
            UPDATE medicamentos SET 
                stability_reconst = ?, stability_diluted = ?
            WHERE name = ?
        ''', (val_rec, val_dil, name_db))
        if cursor.rowcount > 0: count += 1

    conn.commit()
    conn.close()
    print(f"Backend atualizado: {count} registros.")

def run_frontend():
    print("--- ATUALIZANDO FRONTEND (COLUNA ESTABILIDADE ⏳) ---")
    
    html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Master</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Ícones */
        .icon-btn { cursor: pointer; font-size: 1.3em; transition: transform 0.2s; display: inline-block; vertical-align: middle; }
        .icon-btn:hover { transform: scale(1.2); }
        
        .phys-icon { color: #3b82f6; } 
        .stab-icon { color: #d97706; } /* Âmbar para tempo/estabilidade */

        /* Citotóxico */
        .row-cytotoxic { background-color: #fff1f2 !important; border-left: 4px solid #f43f5e; }
        .row-cytotoxic:hover { background-color: #ffe4e6 !important; }
        .cyto-badge { color: #e11d48; font-size: 0.8em; margin-left: 6px; vertical-align: middle; cursor: help; }

        /* Tooltip Flutuante (Hover) */
        .tooltip-box { 
            position: absolute; background: white; border: 1px solid #cbd5e1; 
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; 
            z-index: 1000; width: 320px; font-size: 0.85rem; color: #334155; display: none;
            line-height: 1.4;
        }
        .tooltip-header { font-weight: 700; color: #1e293b; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; margin-bottom: 6px; }

        /* Modais */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 3000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
        .modal-content { background: white; border-radius: 12px; width: 90%; max-width: 700px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); overflow: hidden; animation: modalIn 0.2s ease-out; }
        @keyframes modalIn { from {opacity: 0; transform: scale(0.95);} to {opacity: 1; transform: scale(1);} }
        .modal-header { background: #f1f5f9; padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 20px; }
        .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }
        .data-table td:first-child { font-weight: 600; color: #64748b; width: 40%; background: #f8fafc; }
        
        /* Menu Contexto */
        #context-menu { position: absolute; z-index: 2000; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 8px; min-width: 250px; overflow: hidden; }
        .ctx-header { background: #f8fafc; padding: 8px 12px; font-weight: 700; color: #475569; font-size: 0.75rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
        .ctx-row { padding: 8px 12px; font-size: 0.85rem; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; }
        .ctx-val { color: #1e293b; font-weight: 500; text-align: right; max-width: 160px; white-space: normal; }

        /* Status */
        .safe { color: #059669; font-weight: 600; background: #ecfdf5; padding: 2px 6px; rounded: 4px; font-size: 0.75rem; }
        .alert { color: #dc2626; font-weight: 600; background: #fef2f2; padding: 2px 6px; rounded: 4px; font-size: 0.75rem; }
        .neutral { color: #94a3b8; font-size: 0.8rem; }
        .brand-pill { color: #047857; font-weight: 700; font-size: 0.85rem; }
        .brand-multi { cursor: context-menu; color: #2563eb; font-weight: 700; font-size: 0.85rem; background: #eff6ff; padding: 2px 8px; rounded-full; border: 1px solid #dbeafe; }
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
        <input type="text" id="search" class="w-full p-3 border rounded shadow-sm mb-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="Buscar medicamento...">

        <div class="bg-white shadow rounded overflow-visible">
            <table class="w-full text-sm text-left">
                <thead class="bg-slate-50 uppercase text-xs font-bold text-slate-500 border-b">
                    <tr>
                        <th class="px-4 py-3">Nome Comercial</th>
                        <th class="px-4 py-3">Medicamento</th>
                        <th class="px-4 py-3">Apresentação</th>
                        <th class="px-4 py-3 text-purple-600">Via</th>
                        <th class="px-4 py-3 text-center w-16">Farmacot.</th>
                        <th class="px-4 py-3 text-center text-blue-600 w-16">Fís-Quím</th>
                        <th class="px-4 py-3 text-center text-amber-600 w-16">Estab.</th> <th class="px-2 py-3 text-center">SG 5%</th>
                        <th class="px-2 py-3 text-center">SF 0.9%</th>
                        <th class="px-4 py-3 text-center">Ações</th>
                    </tr>
                </thead>
                <tbody id="table-body" class="divide-y divide-slate-100"></tbody>
            </table>
        </div>
    </div>

    <div id="tooltip" class="tooltip-box">
        <div id="tooltip-header" class="tooltip-header">Info</div>
        <div id="tooltip-content"></div>
    </div>

    <div id="context-menu"></div>

    <div id="info-modal" class="modal-overlay" onclick="App.closeModal(event)">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="text-lg font-bold text-slate-800" id="modal-title">Detalhes</h3>
                <button onclick="document.getElementById('info-modal').style.display='none'" class="text-slate-400 hover:text-red-500 text-2xl">&times;</button>
            </div>
            <div class="modal-body">
                <table class="w-full text-sm data-table border border-slate-100 rounded-lg">
                    <tbody id="modal-table-body"></tbody>
                </table>
                <div class="mt-4 text-xs text-slate-400 text-center">Fonte: Base de Dados PAMC 2025</div>
            </div>
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
                tb.innerHTML += `<tr><td colspan="10" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    let rowClass = "hover:bg-slate-50 relative border-b border-slate-50";
                    let cytoBadge = "";
                    if (m.is_cytotoxic === 1) {
                        rowClass = "row-cytotoxic relative border-b border-red-100";
                        cytoBadge = '<span class="cyto-badge" title="Citotóxico">☣️</span>';
                    }

                    // Brands
                    let brand = m.brand_name || '-';
                    let brandHtml = '<span class="text-slate-300">-</span>';
                    if (brand !== '-' && (brand.includes('|') || brand.length > 25)) {
                         let safe = brand.replace(/'/g, "&#39;");
                         brandHtml = `<span class="brand-multi" oncontextmenu="App.ctxBrands(event, '${safe}'); return false;" onclick="App.ctxBrands(event, '${safe}')">📚 Vários</span>`;
                    } else if (brand !== '-') {
                        brandHtml = `<span class="brand-pill">${brand}</span>`;
                    }

                    let pres = m.concentration || m.concentration_display || '-';
                    if (pres.includes('|')) pres = pres.replace(/\|/g, '<br>');

                    // Ícones das Colunas
                    // 1. Farmacotécnica (Clipboard)
                    let paramIcon = `<div class="text-center">
                        <span class="icon-btn" onclick="App.modalParams(${m.id})" oncontextmenu="App.quickParams(event, ${m.id}); return false;">📋</span>
                    </div>`;

                    // 2. Físico-Químico (Info Blue)
                    let physIcon = `<div class="text-center">
                        <span class="icon-btn phys-icon" onclick="App.modalPhys(${m.id})" oncontextmenu="App.quickPhys(event, ${m.id}); return false;">ℹ️</span>
                    </div>`;

                    // 3. Estabilidade (Hourglass Amber) - NOVA
                    let stabContent = `Rec: ${m.stability_reconst}<br>Dil: ${m.stability_diluted}`;
                    let safeStab = stabContent.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                    let stabIcon = `<div class="text-center">
                        <span class="icon-btn stab-icon" 
                              onclick="App.modalStab(${m.id})" 
                              onmouseenter="App.showTip(event, '${safeStab}', 'Estabilidade')" 
                              onmouseleave="App.hideTip()">⏳</span>
                    </div>`;

                    const fmt = (v) => {
                        if (!v) return '-';
                        if (v.toUpperCase().includes('SIM')) return '<span class="safe">Sim</span>';
                        if (v.toUpperCase().includes('NÃO') || v.toUpperCase().includes('NAO')) return '<span class="alert">Não</span>';
                        return `<span class="neutral">${v}</span>`;
                    };

                    tb.innerHTML += `
                    <tr class="${rowClass}">
                        <td class="px-4 py-3 align-top">${brandHtml}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name} ${cytoBadge}</td>
                        <td class="px-4 py-3 align-top text-xs text-slate-600">${pres}</td>
                        <td class="px-4 py-3 align-top text-purple-700 font-bold text-xs">${m.via_admin || '-'}</td>
                        <td class="px-4 py-3 align-top">${paramIcon}</td>
                        <td class="px-4 py-3 align-top">${physIcon}</td>
                        <td class="px-4 py-3 align-top">${stabIcon}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sg5)}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sf09)}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },

        // --- MODAIS ---
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
                ['<span class="text-red-500 font-bold">Classificação Risco</span>', `<span class="text-red-600 font-bold">${m.risk_source || '-'}</span>`]
            ]);
        },
        modalStab: (id) => {
            const m = App.data.find(x => x.id === id);
            App.showModal(`${m.name} - Estabilidade`, [
                ['Após Reconstituição (Frasco Aberto)', m.stability_reconst],
                ['Após Diluição (Bolsa)', m.stability_diluted]
            ]);
        },

        showModal: (title, rows) => {
            document.getElementById('modal-title').innerText = title;
            let html = '';
            rows.forEach(r => html += `<tr><td>${r[0]}</td><td class="text-slate-700">${r[1] || '-'}</td></tr>`);
            document.getElementById('modal-table-body').innerHTML = html;
            document.getElementById('info-modal').style.display = 'flex';
        },
        closeModal: (e) => {
            if (e.target.id === 'info-modal') document.getElementById('info-modal').style.display = 'none';
        },

        // --- TOOLTIPS (HOVER) ---
        showTip: (e, text, title) => {
            const t = document.getElementById('tooltip');
            document.getElementById('tooltip-header').innerText = title;
            document.getElementById('tooltip-content').innerHTML = text;
            t.style.display = 'block';
            
            let x = e.pageX + 15;
            let y = e.pageY + 15;
            if (x + 320 > window.innerWidth) x = e.pageX - 330;
            
            t.style.left = x + 'px';
            t.style.top = y + 'px';
        },
        hideTip: () => {
            document.getElementById('tooltip').style.display = 'none';
        },

        // --- QUICK MENUS (RIGHT CLICK) ---
        quickParams: (e, id) => {
            e.preventDefault(); e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            App.showCtx(e, `${m.name} (Resumo)`, [['Vol. Reconst.', m.param_vol_reconst], ['Conc. Produto', m.param_conc_prod], ['Tempo', m.param_tempo_infusao]]);
        },
        quickPhys: (e, id) => {
            e.preventDefault(); e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            App.showCtx(e, `${m.name} (Segurança)`, [['Caráter', m.phys_carater], ['Filtro', m.phys_filtro], ['Risco', m.risk_source]]);
        },
        ctxBrands: (e, brands) => {
            e.preventDefault(); e.stopPropagation();
            const m = document.getElementById('context-menu');
            let html = '<div class="ctx-header">MARCAS</div>';
            brands.split('|').forEach(b => html += `<div class="ctx-row"><span class="ctx-val" style="text-align:left; width:100%">${b}</span></div>`);
            m.innerHTML = html;
            App.posCtx(e, m);
        },
        showCtx: (e, title, rows) => {
            const m = document.getElementById('context-menu');
            let html = `<div class="ctx-header">${title}</div>`;
            rows.forEach(r => { if(r[1] && r[1] !== '-') html += `<div class="ctx-row"><span class="ctx-label">${r[0]}</span><span class="ctx-val">${r[1]}</span></div>`; });
            m.innerHTML = html;
            App.posCtx(e, m);
        },
        posCtx: (e, el) => {
            el.style.display = 'block';
            let x = e.pageX;
            if (x + 260 > window.innerWidth) x = window.innerWidth - 270;
            el.style.left = x + 'px';
            el.style.top = e.pageY + 'px';
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
    print("Frontend atualizado com sucesso.")

if __name__ == '__main__':
    run_backend()
    run_frontend()
