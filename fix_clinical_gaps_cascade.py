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
    # Preserva quebras de linha para o HTML
    text = str(val).strip().replace('\n', '<br>')
    return text

def normalize_name(name):
    if not name: return ""
    return str(name).strip().capitalize()

def run():
    print("--- DIAGNÓSTICO E CORREÇÃO CLÍNICA (CASCATA) ---")
    
    # 1. Diagnóstico Inicial
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Conta quantos estão vazios
    cursor.execute("SELECT count(*) FROM medicamentos WHERE toxicity = '' OR toxicity IS NULL")
    empty_tox = cursor.fetchone()[0]
    print(f" [DIAGNÓSTICO] Medicamentos sem dados de Toxicidade: {empty_tox}")
    
    # 2. Ler Excel
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Planilha não encontrada.")
        return

    print(f"Lendo planilha: {excel_file}")
    try:
        xls = pd.ExcelFile(excel_file)
        # Procura aba principal (PAMC)
        target_sheet = next((s for s in xls.sheet_names if "PAMC" in s.upper()), None)
        if not target_sheet: 
            # Fallback: primeira aba
            target_sheet = xls.sheet_names[0]
            
        print(f"Processando aba: '{target_sheet}'...")
        # Lê sem cabeçalho para pegar tudo pela posição (A, B, C)
        df = pd.read_excel(xls, sheet_name=target_sheet, header=None)
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # 3. Lógica de Cascata (Varredura Vertical)
    current_drug_db_name = None
    updates_count = 0
    
    # Mapear índices das colunas (A=0: Fármaco, B=1: Label, C=2: Conteúdo)
    # Às vezes o conteúdo está mesclado, vamos checar colunas 1 e 2
    
    # Encontrar a linha de cabeçalho real para começar a processar DEPOIS dela
    start_row = 0
    for idx, row in df.iterrows():
        # Se a primeira coluna tem "Fármaco", é o cabeçalho
        if 'Fármaco' in str(row[0]) or 'Farmaco' in str(row[0]):
            start_row = idx + 1
            break
            
    print(f"Iniciando varredura na linha {start_row}...")

    for idx in range(start_row, len(df)):
        row = df.iloc[idx]
        
        col_a = str(row[0]).strip() if not pd.isna(row[0]) else ""
        col_b = str(row[1]).strip() if not pd.isna(row[1]) else ""
        col_c = str(row[2]).strip() if not pd.isna(row[2]) else "" # Conteúdo principal costuma estar na C
        
        # Se tem algo na Coluna A que não seja lixo, é um NOVO medicamento
        if col_a and len(col_a) > 2 and col_a.lower() != 'nan':
            # Tenta achar esse medicamento no banco para ter o ID/Nome correto
            search_name = col_a.split('\n')[0].strip() # Pega primeira linha se tiver quebra
            
            # Busca flexível no banco
            cursor.execute("SELECT name FROM medicamentos WHERE name LIKE ?", (f"{search_name}%",))
            res = cursor.fetchone()
            
            if res:
                current_drug_db_name = res[0]
                # print(f" > Foco: {current_drug_db_name}")
            else:
                # Tenta normalizar capitalizando
                cursor.execute("SELECT name FROM medicamentos WHERE name = ?", (search_name.capitalize(),))
                res2 = cursor.fetchone()
                if res2:
                    current_drug_db_name = res2[0]
                else:
                    current_drug_db_name = None # Não achou no banco, ignora linhas seguintes
        
        # Se temos um medicamento em foco, procuramos as linhas de detalhe (Col B ou A vazia)
        elif current_drug_db_name:
            # Analisa Coluna B (Labels: Toxicidade, Assistência...)
            label = col_b.lower()
            content = clean_text(col_c)
            
            # Se conteúdo estiver vazio na C, as vezes está na B junto com o label?
            # Na sua planilha, parece estar separado. B=Label, C=Content.
            
            target_col = None
            
            if 'toxicidade' in label or 'efeitos' in label:
                target_col = 'toxicity'
            elif 'assist' in label and 'enfermagem' in label:
                target_col = 'nursing_care'
            elif 'particularidade' in label:
                target_col = 'particularities'
            
            if target_col and len(content) > 5:
                # Atualiza o banco
                try:
                    cursor.execute(f"UPDATE medicamentos SET {target_col} = ? WHERE name = ?", (content, current_drug_db_name))
                    updates += 1
                    # print(f"   + Atualizado {target_col} para {current_drug_db_name}")
                except Exception as e:
                    print(f"Erro ao gravar: {e}")

    conn.commit()
    
    # 4. Diagnóstico Final
    cursor.execute("SELECT count(*) FROM medicamentos WHERE toxicity = '' OR toxicity IS NULL")
    final_empty = cursor.fetchone()[0]
    
    conn.close()
    
    print("-" * 30)
    print(f"RESUMO DA OPERAÇÃO:")
    print(f" - Campos atualizados: {updates}")
    print(f" - Medicamentos ainda sem Toxicidade: {final_empty} (Eram {empty_tox})")
    print("-" * 30)

if __name__ == '__main__':
    run()
