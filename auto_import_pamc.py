import pandas as pd
import sqlite3
import re
import os
import glob

# CONFIGURAÇÃO
target_name = "dados_pamc.csv"
db_file = "farmacia_clinica.db"

def find_and_rename_csv():
    # Procura qualquer arquivo que termine em .csv e tenha "PAMC" no nome
    files = glob.glob("*PAMC*.csv")
    
    if not files:
        # Tenta procurar qualquer CSV se não achar com PAMC
        files = glob.glob("*.csv")
    
    if not files:
        print("[ERRO] Nenhum arquivo CSV encontrado na pasta.")
        return False

    # Pega o primeiro encontrado
    found_file = files[0]
    print(f"Arquivo encontrado: '{found_file}'")
    
    if found_file != target_name:
        try:
            os.rename(found_file, target_name)
            print(f"Renomeado para: '{target_name}'")
        except Exception as e:
            print(f"[AVISO] Não foi possível renomear (pode estar aberto): {e}")
            # Se não der pra renomear, tenta ler o original mesmo
            return found_file
            
    return target_name

def clean_text(text):
    if pd.isna(text): return "-"
    text = str(text).replace('\n', ' ').replace('\r', '')
    text = text.replace('®', '') 
    return text.strip()

def parse_range(text):
    """Lê '0,6-8mg/ml' e retorna (0.6, 8.0)"""
    if pd.isna(text) or text == '-': return 0.0, 0.0
    text = str(text).lower().replace(',', '.')
    
    # Padrão '0.6-8'
    match = re.findall(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', text)
    if match:
        return float(match[0][0]), float(match[0][1])
    
    # Padrão único '5.0'
    match_single = re.findall(r'(\d+\.?\d*)', text)
    if match_single:
        val = float(match_single[0])
        return val, val
    return 0.0, 0.0

def parse_diluents(text):
    """Lê 'SF\nSG' e retorna Sim/Não"""
    if pd.isna(text): return "-", "-"
    text = str(text).upper()
    sf = "Sim" if "SF" in text or "0,9%" in text else "Não"
    sg = "Sim" if "SG" in text or "5%" in text else "Não"
    if "NÃO DILUIR" in text: return "Não", "Não"
    return sg, sf

def run():
    print("--- INICIANDO AUTO-IMPORTAÇÃO (PAMC 2025) ---")
    
    # 1. Encontrar o arquivo certo
    csv_to_read = find_and_rename_csv()
    if not csv_to_read: return

    # 2. Ler CSV
    try:
        df = pd.read_csv(csv_to_read)
        # Filtra linhas válidas
        df_meds = df[df['Fármaco'].notna()].copy()
        print(f"Processando {len(df_meds)} registros da planilha...")
    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV: {e}")
        return

    # 3. Preparar Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Resetar Tabela para garantir pureza dos dados
    cursor.execute("DROP TABLE IF EXISTS medicamentos")
    cursor.execute('''
        CREATE TABLE medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand_name TEXT,
            category TEXT DEFAULT 'Geral',
            concentration TEXT,
            concentration_display TEXT,
            has_multiple_presentations INTEGER DEFAULT 0,
            concMin REAL DEFAULT 0,
            concMax REAL DEFAULT 0,
            sg5 TEXT DEFAULT '-',
            sf09 TEXT DEFAULT '-',
            observations TEXT DEFAULT '',
            stability_reconst TEXT,
            stability_diluted TEXT,
            filter_req TEXT
        )
    ''')

    count = 0
    for _, row in df_meds.iterrows():
        # Ignora cabeçalhos repetidos no meio da planilha
        raw_name = clean_text(row['Fármaco'])
        if not raw_name or raw_name == '_' or 'Fármaco' in raw_name: continue
        
        name = raw_name.capitalize()
        brand = clean_text(row['Nome Comercial'])
        presentation = clean_text(row['Apresentação'])
        
        # Parse Faixa
        c_min, c_max = parse_range(row['[ ] máx. de adm.'])
        
        # Parse Diluentes
        sg, sf = parse_diluents(row['Diluentes'])
        
        # Parse Observações (Junta Filtro + Incomp + Estabilidade)
        obs_parts = []
        filtro = clean_text(row.get('Filtro', ''))
        if filtro and filtro.lower() not in ['-', '_', 'nao', 'não', 'nan']:
            obs_parts.append(f"Filtro: {filtro}")
            
        incomp = clean_text(row.get('Incompatibilidade', ''))
        if incomp and incomp.lower() not in ['-', '_', 'nan']:
            obs_parts.append(f"Incomp: {incomp}")
            
        fotossens = clean_text(row.get('Fotossensibilidade', ''))
        if fotossens and 'sim' in fotossens.lower():
            obs_parts.append("Fotossensível")
            
        observations = " | ".join(obs_parts)
        
        stab_rec = clean_text(row.get('Estab. após reconstituído ou frasco aberto', '-'))
        stab_dil = clean_text(row.get('Estab. após diluição', '-'))

        # Lógica Multi
        is_multi = 1 if ('\n' in presentation or '/' in presentation and len(presentation) > 25) else 0
        
        # Categoria Simples
        category = "Geral"
        n_low = name.lower()
        if "mab" in n_low: category = "Anticorpos Monoclonais"
        elif "ib" in n_low: category = "Inibidores"
        elif "platina" in n_low: category = "Platinas"
        elif "taxel" in n_low: category = "Taxanos"
        
        cursor.execute('''
            INSERT INTO medicamentos (
                name, brand_name, concentration, concentration_display, 
                has_multiple_presentations, concMin, concMax, sg5, sf09,
                observations, stability_reconst, stability_diluted, category, filter_req
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, brand, presentation, presentation, 
            is_multi, c_min, c_max, sg, sf, 
            observations, stab_rec, stab_dil, category, filtro
        ))
        count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: Banco reconstruído com {count} medicamentos.")
    print("-" * 30)

if __name__ == '__main__':
    run()
