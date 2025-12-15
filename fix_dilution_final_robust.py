import pandas as pd
import sqlite3
import re
import unicodedata
import os
import glob

db_file = "farmacia_clinica.db"

# MAPA MANUAL PARA NOMES DIFICEIS
manual_map = {
    "ALFAINTERFERONA 2B RECOMBINANTE": "Alfapeginterferona 2a",
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
    "TRASTUZUMABE ENTANSINA": "Trastuzumabe entansina"
}

def find_dilution_csv():
    # Procura arquivo que tenha 'Padroniza' e termine em .csv
    files = glob.glob("*Padroniza*.csv")
    if not files:
        # Tenta achar qualquer CSV que tenha 'Dilui' no nome
        files = glob.glob("*Dilui*.csv")
    return files[0] if files else None

def normalize(text):
    if not isinstance(text, str): return ""
    # Remove acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().strip()

def run():
    print("--- CORRIGINDO LACUNAS DE DILUIÇÃO (ROBUSTO) ---")
    
    # 1. Achar arquivo
    target_file = find_dilution_csv()
    if not target_file:
        print("[ERRO] Arquivo de Padronização não encontrado.")
        print("Certifique-se que o arquivo '.csv' com 'Padronização' no nome está na pasta.")
        return

    print(f"Lendo arquivo: {target_file}")
    try:
        df = pd.read_csv(target_file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV: {e}")
        return

    # 2. Extrair dados (colunas duplas)
    dilution_data = []
    
    # Índices típicos onde os dados estão (A=0, B=1, C=2) e (F=5, G=6, H=7)
    blocks = [(0, 1, 2), (5, 6, 7)]
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            
            for _, row in sub.iterrows():
                n = str(row['nome'])
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                # Guarda dados
                dilution_data.append({
                    'raw_name': n.strip(),
                    'norm_name': normalize(n),
                    'soro': str(row['soro']).strip(),
                    'vol': str(row['vol']).strip()
                })

    print(f"Encontrados {len(dilution_data)} padrões na planilha.")

    # 3. Atualizar Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM medicamentos")
    db_meds = cursor.fetchall()
    
    count = 0
    for med in db_meds:
        mid = med[0]
        db_name = med[1]
        db_norm = normalize(db_name)
        
        match = None
        
        # A. Tentativa Manual (Mapa)
        for k_csv, k_db in manual_map.items():
            if normalize(k_db) == db_norm:
                # Procura a chave do CSV na lista de dados
                match = next((d for d in dilution_data if normalize(k_csv) == d['norm_name']), None)
                break
        
        # B. Tentativa Automática (Nome exato)
        if not match:
            match = next((d for d in dilution_data if d['norm_name'] == db_norm), None)
            
        # C. Tentativa Parcial (Contém)
        if not match:
            match = next((d for d in dilution_data if db_norm in d['norm_name'] or d['norm_name'] in db_norm), None)

        if match:
            s = match['soro'].replace('nan', '-').replace('_', '-')
            v = match['vol'].replace('nan', '-').replace('_', '-')
            
            if s != '-' and s != '' and v != '-' and v != '':
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", (s, v, mid))
                count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} medicamentos atualizados com dados de diluição.")
    print("-" * 30)

if __name__ == '__main__':
    run()
