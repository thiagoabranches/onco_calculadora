import pandas as pd
import sqlite3
import glob
import os

db_file = "farmacia_clinica.db"

def find_excel_file():
    files = glob.glob("*PAMC*.xlsx")
    if not files: files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '', 'nan']: return ""
    return str(val).replace('\n', ' ').strip()

def run_backend():
    print("--- MOTOR DE PADRONIZAÇÃO DE DILUIÇÕES ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    print(f"Lendo: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        # Procura a aba "Padronização..."
        target_sheet = next((s for s in xls.sheet_names if "padroniza" in s.lower() and "dilui" in s.lower()), None)
        
        if not target_sheet:
            print("[ERRO] Aba 'Padronização de Diluições' não encontrada.")
            return

        print(f"Processando aba: {target_sheet}")
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # Normalizar o DataFrame (Lidar com listas duplas lado a lado)
    # A planilha parece ter: MED | SORO | VOL ... MED | SORO | VOL
    # Vamos empilhar
    
    # Identifica colunas
    cols = df.columns.tolist()
    # Pega indices das colunas de Medicamento
    med_indices = [i for i, c in enumerate(cols) if 'medicamento' in str(c).lower()]
    
    data_list = []
    
    for idx in med_indices:
        # Assume que as colunas seguintes são Soro e Volume
        if idx + 2 < len(cols):
            sub_df = df.iloc[:, idx:idx+3]
            sub_df.columns = ['med', 'soro', 'vol']
            data_list.append(sub_df)
            
    if not data_list:
        print("[AVISO] Estrutura da aba não reconhecida. Tentando leitura direta.")
        # Fallback se não achar colunas duplas
        if 'MEDICAMENTO' in df.columns:
            data_list.append(df[['MEDICAMENTO', 'SORO', 'VOLUME PARA ADULTOS']].rename(columns={'MEDICAMENTO':'med', 'SORO':'soro', 'VOLUME PARA ADULTOS':'vol'}))

    final_df = pd.concat(data_list, ignore_index=True)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Novas Colunas
    try: 
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_diluent TEXT DEFAULT '-'")
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_volume TEXT DEFAULT '-'")
    except: pass

    print("Atualizando padronização...")
    count = 0
    
    for _, row in final_df.iterrows():
        raw_name = clean_text(row['med'])
        if not raw_name or 'MEDICAMENTO' in raw_name.upper(): continue
        
        # Tenta achar o medicamento no banco (match flexível)
        # A planilha de padronização pode ter nomes simplificados
        name_search = raw_name.capitalize()
        
        diluent = clean_text(row['soro'])
        volume = clean_text(row['vol'])
        
        if not diluent and not volume: continue

        # Update
        # Usa LIKE para pegar variações (ex: "Paclitaxel" na tabela vs "Paclitaxel 100mg" na lista)
        cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE name LIKE ?", (diluent, volume, f"{name_search}%"))
        if cursor.rowcount > 0: count += 1

    conn.commit()
    conn.close()
    print(f"Backend atualizado: {count} padronizações aplicadas.")

def run_frontend():
    print("--- ATUALIZANDO LAYOUT (SUBSTITUIÇÃO DE COLUNAS) ---")
    
    html_code = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OncoCalc Pro | Farmácia Clínica</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #f1f5f9; color: #334155; font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

        /* TABELA */
        .category-header { background: linear-gradient(to right, #e2e8f0, #f8fafc); color: #475569; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; padding: 12px 20px; border-bottom: 1px solid #e2e8f0; position: sticky; left: 0; }
        tr.hover-row:hover td { background-color: #f8fafc; }
        .row-cytotoxic { background-color: #fff1f2 !important; }
        .row-cytotoxic td:first-child { border-left: 4px solid #f43f5e; }
        .cyto-badge { color: #e11d48; font-size: 0.9em; margin-left: 6px; cursor: help; }

        /* ÍCONES */
        .icon-btn { cursor: pointer; font-size: 1.25rem; transition: all 0.2s ease; opacity: 0.85; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
        .icon-btn:hover { transform: translateY(-1px); opacity: 1; background-color: rgba(0,0,0,0.05); }
        .phys-icon { color: #3b82f6; } 
        .stab-icon { color: #d97706; }
        .clin-icon { color: #db2777; }
        .calc-btn-table { background-color: #2563eb; color: white; padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2); transition: background 0.2s; }
        .calc-btn-table:hover { background-color: #1d4ed8; }

        /* BADGES */
        .brand-pill { background: #ecfdf5; color: #047857; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; border: 1px solid #d1fae5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; display: inline-block; }
        .brand-multi { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; cursor: context-menu; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
        .via-badge { background: #f3e8ff; color: #7e22ce; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.7rem; border: 1px solid #e9d5ff; }
        
        /* NOVA PADRONIZAÇÃO (DILUIÇÃO) */
        .std-badge { 
            display: inline-block; padding: 4px 10px; border-radius: 6px; 
            font-weight: 700; font-size: 0.75rem; text-align: center; min-width: 80px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid transparent;
        }
        /* SF 0.9% -> Amarelo + Preto */
        .std-sf { background-color: #fef08a; color: #000000; border-color: #fde047; }
        /* SG 5% -> Azul + Branco */
        .std-sg { background-color: #2563eb; color: #ffffff; border-color: #1d4ed8; }
        /* Outros */
        .std-other { background-color: #f1f5f9; color: #64748b; border-color: #e2e8f0; }

        /* MODAIS */
        .tooltip-box { position: absolute; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; z-index: 50; width: 320px; font-size: 0.85rem; color: #334155; display: none; line-height: 1.5; }
        .tooltip-header { font-weight: 700; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; margin-bottom: 8px; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;}
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.4); z-index: 60; display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
        .modal-content { background: white; border-radius: 16px; width: 95%; max-width: 800px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); overflow: hidden; animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
        .modal-header { background: white; padding: 20px 24px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 24px; overflow-y: auto; background: #fafafa; }
        
        .data-table { width: 100%; border-collapse: separate; border-spacing: 0; background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
        .data-table td { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
        .data-table tr:last-child td { border-bottom: none; }
        .data-table td:first-child { font-weight: 600; color: #64748b; width: 35%; background: #f8fafc; border-right: 1px solid #f1f5f9; }
        
        .clin-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .clin-title { font-weight: 700; color: #334155; font-size: 0.9rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
        .clin-text { font-size: 0.9rem; color: #475569; line-height: 1.6; }
        .alert-box { background: #fef2f2; border-color: #fecaca; }
        .alert-box .clin-title { color: #b91c1c; }
        .alert-box .clin-text { color: #7f1d1d; }

        #context-menu { position: absolute; z-index: 70; display: none; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 8px; min-width: 260px; overflow: hidden; }
        .ctx-header { background: #f8fafc; padding: 10px 14px; font-weight: 700; color: #64748b; font-size: 0.7rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; letter-spacing: 0.05em; }
        .ctx-item { padding: 10px 14px; font-size: 0.85rem; border-bottom: 1px solid #f8fafc; color: #334155; cursor: default; }
        .ctx-label { display: block; font-size: 0.7rem; color: #94a3b8; margin-bottom: 2px; font-weight: 600; }

        .calc-input { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 2px; font-size: 0.9rem; }
        .calc-input:focus { border-color: #3b82f6; outline: none; ring: 2px solid #bfdbfe; }
        .calc-label { display: block; font-size: 0.75rem; font-weight: 700; color: #64748b; margin-bottom: 2px; margin-top: 8px;}
        .calc-result { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 16px; border-radius: 8px; text-align: center; margin-top: 16px; animation: slideUp 0.2s ease-out; }
        .calc-res-val { font-size: 1.5rem; font-weight: 800; color: #15803d; }
        .tab-btn { padding: 10px 20px; font-size: 0.85rem; font-weight: 600; color: #64748b; border-bottom: 2px solid transparent; cursor: pointer; transition: all 0.2s; }
        .tab-btn:hover { color: #334155; }
        .tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; background: #f8fafc; }
        .tab-content { display: none; padding: 20px 0; }
        .tab-content.active { display: block; }
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
            <button onclick="Calc.open()" class="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 font-semibold text-sm transition border border-indigo-100">
                <span>🧮</span> Calculadoras
            </button>

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
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">Farm.</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">Fís-Q</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">Estab.</th>
                            <th class="px-2 py-4 text-center border-b border-slate-200 bg-slate-50">Clín.</th>
                            <th class="px-4 py-4 text-center border-b border-slate-200 bg-slate-50">Padronização</th> <th class="px-6 py-4 text-center border-b border-slate-200 bg-slate-50">Ações</th>
                        </tr>
                    </thead>
                    <tbody id="table-body" class="divide-y divide-slate-100 text-sm text-slate-600"></tbody>
                </table>
            </div>
        </div>
    </main>

    <div id="tooltip" class="tooltip-box"><div id="tooltip-header" class="tooltip-header"></div><div id="tooltip-content"></div></div>
    <div id="context-menu"></div>

    <div id="info-modal" class="modal-overlay" onclick="App.closeModal(event, 'info-modal')">
        <div class="modal-content"><div class="modal-header"><h3 class="text-lg font-bold text-slate-800" id="modal-title">Detalhes</h3><button onclick="document.getElementById('info-modal').style.display='none'" class="text-slate-400 hover:text-red-500 text-2xl">&times;</button></div><div class="modal-body"><table class="data-table"><tbody id="modal-table-body"></tbody></table></div></div>
    </div>
    <div id="clin-modal" class="modal-overlay" onclick="App.closeModal(event, 'clin-modal')">
        <div class="modal-content"><div class="modal-header"><h3 class="text-lg font-bold text-slate-800" id="clin-modal-title">Info</h3><button onclick="document.getElementById('clin-modal').style.display='none'" class="text-slate-400 hover:text-red-500 text-2xl">&times;</button></div><div class="modal-body" id="clin-modal-body"></div></div>
    </div>
    <div id="calc-modal" class="modal-overlay" onclick="Calc.close(event)">
        <div class="modal-content" style="max-width: 550px;">
            <div class="modal-header bg-indigo-50"><div class="flex items-center gap-2"><span class="text-2xl">🧮</span><h3 class="text-lg font-bold text-indigo-900">Calculadoras Clínicas</h3></div><button onclick="document.getElementById('calc-modal').style.display='none'" class="text-slate-400 hover:text-red-500 text-2xl">&times;</button></div>
            <div class="px-6 border-b border-slate-100 flex gap-4 bg-white"><div class="tab-btn active" onclick="Calc.tab('calvert', this)">Calvert</div><div class="tab-btn" onclick="Calc.tab('bsa', this)">SC (BSA)</div><div class="tab-btn" onclick="Calc.tab('crcl', this)">ClCr</div></div>
            <div class="modal-body">
                <div id="tab-calvert" class="tab-content active"><div class="grid grid-cols-2 gap-4 mb-4"><div><label class="calc-label">Sexo</label><select id="cal-sex" class="calc-input bg-white"><option value="M">Masculino</option><option value="F">Feminino</option></select></div><div><label class="calc-label">Idade (anos)</label><input type="number" id="cal-age" class="calc-input"></div><div><label class="calc-label">Peso (kg)</label><input type="number" id="cal-weight" class="calc-input"></div><div><label class="calc-label">Altura (cm)</label><input type="number" id="cal-height" class="calc-input"></div><div><label class="calc-label">Creatinina (mg/dL)</label><input type="number" id="cal-scr" class="calc-input" step="0.01"></div><div><label class="calc-label text-indigo-600">AUC Alvo</label><input type="number" id="cal-auc" class="calc-input border-indigo-200 bg-indigo-50"></div></div><div class="flex items-center gap-3 mb-6 bg-slate-50 p-3 rounded-lg border border-slate-200"><input type="checkbox" id="cal-cap" class="w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500"><label for="cal-cap" class="text-xs font-bold text-slate-600 cursor-pointer select-none">Cap Conservador (Max 100 mL/min)</label></div><button onclick="Calc.runCalvertAdvanced()" class="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700 shadow-md">Calcular</button><div id="res-cal" class="calc-result hidden text-left bg-white border border-indigo-100 shadow-sm"><div class="text-center border-b border-slate-100 pb-3 mb-3"><span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Dose Final</span><br><span class="text-4xl font-black text-indigo-600" id="val-dose-final">000 mg</span></div><div class="grid grid-cols-2 gap-2 text-xs text-slate-500"><div class="bg-slate-50 p-2 rounded"><span class="block text-[0.65rem] uppercase font-bold text-slate-400">TFG Calc.</span><span id="val-gfr-raw" class="font-mono font-bold text-slate-700 text-lg">00</span> mL/min</div><div class="bg-slate-50 p-2 rounded"><span class="block text-[0.65rem] uppercase font-bold text-slate-400">TFG Usada</span><span id="val-gfr-used" class="font-mono font-bold text-slate-700 text-lg">00</span> mL/min</div></div><div class="mt-2 text-xs text-slate-400">Peso: <span id="val-weight-type" class="font-bold text-slate-600">Real</span></div><div id="cal-warning" class="mt-3 text-xs text-red-700 font-bold bg-red-50 p-3 rounded border border-red-100 hidden"></div></div></div>
                <div id="tab-bsa" class="tab-content"><label class="calc-label">Peso (kg)</label><input type="number" id="bsa-peso" class="calc-input"><label class="calc-label">Altura (cm)</label><input type="number" id="bsa-altura" class="calc-input"><button onclick="Calc.runBSA()" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold mt-4">Calcular</button><div id="res-bsa" class="calc-result hidden">SC = <span class="calc-res-val" id="val-bsa">0.00</span> m²</div></div>
                <div id="tab-crcl" class="tab-content"><div class="grid grid-cols-2 gap-4"><div><label class="calc-label">Creatinina</label><input type="number" id="cr-creat" class="calc-input" step="0.1"></div><div><label class="calc-label">Peso</label><input type="number" id="cr-peso" class="calc-input"></div><div><label class="calc-label">Idade</label><input type="number" id="cr-idade" class="calc-input"></div><div><label class="calc-label">Sexo</label><select id="cr-sexo" class="calc-input"><option value="M">Masculino</option><option value="F">Feminino</option></select></div></div><button onclick="Calc.runCrCl()" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold mt-4">Calcular</button><div id="res-crcl" class="calc-result hidden">ClCr = <span class="calc-res-val" id="val-crcl">00</span> mL/min</div></div>
            </div>
        </div>
    </div>

    <script>
    // JS MANTIDO (Calculadoras + App)
    const Calc = {
        open: () => document.getElementById('calc-modal').style.display = 'flex',
        close: (e) => { if(e.target.id === 'calc-modal') document.getElementById('calc-modal').style.display = 'none'; },
        tab: (name, btn) => {
            document.querySelectorAll('.tab-content').forEach(d => d.style.display='none');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('tab-'+name).style.display='block';
            btn.classList.add('active');
        },
        runCalvertAdvanced: () => {
            const sex = document.getElementById('cal-sex').value;
            const age = parseFloat(document.getElementById('cal-age').value);
            const weight = parseFloat(document.getElementById('cal-weight').value);
            const height = parseFloat(document.getElementById('cal-height').value);
            let scr = parseFloat(document.getElementById('cal-scr').value);
            const auc = parseFloat(document.getElementById('cal-auc').value);
            const useCap = document.getElementById('cal-cap').checked;
            const resDiv = document.getElementById('res-cal');
            const warnDiv = document.getElementById('cal-warning');
            if(!age || !weight || !height || !scr || !auc) { alert("Preencha todos os campos."); return; }
            let ibw = (sex === 'M') ? 50 + 2.3 * ((height/2.54) - 60) : 45.5 + 2.3 * ((height/2.54) - 60);
            const bmi = weight / ((height/100)**2);
            let weightUsed = (bmi >= 25) ? ibw + 0.4 * (weight - ibw) : weight;
            let weightLabel = (bmi >= 25) ? "Ajustado (IMC ≥ 25)" : "Real (IMC < 25)";
            if (scr < 0.7) scr = 0.7;
            let gfr = ((140 - age) * weightUsed) / (72 * scr);
            if (sex === 'F') gfr *= 0.85;
            const gfrRaw = gfr;
            let gfrFinal = gfr;
            if (useCap && gfr > 100) gfrFinal = 100;
            const dose = auc * (gfrFinal + 25);
            const doseRounded = Math.round(dose / 10) * 10;
            document.getElementById('val-dose-final').innerText = doseRounded + " mg";
            document.getElementById('val-gfr-raw').innerText = gfrRaw.toFixed(1);
            document.getElementById('val-gfr-used').innerText = gfrFinal.toFixed(1);
            document.getElementById('val-weight-type').innerText = weightLabel + ` (${weightUsed.toFixed(1)} kg)`;
            warnDiv.classList.add('hidden');
            if (gfrRaw < 20) {
                warnDiv.innerText = "ALERTA: TFG < 20 mL/min. Calvert não recomendado.";
                warnDiv.classList.remove('hidden');
                warnDiv.className = "mt-3 text-xs text-red-700 font-bold bg-red-50 p-3 rounded border border-red-100";
            } else if (useCap && gfrRaw > 100) {
                warnDiv.innerText = "Nota: TFG limitada a 100 mL/min.";
                warnDiv.classList.remove('hidden');
                warnDiv.className = "mt-3 text-xs text-blue-700 font-bold bg-blue-50 p-3 rounded border border-blue-100";
            }
            resDiv.classList.remove('hidden');
        },
        runBSA: () => {
            const p = parseFloat(document.getElementById('bsa-peso').value);
            const a = parseFloat(document.getElementById('bsa-altura').value);
            if(p && a) {
                const bsa = Math.sqrt((p * a) / 3600);
                document.getElementById('val-bsa').innerText = bsa.toFixed(2);
                document.getElementById('res-bsa').classList.remove('hidden');
            }
        },
        runCrCl: () => {
            const cr = parseFloat(document.getElementById('cr-creat').value);
            const p = parseFloat(document.getElementById('cr-peso').value);
            const age = parseFloat(document.getElementById('cr-idade').value);
            const sex = document.getElementById('cr-sexo').value;
            if(cr && p && age) {
                let cl = ((140 - age) * p) / (72 * cr);
                if(sex === 'F') cl *= 0.85;
                document.getElementById('val-crcl').innerText = cl.toFixed(1);
                document.getElementById('res-crcl').classList.remove('hidden');
            }
        }
    };

    const App = {
        data: [],
        init: async () => {
            try { const res = await fetch('/api/medicamentos'); App.data = await res.json(); App.render(App.data); } catch(e) {}
            document.getElementById('search').addEventListener('input', e => App.render(App.data.filter(m => JSON.stringify(m).toLowerCase().includes(e.target.value.toLowerCase()))));
        },
        render: (list) => {
            const tb = document.getElementById('table-body'); tb.innerHTML = '';
            const cats = {}; list.forEach(m => { let c = m.category || 'Geral'; if(!cats[c]) cats[c] = []; cats[c].push(m); });
            Object.keys(cats).sort().forEach(cat => {
                tb.innerHTML += `<tr><td colspan="11" class="category-header sticky top-[53px] z-0">${cat}</td></tr>`;
                cats[cat].sort((a,b) => a.name.localeCompare(b.name)).forEach(m => {
                    let rowClass = m.is_cytotoxic ? "row-cytotoxic hover:bg-red-50 transition" : "hover-row transition";
                    let cytoBadge = m.is_cytotoxic ? '<span class="cyto-badge" title="Citotóxico (Fonte: NIOSH)">☣️</span>' : '';
                    let brand = m.brand_name || '-';
                    let brandHtml = (brand !== '-' && (brand.includes('|') || brand.length > 25)) ? 
                        `<span class="brand-multi" oncontextmenu="App.ctxBrands(event, '${brand.replace(/'/g, "&#39;")}')">📚 Vários</span>` : 
                        (brand !== '-' ? `<span class="brand-pill">${brand}</span>` : '<span class="text-slate-300">-</span>');
                    let pres = m.concentration || '-'; if (pres.includes('|')) pres = pres.replace(/\|/g, '<br>');
                    
                    let icons = [
                        `<span class="icon-btn text-slate-500 hover:text-blue-600" onclick="App.modalParams(${m.id})" oncontextmenu="App.quickParams(event, ${m.id}); return false;">📋</span>`,
                        `<span class="icon-btn phys-icon" onclick="App.modalPhys(${m.id})" oncontextmenu="App.quickPhys(event, ${m.id}); return false;">ℹ️</span>`,
                        `<span class="icon-btn stab-icon" onclick="App.modalStab(${m.id})" onmouseenter="App.showTip(event, 'Rec: ${m.stability_reconst}<br>Dil: ${m.stability_diluted}'.replace(/'/g,''), 'Estabilidade')" onmouseleave="App.hideTip()">⏳</span>`,
                        `<span class="icon-btn clin-icon" onclick="App.modalClin(${m.id})">🏥</span>`
                    ];
                    
                    // --- NOVA LÓGICA PADRONIZAÇÃO ---
                    let stdContent = '<span class="dil-dash">-</span>';
                    if (m.std_volume && m.std_volume !== '-') {
                        let dil = m.std_diluent ? m.std_diluent.toUpperCase() : '';
                        let styleClass = 'std-other';
                        
                        if (dil.includes('SF') || dil.includes('0,9') || dil.includes('CLORETO')) {
                            styleClass = 'std-sf'; // Amarelo + Preto
                        } else if (dil.includes('SG') || dil.includes('5%') || dil.includes('GLICOSE')) {
                            styleClass = 'std-sg'; // Azul + Branco
                        }
                        
                        // Badge único com o volume
                        stdContent = `<span class="std-badge ${styleClass}" title="${m.std_diluent}">${m.std_volume}</span>`;
                    }

                    tb.innerHTML += `<tr class="${rowClass} border-b border-slate-100 last:border-0">
                        <td class="px-6 py-4 align-top">${brandHtml}</td>
                        <td class="px-6 py-4 align-top font-bold text-slate-800 text-[0.9rem] leading-snug">${m.name} ${cytoBadge}</td>
                        <td class="px-6 py-4 align-top text-xs text-slate-500 leading-relaxed">${pres}</td>
                        <td class="px-4 py-4 align-top"><span class="via-badge">${m.via_admin || 'IV'}</span></td>
                        ${icons.map(i => `<td class="px-2 py-4 align-top text-center">${i}</td>`).join('')}
                        
                        <td class="px-4 py-4 align-top text-center">${stdContent}</td> <td class="px-6 py-4 align-top text-center"><button class="calc-btn-table" onclick="Calc.open()">Calc</button></td>
                    </tr>`;
                });
            });
        },
        // Modal functions...
        modalParams: (id) => App.openInfoModal(id, 'Farmacotécnica', [['Vol. Reconst.', 'param_vol_reconst'], ['Conc. Produto', 'param_conc_prod'], ['Diluentes', 'param_diluentes_raw'], ['Conc. Máx.', 'param_conc_max_raw'], ['Diluição Padrão', 'param_diluicao_padrao'], ['Volume Padrão', 'param_vol_padrao'], ['Tempo Infusão', 'param_tempo_infusao']]),
        modalPhys: (id) => App.openInfoModal(id, 'Físico-Químico', [['Incompatibilidade', 'phys_incomp'], ['Fotossensibilidade', 'phys_foto'], ['Caráter', 'phys_carater'], ['Filtro', 'phys_filtro'], ['Risco (NIOSH)', 'risk_source']]),
        modalStab: (id) => App.openInfoModal(id, 'Estabilidade', [['Reconstituído', 'stability_reconst'], ['Diluído', 'stability_diluted']]),
        openInfoModal: (id, title, fields) => { const m = App.data.find(x => x.id === id); document.getElementById('modal-title').innerText = `${m.name} - ${title}`; let html = ''; fields.forEach(f => html += `<tr><td>${f[0]}</td><td class="text-slate-600">${m[f[1]] || '-'}</td></tr>`); document.getElementById('modal-table-body').innerHTML = html; document.getElementById('info-modal').style.display = 'flex'; },
        modalClin: (id) => { const m=App.data.find(x=>x.id===id); document.getElementById('clin-modal-title').innerText=`${m.name} - Clínica`; let c=''; if(m.toxicity&&m.toxicity.length>5)c+=`<div class="clin-card alert-box"><div class="clin-title">☣️ Toxicidade</div><div class="clin-text">${m.toxicity}</div></div>`; if(m.nursing_care&&m.nursing_care.length>5)c+=`<div class="clin-card"><div class="clin-title">👩‍⚕️ Enfermagem</div><div class="clin-text">${m.nursing_care}</div></div>`; if(m.particularities&&m.particularities.length>5)c+=`<div class="clin-card"><div class="clin-title">💡 Particularidades</div><div class="clin-text">${m.particularities}</div></div>`; if(!c)c='<div class="text-center text-gray-400 py-10">Sem dados.</div>'; document.getElementById('clin-modal-body').innerHTML=c; document.getElementById('clin-modal').style.display='flex'; },
        closeModal: (e, id) => { if(e.target.id === id) document.getElementById(id).style.display = 'none'; },
        showTip: (e, text, title) => { const t = document.getElementById('tooltip'); document.getElementById('tooltip-header').innerText = title; document.getElementById('tooltip-content').innerHTML = text; t.style.display = 'block'; t.style.left = (e.pageX+15)+'px'; t.style.top = (e.pageY+15)+'px'; },
        hideTip: () => document.getElementById('tooltip').style.display='none',
        ctxBrands: (e, b) => App.showCtx(e, 'MARCAS', b.split('|').map(x=>['',x])),
        quickParams: (e, id) => { const m=App.data.find(x=>x.id===id); App.showCtx(e, 'Resumo', [['Vol', m.param_vol_reconst], ['Tempo', m.param_tempo_infusao]]); },
        quickPhys: (e, id) => { const m=App.data.find(x=>x.id===id); App.showCtx(e, 'Segurança', [['Filtro', m.phys_filtro], ['Caráter', m.phys_carater]]); },
        showCtx: (e, t, rows) => { e.preventDefault(); e.stopPropagation(); const m=document.getElementById('context-menu'); let h=`<div class="ctx-header">${t}</div>`; rows.forEach(r=>{if(r[1])h+=`<div class="ctx-item">${r[0]?`<span class="ctx-label">${r[0]}</span>`:''}${r[1]}</div>`}); m.innerHTML=h; m.style.display='block'; m.style.left=e.pageX+'px'; m.style.top=e.pageY+'px'; },
        closeAll: () => document.getElementById('context-menu').style.display='none'
    };
    document.addEventListener('DOMContentLoaded', App.init);
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)
