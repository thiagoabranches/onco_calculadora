import pandas as pd
import sqlite3
import unicodedata
import os
import glob

db_file = "farmacia_clinica.db"

# MAPA MANUAL (Nomes Planilha -> Nomes Banco)
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

def find_excel_file():
    # Procura qualquer .xlsx que tenha PAMC no nome
    files = glob.glob("*PAMC*.xlsx")
    if not files:
        # Se falhar, pega qualquer xlsx
        files = glob.glob("*.xlsx")
    
    if files:
        print(f" [ARQUIVO ENCONTRADO] '{files[0]}'")
        return files[0]
    return None

def run():
    print("--- MOTOR DE DILUIÇÃO V2 (AUTOMÁTICO) ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Nenhuma planilha encontrada na pasta.")
        return

    print("Lendo planilha...")
    try:
        xls = pd.ExcelFile(excel_file)
        # Procura aba
        target_sheet = next((s for s in xls.sheet_names if "PADRONIZA" in s.upper() or "DILUI" in s.upper()), None)
        
        if not target_sheet:
            print("[ERRO] Aba de Padronização não encontrada.")
            return
            
        print(f"Lendo aba: '{target_sheet}'")
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # Extrair Dados (Colunas Duplas)
    dilution_data = []
    # Indices: (A,B,C) e (F,G,H) -> 0,1,2 e 5,6,7
    blocks = [(0, 1, 2), (5, 6, 7)]
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            
            for _, row in sub.iterrows():
                n = str(row['nome'])
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                s = str(row['soro']).strip()
                v = str(row['vol']).strip()
                
                if s == 'nan' and v == 'nan': continue
                
                dilution_data.append({
                    'raw_name': n.strip(),
                    'norm_name': normalize(n),
                    'soro': s.replace('nan', '-').replace('_', '-'),
                    'vol': v.replace('nan', '-').replace('_', '-')
                })

    print(f" [OK] Extraídos {len(dilution_data)} padrões.")

    # Atualizar Banco
    print("Atualizando Banco de Dados...")
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
        
        # A. Mapa Manual
        for k_excel, k_db in manual_map.items():
            if normalize(k_db) == db_norm:
                match = next((d for d in dilution_data if normalize(k_excel) == d['norm_name']), None)
                break
        
        # B. Match Exato
        if not match:
            match = next((d for d in dilution_data if d['norm_name'] == db_norm), None)
            
        # C. Match Parcial
        if not match:
            match = next((d for d in dilution_data if db_norm in d['norm_name'] or d['norm_name'] in db_norm), None)

        if match:
            s = match['soro']
            v = match['vol']
            if (s != '-' and s != '') or (v != '-' and v != ''):
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", (s, v, mid))
                count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} medicamentos atualizados.")
    print("-" * 30)

if __name__ == '__main__':
    run()
