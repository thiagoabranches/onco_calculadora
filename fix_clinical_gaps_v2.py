import pandas as pd
import sqlite3
import glob
import os
import re

db_file = "farmacia_clinica.db"

def find_excel_file():
    files = glob.glob("*PAMC*.xlsx")
    if not files: files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '', 'nan']: return ""
    return str(val).strip().replace('\n', '<br>')

def run():
    print("--- DIAGNOSTICO E CORRECAO CLINICA (V2) ---")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. Ler Excel
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha nao encontrada.")
        return

    print(f"Lendo planilha: {excel_file}")
    try:
        xls = pd.ExcelFile(excel_file)
        target_sheet = next((s for s in xls.sheet_names if "PAMC" in s.upper()), None)
        if not target_sheet: target_sheet = xls.sheet_names[0]
            
        print(f"Processando aba: '{target_sheet}'...")
        df = pd.read_excel(xls, sheet_name=target_sheet, header=None)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # 2. Lógica de Cascata
    current_drug_db_name = None
    updates = 0  # Variável corrigida
    
    # Encontrar onde começam os dados
    start_row = 0
    for idx, row in df.iterrows():
        if 'Fármaco' in str(row[0]) or 'Farmaco' in str(row[0]):
            start_row = idx + 1
            break
            
    print(f"Iniciando leitura na linha {start_row}...")

    for idx in range(start_row, len(df)):
        row = df.iloc[idx]
        
        col_a = str(row[0]).strip() if not pd.isna(row[0]) else ""
        col_b = str(row[1]).strip() if not pd.isna(row[1]) else "" # Label
        col_c = str(row[2]).strip() if not pd.isna(row[2]) else "" # Conteúdo
        
        # Se Coluna A tem texto, é um novo medicamento
        if col_a and len(col_a) > 2 and col_a.lower() != 'nan':
            search_name = col_a.split('\n')[0].strip()
            
            # Busca no banco para garantir que existe e pegar o nome correto
            cursor.execute("SELECT name FROM medicamentos WHERE name LIKE ?", (f"{search_name}%",))
            res = cursor.fetchone()
            
            if res:
                current_drug_db_name = res[0]
            else:
                # Tenta busca exata capitalizada
                cursor.execute("SELECT name FROM medicamentos WHERE name = ?", (search_name.capitalize(),))
                res2 = cursor.fetchone()
                if res2:
                    current_drug_db_name = res2[0]
                else:
                    current_drug_db_name = None
        
        # Se estamos "dentro" de um medicamento, olha as linhas de baixo
        elif current_drug_db_name:
            label = col_b.lower()
            content = clean_text(col_c)
            
            target_col = None
            
            if 'toxicidade' in label or 'efeitos' in label:
                target_col = 'toxicity'
            elif 'assist' in label and 'enfermagem' in label:
                target_col = 'nursing_care'
            elif 'particularidade' in label:
                target_col = 'particularities'
            
            if target_col and len(content) > 5:
                try:
                    cursor.execute(f"UPDATE medicamentos SET {target_col} = ? WHERE name = ?", (content, current_drug_db_name))
                    updates += 1
                except Exception as e:
                    print(f"Erro ao gravar: {e}")

    conn.commit()
    
    # Diagnóstico Final
    cursor.execute("SELECT count(*) FROM medicamentos WHERE toxicity != '' AND toxicity IS NOT NULL")
    filled_tox = cursor.fetchone()[0]
    
    conn.close()
    
    print("-" * 30)
    print(f"RESUMO:")
    print(f" - Campos atualizados: {updates}")
    print(f" - Medicamentos com Toxicidade preenchida: {filled_tox}")
    print("-" * 30)

if __name__ == '__main__':
    run()
