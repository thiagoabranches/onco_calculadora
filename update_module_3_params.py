import pandas as pd
import sqlite3
import glob
import os
import re

db_file = "farmacia_clinica.db"

# --- 1. FUNÇÕES DE SUPORTE ---
def find_excel_file():
    files = glob.glob("*PAMC*.xlsx")
    if not files: files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '', 'nan']: return "-"
    return str(val).replace('\n', ' ').strip()

def run_backend():
    print("--- ATUALIZANDO BANCO COM PARÂMETROS FARMACOTÉCNICOS (COLUNAS E-L) ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    print(f"Lendo fonte: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        target_sheet = None
        for sheet in xls.sheet_names:
            df_check = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            # Verifica se tem colunas chaves
            cols = [str(c) for c in df_check.columns]
            if any('Fármaco' in c for c in cols) or any('Farmaco' in c for c in cols):
                target_sheet = sheet
                break
        
        if not target_sheet:
            print("[ERRO] Aba de dados não encontrada.")
            return

        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] Falha ao ler Excel: {e}")
        return

    # Conectar ao Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Adicionar Novas Colunas (se não existirem)
    new_cols = [
        'param_vol_reconst', 'param_conc_prod', 'param_diluentes_raw', 
        'param_conc_max_raw', 'param_diluicao_padrao', 'param_vol_padrao', 
        'param_tipo_infusao', 'param_tempo_infusao'
    ]
    
    for col in new_cols:
        try: cursor.execute(f"ALTER TABLE medicamentos ADD COLUMN {col} TEXT DEFAULT '-'")
        except: pass

    # Mapeamento das Colunas do Excel (E até L)
    # Precisamos achar os nomes exatos no DataFrame
    cols_map = {}
    all_cols = df.columns.tolist()
    
    # Busca inteligente de colunas pelo nome aproximado
    def find_col(keywords):
        for c in all_cols:
            c_str = str(c).lower()
            if all(k in c_str for k in keywords): return c
        return None

    col_farmaco = find_col(['farmaco']) or find_col(['fármaco'])
    cols_map['vol_reconst'] = find_col(['vol', 'reconstitu']) # Col E
    cols_map['conc_prod'] = find_col(['do produto']) # Col F ([ ] do produto)
    cols_map['diluentes'] = find_col(['diluente']) # Col G
    cols_map['conc_max'] = find_col(['máx', 'adm']) # Col H ([ ] máx. de adm.)
    cols_map['dil_padrao'] = find_col(['diluição', 'padrão']) # Col I
    cols_map['vol_padrao'] = find_col(['volume', 'padrão']) # Col J
    cols_map['tipo_inf'] = find_col(['tipo', 'infusão']) # Col K
    cols_map['tempo_inf'] = find_col(['tempo', 'infusão']) # Col L

    print("Atualizando registros...")
    count = 0
    
    for _, row in df.iterrows():
        raw_name = clean_text(row.get(col_farmaco))
        if raw_name == '-' or 'Toxicidade' in raw_name: continue
        
        name_db = raw_name.capitalize()
        
        # Extrai dados E-L
        p_vol_rec = clean_text(row.get(cols_map['vol_reconst']))
        p_conc_prod = clean_text(row.get(cols_map['conc_prod']))
        p_diluentes = clean_text(row.get(cols_map['diluentes']))
        p_conc_max = clean_text(row.get(cols_map['conc_max']))
        p_dil_padrao = clean_text(row.get(cols_map['dil_padrao']))
        p_vol_padrao = clean_text(row.get(cols_map['vol_padrao']))
        p_tipo_inf = clean_text(row.get(cols_map['tipo_inf']))
        p_tempo_inf = clean_text(row.get(cols_map['tempo_inf']))

        cursor.execute('''
            UPDATE medicamentos SET 
                param_vol_reconst = ?, param_conc_prod = ?, param_diluentes_raw = ?,
                param_conc_max_raw = ?, param_diluicao_padrao = ?, param_vol_padrao = ?,
                param_tipo_infusao = ?, param_tempo_infusao = ?
            WHERE name = ?
        ''', (
            p_vol_rec, p_conc_prod, p_diluentes, p_conc_max, 
            p_dil_padrao, p_vol_padrao, p_tipo_inf, p_tempo_inf, 
            name_db
        ))
        if cursor.rowcount > 0: count += 1

    conn.commit()
    conn.close()
    print(f"Backend atualizado: {count} registros com parâmetros.")

