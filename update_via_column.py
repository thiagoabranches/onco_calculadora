import pandas as pd
import sqlite3
import glob
import os

db_file = "farmacia_clinica.db"

def find_excel_file():
    # Procura arquivos .xlsx com 'PAMC' no nome
    files = glob.glob("*PAMC*.xlsx")
    if not files: files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '']: return "-"
    return str(val).replace('\n', ' ').strip()

def run():
    print("--- ADICIONANDO COLUNA 'VIA' (DO EXCEL) ---")
    
    # 1. Localizar e Ler Excel
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    print(f"Lendo fonte: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        # Encontra a aba certa
        target_sheet = None
        for sheet in xls.sheet_names:
            df_check = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            if 'Via' in df_check.columns and ('Fármaco' in df_check.columns or 'Farmaco' in df_check.columns):
                target_sheet = sheet
                break
        
        if not target_sheet:
            print("[ERRO] Coluna 'Via' não encontrada nas abas.")
            return

        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        print(f"[ERRO] Falha ao ler Excel: {e}")
        return

    # 2. Atualizar Banco de Dados
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Cria a coluna se não existir
    try:
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN via_admin TEXT DEFAULT '-'")
    except:
        pass # Já existe

    print("Atualizando registros...")
    
    count = 0
    # Identifica nome da coluna de farmaco (com ou sem acento)
    col_farmaco = 'Fármaco' if 'Fármaco' in df.columns else 'Farmaco'

    for _, row in df.iterrows():
        raw_name = clean_text(row.get(col_farmaco))
        if raw_name == '-' or 'Toxicidade' in raw_name: continue
        
        # Normaliza nome para busca (Capitalize)
        db_name = raw_name.capitalize()
        
        # Pega o dado da Via exatamente como está
        via_valor = clean_text(row.get('Via'))
        
        # Atualiza no banco
        cursor.execute("UPDATE medicamentos SET via_admin = ? WHERE name = ?", (via_valor, db_name))
        if cursor.rowcount > 0:
            count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: Coluna 'Via' preenchida para {count} medicamentos.")
    print("-" * 30)

if __name__ == '__main__':
    run()
