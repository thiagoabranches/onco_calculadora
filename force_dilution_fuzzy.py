import pandas as pd
import sqlite3
import unicodedata
import os
import glob
from difflib import SequenceMatcher

db_file = "farmacia_clinica.db"

# MAPA MANUAL (Para o que for muito diferente)
manual_map = {
    "ALFAINTERFERONA": "Alfapeginterferona 2a",
    "ALFAINTERFERONA 2B": "Alfapeginterferona 2a", 
    "ABRAXANE": "Nab-paclitaxel",
    "PACLITAXEL (ABRAXANE)": "Nab-paclitaxel",
    "HERCEPTIN": "Trastuzumabe",
    "MABTHERA": "Rituximabe",
    "AVASTIN": "Bevacizumabe",
    "ERBITUX": "Cetuximabe",
    "VECTIBIX": "Panitumumabe",
    "KEYTRUDA": "Pembrolizumabe",
    "OPDIVO": "Nivolumabe",
    "YERVOY": "Ipilimumabe",
    "PERJETA": "Pertuzumabe",
    "DARZALEX": "Daratumumab",
    "KYPROLIS": "Carfilzomib",
    "VELCADE": "Bortezomibe",
    "JEVTANA": "Cabazitaxel",
    "TAXOTERE": "Docetaxel",
    "NAVELBINE": "Vinorelbina",
    "GEMZAR": "Gencitabina",
    "ALIMTA": "Pemetrexede",
    "VIDAZA": "Azacitidina",
    "DACOGEN": "Decitabina"
}

def normalize(text):
    if not isinstance(text, str): return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().strip()

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_excel():
    files = glob.glob("*.xlsx")
    return files[0] if files else None

def run():
    print("--- MOTOR DE CORREÇÃO INTELIGENTE (FUZZY MATCH) ---")
    
    excel_file = find_excel()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    # 1. Ler Excel
    try:
        xls = pd.ExcelFile(excel_file)
        target_sheet = next((s for s in xls.sheet_names if "PADRONIZA" in s.upper() or "DILUI" in s.upper()), None)
        if not target_sheet:
            print("[ERRO] Aba de Padronização não encontrada.")
            return
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # 2. Extrair Lista de Padronização
    std_list = []
    blocks = [(0, 1, 2), (5, 6, 7)] # Colunas A,B,C e F,G,H
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            for _, row in sub.iterrows():
                n = str(row['nome'])
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                s = str(row['soro']).strip().replace('nan', '-')
                v = str(row['vol']).strip().replace('nan', '-')
                
                if s != '-' or v != '-':
                    std_list.append({
                        'raw': n,
                        'norm': normalize(n),
                        'soro': s,
                        'vol': v
                    })

    print(f"Lidos {len(std_list)} padrões da planilha.")

    # 3. Varrer Banco e Casar Dados
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, std_diluent, std_volume FROM medicamentos")
    rows = cursor.fetchall()
    
    updates = 0
    
    for r in rows:
        mid = r[0]
        db_name = r[1]
        current_dil = r[2]
        
        # Só tenta corrigir se estiver vazio ou inválido
        if not current_dil or current_dil == '-' or current_dil == 'nan':
            db_norm = normalize(db_name)
            best_match = None
            best_score = 0
            
            # A. Tenta Mapa Manual Primeiro (Marcas)
            for k_csv, k_db in manual_map.items():
                if normalize(k_db) == db_norm:
                    # Tenta achar k_csv na lista std
                    for item in std_list:
                        if normalize(k_csv) in item['norm']:
                            best_match = item
                            best_score = 1.0
                            break
                if best_match: break
            
            # B. Se não achou, vai por Similaridade
            if not best_match:
                for item in std_list:
                    # Score de similaridade (0 a 1)
                    score = similar(db_norm, item['norm'])
                    
                    # Bonus se um contém o outro (ex: "Paclitaxel" in "Paclitaxel 100mg")
                    if db_norm in item['norm'] or item['norm'] in db_norm:
                        score += 0.3
                    
                    if score > best_score:
                        best_score = score
                        best_match = item
            
            # C. Aplica se a confiança for alta (> 0.6)
            if best_match and best_score > 0.6:
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", 
                               (best_match['soro'], best_match['vol'], mid))
                updates += 1
                # print(f" [FIX] {db_name} <== {best_match['raw']} (Score: {best_score:.2f})")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {updates} medicamentos corrigidos via Inteligência de Texto.")
    print("-" * 30)

if __name__ == '__main__':
    run()