def run_frontend():
    print("--- ATUALIZANDO FRONTEND (NOVA COLUNA + MODAL) ---")
    
    html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OncoCalc Pro - Master</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f8fafc; color: #1e293b; font-family: sans-serif; }
        .category-header { background-color: #e2e8f0; font-weight: 700; padding: 10px 16px; text-transform: uppercase; font-size: 0.75rem; color: #475569; letter-spacing: 0.05em; border-top: 1px solid #cbd5e1; }
        
        /* Ícones e Botões */
        .info-icon { cursor: pointer; color: #3b82f6; margin-left: 4px; font-size: 1.1em; vertical-align: middle; }
        .param-icon { cursor: pointer; font-size: 1.2em; transition: transform 0.2s; display: inline-block; }
        .param-icon:hover { transform: scale(1.2); }
        
        /* Tooltip Flutuante (Hover) */
        .tooltip-box { 
            position: absolute; background: white; border: 1px solid #cbd5e1; 
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; 
            z-index: 1000; width: 300px; font-size: 0.85rem; color: #334155; display: none;
        }
        .tooltip-box.sticky { display: block !important; border-color: #3b82f6; border-width: 2px; }
        .close-btn { float: right; cursor: pointer; color: #94a3b8; font-size: 1.2em; margin-top: -5px; }

        /* Modal Principal (Dialog) */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 3000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
        .modal-content { background: white; border-radius: 12px; width: 90%; max-width: 700px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); overflow: hidden; animation: modalIn 0.2s ease-out; }
        @keyframes modalIn { from {opacity: 0; transform: scale(0.95);} to {opacity: 1; transform: scale(1);} }
        .modal-header { background: #f1f5f9; padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 20px; }
        .param-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }
        .param-table td:first-child { font-weight: 600; color: #64748b; width: 40%; background: #f8fafc; }
        
        /* Menu Contexto (Visualização Rápida) */
        #context-menu { position: absolute; z-index: 2000; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 8px; min-width: 250px; overflow: hidden; }
        .ctx-header { background: #f8fafc; padding: 8px 12px; font-weight: 700; color: #475569; font-size: 0.75rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
        .ctx-row { padding: 8px 12px; font-size: 0.85rem; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; }
        .ctx-label { color: #64748b; font-size: 0.75rem; font-weight: 600; }
        .ctx-val { color: #1e293b; font-weight: 500; text-align: right; max-width: 150px; }

        /* Status Pills */
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
                        <th class="px-4 py-3 text-center w-12">#</th> <th class="px-4 py-3">Nome Comercial</th>
                        <th class="px-4 py-3">Medicamento</th>
                        <th class="px-4 py-3">Apresentação</th>
                        <th class="px-4 py-3 text-purple-600">Via</th>
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

    <div id="tooltip" class="tooltip-box">
        <span class="close-btn" onclick="App.closeSticky(event)">×</span>
        <div id="tooltip-content"></div>
    </div>

    <div id="context-menu"></div>

    <div id="param-modal" class="modal-overlay" onclick="App.closeModal(event)">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="text-lg font-bold text-slate-800" id="modal-title">Parâmetros Farmacotécnicos</h3>
                <button onclick="document.getElementById('param-modal').style.display='none'" class="text-slate-400 hover:text-red-500 text-2xl">&times;</button>
            </div>
            <div class="modal-body">
                <table class="w-full text-sm param-table border border-slate-100 rounded-lg">
                    <tbody id="modal-table-body">
                        </tbody>
                </table>
                <div class="mt-4 text-xs text-slate-400 text-center">Fonte: Base de Dados PAMC 2025</div>
            </div>
        </div>
    </div>

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
                tb.innerHTML += `<tr><td colspan="9" class="category-header">${cat}</td></tr>`;
                
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    // Marcas
                    let brand = m.brand_name || '-';
                    let brandHtml = '<span class="text-slate-300">-</span>';
                    if (brand !== '-') {
                        if (brand.includes('|') || brand.length > 25) {
                             if(brand.includes('|')) {
                                let safe = brand.replace(/'/g, "&#39;");
                                brandHtml = `<span class="brand-multi" oncontextmenu="App.showBrandCtx(event, '${safe}'); return false;" onclick="App.showBrandCtx(event, '${safe}')">📚 Vários</span>`;
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

                    // Ícone Params (Coluna 1)
                    // Clique Esq: Modal | Clique Dir: Quick View
                    let paramIcon = `<div class="text-center" title="Ver Parâmetros">
                        <span class="param-icon" 
                              onclick="App.openParamModal(${m.id})" 
                              oncontextmenu="App.openParamQuick(event, ${m.id}); return false;">
                            📋
                        </span>
                    </div>`;

                    // Faixa + Obs
                    let faixa = (m.concMin > 0) ? `${m.concMin} - ${m.concMax}` : '-';
                    let infoIcon = '';
                    if (m.observations && m.observations.length > 5) {
                        let safeObs = m.observations.replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                        infoIcon = `<span class="info-icon" onmouseenter="App.showTip(event, '${safeObs}', ${m.id})" onclick="App.stickTip(event, ${m.id})">ℹ️</span>`;
                    }

                    // Diluentes
                    const fmt = (v) => {
                        if (!v) return '-';
                        if (v.toUpperCase().includes('SIM')) return '<span class="safe">Sim</span>';
                        if (v.toUpperCase().includes('NÃO') || v.toUpperCase().includes('NAO')) return '<span class="alert">Não</span>';
                        return `<span class="neutral">${v}</span>`;
                    };

                    tb.innerHTML += `
                    <tr class="hover:bg-slate-50 relative border-b border-slate-50">
                        <td class="px-4 py-3 align-top">${paramIcon}</td>
                        <td class="px-4 py-3 align-top">${brandHtml}</td>
                        <td class="px-4 py-3 align-top font-bold text-slate-700">${m.name}</td>
                        <td class="px-4 py-3 align-top text-xs text-slate-600">${pres}</td>
                        <td class="px-4 py-3 align-top text-purple-700 font-bold text-xs">${m.via_admin || '-'}</td>
                        <td class="px-4 py-3 align-top text-blue-600 font-medium text-xs whitespace-nowrap">${faixa} ${infoIcon}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sg5)}</td>
                        <td class="px-2 py-3 align-top text-center text-xs">${fmt(m.sf09)}</td>
                        <td class="px-4 py-3 align-top text-center">
                            <button class="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-blue-700">Calc</button>
                        </td>
                    </tr>`;
                });
            });
        },

        // --- LÓGICA DO MODAL (Botão Esquerdo) ---
        openParamModal: (id) => {
            const m = App.data.find(x => x.id === id);
            if (!m) return;

            document.getElementById('modal-title').innerText = `${m.name} - Parâmetros Técnicos`;
            
            const rows = [
                ['Volume de Reconstituição', m.param_vol_reconst],
                ['Concentração do Produto', m.param_conc_prod],
                ['Diluentes Permitidos', m.param_diluentes_raw],
                ['Conc. Máxima de Adm.', m.param_conc_max_raw],
                ['Diluição Padrão (Adulto)', m.param_diluicao_padrao],
                ['Volume Padrão (Adulto)', m.param_vol_padrao],
                ['Tipo de Infusão', m.param_tipo_infusao],
                ['Tempo de Infusão', m.param_tempo_infusao],
                ['Estabilidade (Reconstituído)', m.stability_reconst],
                ['Estabilidade (Diluído)', m.stability_diluted]
            ];

            let html = '';
            rows.forEach(r => {
                html += `<tr><td>${r[0]}</td><td class="text-slate-700">${r[1] || '-'}</td></tr>`;
            });

            document.getElementById('modal-table-body').innerHTML = html;
            document.getElementById('param-modal').style.display = 'flex';
        },

        closeModal: (e) => {
            if (e.target.id === 'param-modal') {
                document.getElementById('param-modal').style.display = 'none';
            }
        },

        // --- LÓGICA VISUALIZAÇÃO RÁPIDA (Botão Direito) ---
        openParamQuick: (e, id) => {
            e.preventDefault(); e.stopPropagation();
            const m = App.data.find(x => x.id === id);
            const menu = document.getElementById('context-menu');
            
            let html = `<div class="ctx-header">${m.name} (Resumo)</div>`;
            
            // Itens críticos para quick view
            const quickItems = [
                ['Vol. Reconst.', m.param_vol_reconst],
                ['Conc. Produto', m.param_conc_prod],
                ['Tempo Infusão', m.param_tempo_infusao],
                ['Diluente', m.param_diluentes_raw]
            ];

            quickItems.forEach(item => {
                if(item[1] && item[1] !== '-') {
                    html += `<div class="ctx-row">
                        <span class="ctx-label">${item[0]}</span>
                        <span class="ctx-val">${item[1]}</span>
                    </div>`;
                }
            });
            
            html += `<div class="p-2 text-center text-xs text-blue-500 cursor-pointer hover:underline" onclick="App.openParamModal(${id})">Ver Completo</div>`;

            menu.innerHTML = html;
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
        },

        // --- OUTRAS LÓGICAS ---
        showBrandCtx: (e, brands) => {
            e.preventDefault(); e.stopPropagation();
            const m = document.getElementById('context-menu');
            let html = '<div class="ctx-header">MARCAS COMERCIAIS</div>';
            brands.split('|').forEach(b => html += `<div class="p-2 border-b border-slate-50 text-sm hover:bg-slate-50">${b}</div>`);
            m.innerHTML = html;
            m.style.display = 'block';
            m.style.left = e.pageX + 'px';
            m.style.top = e.pageY + 'px';
        },

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
    print("Frontend atualizado com sucesso.")

if __name__ == '__main__':
    run_backend()
    run_frontend()
