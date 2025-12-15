import pandas as pd
import sqlite3
import glob
import os
import unicodedata
import re

db_file = "farmacia_clinica.db"

def normalize_key(text):
    """Remove acentos, espaços, hífens e deixa minúsculo para comparação"""
    if not isinstance(text, str): return ""
    # Normaliza unicode (remove acentos)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Remove tudo que não for letra ou número
    text = re.sub(r'[^a-z0-9]', '', text.lower())
    return text

def find_excel_file():
    files = glob.glob("*.xlsx")
    return files[0] if files else None

def run():
    print("--- CORREÇÃO DE LACUNAS DE DILUIÇÃO (MATCH AVANÇADO) ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    # 1. Carregar Dados da Planilha
    try:
        xls = pd.ExcelFile(excel_file)
        target_sheet = next((s for s in xls.sheet_names if "PADRONIZA" in s.upper()), None)
        if not target_sheet:
            print("[ERRO] Aba de Padronização não encontrada.")
            return
        
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # 2. Processar a estrutura de colunas duplas da planilha
    # Cria um dicionário: { "nome_normalizado": {"soro": "...", "vol": "..."} }
    dilution_map = {}
    
    # Identifica colunas de medicamento
    med_cols_indices = [i for i, col in enumerate(df.columns) if "MEDICAMENTO" in str(col).upper()]
    
    # Se não achou pelo cabeçalho, tenta índices fixos (A, E...)
    if not med_cols_indices:
        med_cols_indices = [0, 5] # Chute comum para layout lado a lado

    print("Mapeando dados da planilha...")
    for idx in med_cols_indices:
        if idx + 2 < len(df.columns):
            # Itera linhas dessa seção
            for _, row in df.iloc[:, idx:idx+3].iterrows():
                raw_name = str(row.iloc[0])
                if pd.isna(row.iloc[0]) or 'MEDICAMENTO' in raw_name.upper(): continue
                
                key = normalize_key(raw_name)
                if not key: continue
                
                soro = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else "-"
                vol = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else "-"
                
                # Guarda no mapa
                dilution_map[key] = {'soro': soro, 'vol': vol}

    # 3. Atualizar o Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, std_volume FROM medicamentos")
    rows = cursor.fetchall()
    
    count_updates = 0
    
    print(f"Verificando {len(rows)} medicamentos no banco...")
    
    for r in rows:
        mid = r[0]
        db_name = r[1]
        current_vol = r[2]
        
        # Só tenta corrigir se estiver vazio ou com traço
        if not current_vol or current_vol == '-' or current_vol == 'nan':
            db_key = normalize_key(db_name)
            
            # Tenta encontrar correspondência exata na chave normalizada
            match = dilution_map.get(db_key)
            
            # Se não achou exato, tenta parcial (ex: "doxorrubicinalipossomal" in "doxorrubicina")
            if not match:
                for k, v in dilution_map.items():
                    if k in db_key or db_key in k:
                        # Evita falsos positivos curtos
                        if len(k) > 4:
                            match = v
                            break
            
            if match:
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", 
                               (match['soro'], match['vol'], mid))
                print(f" [FIX] {db_name} -> {match['soro']} {match['vol']}")
                count_updates += 1
            else:
                # Opcional: Avisar o que não achou para diagnóstico
                # print(f" [MISS] {db_name} não encontrado na padronização.")
                pass

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count_updates} medicamentos corrigidos com inteligência de texto.")
    print("-" * 30)

if __name__ == '__main__':
    run()
