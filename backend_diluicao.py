import pandas as pd
import sqlite3
import glob
import os

db_file = "farmacia_clinica.db"

def find_excel_file():
    # Procura qualquer Excel na pasta
    files = glob.glob("*.xlsx")
    return files[0] if files else None

def clean_text(val):
    if pd.isna(val) or str(val).strip() in ['_', '-', '', 'nan', 'NAN']: return None
    return str(val).replace('\n', ' ').strip()

def run():
    print("--- MOTOR 8: PADRONIZAÇÃO DE DILUIÇÕES ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Nenhuma planilha Excel encontrada.")
        return

    print(f"Lendo: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        # Tenta achar a aba correta
        target_sheet = next((s for s in xls.sheet_names if "PADRONIZA" in s.upper() and "DILUI" in s.upper()), None)
        
        if not target_sheet:
            print("[ERRO] Aba 'Padronização de Diluições' não encontrada.")
            return

        df = pd.read_excel(xls, sheet_name=target_sheet)
        print(f"Processando aba: {target_sheet}")
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # Lógica para ler colunas duplas (Medicamento | Soro | Volume ... Medicamento | Soro | Volume)
    # A planilha tem blocos lado a lado. Vamos unificar.
    all_data = []
    
    # Índices das colunas que contêm "MEDICAMENTO"
    med_cols_indices = [i for i, col in enumerate(df.columns) if "MEDICAMENTO" in str(col).upper()]
    
    for idx in med_cols_indices:
        # Pega o bloco de 3 colunas: Med, Soro, Volume
        if idx + 2 < len(df.columns):
            sub_df = df.iloc[:, idx:idx+3]
            sub_df.columns = ['med', 'soro', 'vol']
            all_data.append(sub_df)
    
    if not all_data:
        # Tenta fallback se não achou estrutura dupla
        if 'MEDICAMENTO' in df.columns and 'VOLUME PARA ADULTOS' in df.columns:
             all_data.append(df[['MEDICAMENTO', 'SORO', 'VOLUME PARA ADULTOS']].rename(columns={'MEDICAMENTO':'med', 'SORO':'soro', 'VOLUME PARA ADULTOS':'vol'}))

    final_df = pd.concat(all_data, ignore_index=True)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Cria colunas se não existirem
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_diluent TEXT DEFAULT '-'")
    except: pass
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN std_volume TEXT DEFAULT '-'")
    except: pass

    count = 0
    for _, row in final_df.iterrows():
        raw_name = clean_text(row['med'])
        if not raw_name or 'MEDICAMENTO' in raw_name.upper(): continue
        
        # Nome para busca (Capitalizado)
        search_name = raw_name.capitalize()
        
        diluent = clean_text(row['soro']) or '-'
        volume = clean_text(row['vol']) or '-'
        
        # Atualiza no banco
        # Usa LIKE para flexibilidade (ex: "Paclitaxel" acha "Paclitaxel")
        cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE name LIKE ?", (diluent, volume, f"{search_name}%"))
        if cursor.rowcount > 0:
            count += 1

    conn.commit()
    conn.close()
    print(f"SUCESSO: {count} padrões de diluição atualizados.")

if __name__ == '__main__':
    run()
