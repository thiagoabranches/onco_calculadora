import pandas as pd
import sqlite3
import re
import os

# CONFIGURAÇÃO
csv_file = "PAMC versão 06.2025 - Editado.xlsx - PAMC 2025.csv"
db_file = "farmacia_clinica.db"

def clean_text(text):
    if pd.isna(text): return "-"
    text = str(text).replace('\n', ' ').replace('\r', '')
    text = text.replace('®', '') # Remove simbolo de registro para facilitar busca
    return text.strip()

def parse_range(text):
    """Lê '0,6-8mg/ml' e retorna (0.6, 8.0)"""
    if pd.isna(text) or text == '-': return 0.0, 0.0
    text = str(text).lower().replace(',', '.')
    
    # Tenta achar padrao "num - num"
    match = re.findall(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', text)
    if match:
        return float(match[0][0]), float(match[0][1])
    
    # Tenta achar um unico numero (assumir maximo ou fixo)
    match_single = re.findall(r'(\d+\.?\d*)', text)
    if match_single:
        val = float(match_single[0])
        return val, val # Se for unico, min=max
        
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
    print("--- INICIANDO IMPORTAÇÃO DEFINITIVA (PAMC 2025) ---")
    
    # 1. Carregar CSV
    if not os.path.exists(csv_file):
        print(f"[ERRO] Arquivo '{csv_file}' não encontrado.")
        return

    df = pd.read_csv(csv_file)
    
    # 2. Filtrar linhas válidas (onde 'Fármaco' não é nulo)
    df_meds = df[df['Fármaco'].notna()].copy()
    
    print(f"Lendo {len(df_meds)} registros da planilha...")

    # 3. Preparar Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
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
        # Dados Básicos
        raw_name = clean_text(row['Fármaco'])
        if not raw_name or raw_name == '_': continue
        
        # Capitaliza nome (ex: "aflibercepte" -> "Aflibercepte")
        name = raw_name.capitalize()
        
        brand = clean_text(row['Nome Comercial'])
        presentation = clean_text(row['Apresentação'])
        
        # Faixas
        c_min, c_max = parse_range(row['[ ] máx. de adm.'])
        
        # Diluentes
        sg, sf = parse_diluents(row['Diluentes'])
        
        # Observações (Juntando Filtro + Incompatibilidade + Estabilidade)
        obs_parts = []
        filtro = clean_text(row.get('Filtro', ''))
        if filtro and filtro.lower() not in ['-', '_', 'nao', 'não']:
            obs_parts.append(f"Filtro: {filtro}")
            
        incomp = clean_text(row.get('Incompatibilidade', ''))
        if incomp and incomp not in ['-', '_']:
            obs_parts.append(f"Incomp: {incomp}")
            
        fotossens = clean_text(row.get('Fotossensibilidade', ''))
        if fotossens and 'sim' in fotossens.lower():
            obs_parts.append("Fotossensível")
            
        observations = " | ".join(obs_parts)
        
        # Estabilidade
        stab_rec = clean_text(row.get('Estab. após reconstituído ou frasco aberto', '-'))
        stab_dil = clean_text(row.get('Estab. após diluição', '-'))

        # Lógica de Múltiplas Apresentações (se tiver pipe ou newline no original)
        is_multi = 1 if ('|' in presentation or '/' in presentation and len(presentation) > 20) else 0 
        # A lógica acima é simples, pode ser refinada. Se a string for muito longa, assume menu.

        # Categorização Básica (pelo nome)
        category = "Geral"
        n_lower = name.lower()
        if "mab" in n_lower: category = "Anticorpos Monoclonais"
        elif "ib" in n_lower: category = "Inibidores"
        elif "platina" in n_lower: category = "Platinas"
        elif "taxel" in n_lower: category = "Taxanos"
        
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
    print(f"SUCESSO: Banco recriado com {count} medicamentos da planilha oficial.")
    print("-" * 30)

if __name__ == '__main__':
    run()
