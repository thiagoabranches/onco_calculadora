import pandas as pd
import sqlite3
import unicodedata
import os

# NOME EXATO ENCONTRADO NO SEU DIAGNÓSTICO
excel_file = "PAMC verso 06.2025 - Editado.xlsx"
db_file = "farmacia_clinica.db"

# MAPA DE TRADUÇÃO (NOMES PLANILHA -> NOMES BANCO)
manual_map = {
    "ALFAINTERFERONA 2B RECOMBINANTE": "Alfapeginterferona 2a",
    "ALFAINTERFERONA": "Alfapeginterferona 2a",
    "DOXORRUBICINA LIPOSSOMAL PEGUILADA": "Doxorrubicina Lipossomal",
    "PACLITAXEL (ABRAXANE)": "Nab-paclitaxel",
    "RAMUCIRUMABE (CYRAMZA)": "Ramucirumabe",
    "TRASTUZUMABE (HERCEPTIN)": "Trastuzumabe",
    "ZOLBETUXIMABE (VYLOY)": "Zolbetuximabe",
    "BENDAMUSTINA (RIBOMUSTIN)": "Bendamustina",
    "BORTEZOMIBE (VELCADE)": "Bortezomibe",
    "CABAZITAXEL (JEVTANA)": "Cabazitaxel",
    "CARFILZOMIBE (KYPROLIS)": "Carfilzomib",
    "CETUXIMABE (ERBITUX)": "Cetuximabe",
    "DARATUMUMABE (DARZALEX)": "Daratumumab",
    "DOCETAXEL (TAXOTERE)": "Docetaxel",
    "IPILIMUMABE (YERVOY)": "Ipilimumabe",
    "NIVOLUMABE (OPDIVO)": "Nivolumabe",
    "PEMBROLIZUMABE (KEYTRUDA)": "Pembrolizumabe",
    "PERTUZUMABE (PERJETA)": "Pertuzumabe",
    "RITUXIMABE (MABTHERA)": "Rituximabe",
    "TRASTUZUMABE DERUXTECANA": "Trastuzumabe deruxtecan",
    "TRASTUZUMABE ENTANSINA": "Trastuzumabe entansina",
    "VINORELBINA (NAVELBINE)": "Vinorelbina"
}

def normalize(text):
    if not isinstance(text, str): return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().strip()

def run():
    print(f"--- MOTOR DE DILUIÇÃO (LENDO EXCEL DIRETO) ---")
    
    if not os.path.exists(excel_file):
        print(f"[ERRO] Arquivo '{excel_file}' não está na pasta.")
        return

    print("Lendo arquivo Excel... (Pode demorar alguns segundos)")
    try:
        xls = pd.ExcelFile(excel_file)
        
        # 1. Encontrar a aba certa (procurando por 'Padroniza' ou 'Dilui')
        target_sheet = None
        for sheet in xls.sheet_names:
            if "PADRONIZA" in sheet.upper() or "DILUI" in sheet.upper():
                target_sheet = sheet
                break
        
        if not target_sheet:
            print("[ERRO] Aba de Padronização não encontrada no Excel.")
            return
            
        print(f"Lendo aba: '{target_sheet}'")
        df = pd.read_excel(xls, sheet_name=target_sheet)
        
    except Exception as e:
        print(f"[ERRO] Falha ao ler Excel: {e}")
        return

    # 2. Extrair Dados (Colunas Duplas)
    # A planilha tem blocos: Med | Soro | Vol (A,B,C) e Med | Soro | Vol (F,G,H)
    dilution_data = []
    blocks = [(0, 1, 2), (5, 6, 7)] # Índices das colunas
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            
            for _, row in sub.iterrows():
                n = str(row['nome'])
                # Pula cabeçalhos ou vazios
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                s = str(row['soro']).strip()
                v = str(row['vol']).strip()
                
                # Ignora linhas sem dados úteis
                if s == 'nan' and v == 'nan': continue
                
                dilution_data.append({
                    'raw_name': n.strip(),
                    'norm_name': normalize(n),
                    'soro': s.replace('nan', '-').replace('_', '-'),
                    'vol': v.replace('nan', '-').replace('_', '-')
                })

    print(f" [OK] Extraídos {len(dilution_data)} padrões de diluição.")

    # 3. Atualizar Banco de Dados
    print("Aplicando no Banco de Dados...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Garante colunas
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_diluent TEXT DEFAULT '-'")
    except: pass
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_volume TEXT DEFAULT '-'")
    except: pass

    cursor.execute("SELECT id, name FROM medicamentos")
    db_meds = cursor.fetchall()
    
    count = 0
    for med in db_meds:
        mid = med[0]
        db_name = med[1]
        db_norm = normalize(db_name)
        
        match = None
        
        # A. Mapa Manual (Prioridade Máxima)
        for k_excel, k_db in manual_map.items():
            if normalize(k_db) == db_norm:
                # Procura o nome do Excel na lista extraída
                match = next((d for d in dilution_data if normalize(k_excel) == d['norm_name']), None)
                break
        
        # B. Match Exato Normalizado
        if not match:
            match = next((d for d in dilution_data if d['norm_name'] == db_norm), None)
            
        # C. Match Parcial (ex: "Paclitaxel" dentro de "Paclitaxel 100mg")
        if not match:
            match = next((d for d in dilution_data if db_norm in d['norm_name'] or d['norm_name'] in db_norm), None)

        if match:
            s = match['soro']
            v = match['vol']
            
            # Só atualiza se tiver algo útil para escrever
            if (s != '-' and s != '') or (v != '-' and v != ''):
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", (s, v, mid))
                count += 1
                # print(f"FIX: {db_name} -> {s} em {v}")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} medicamentos atualizados com diluição.")
    print("-" * 30)

if __name__ == '__main__':
    run()
