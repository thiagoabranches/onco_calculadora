import pandas as pd
import sqlite3
import re
import os
import glob

# CONFIGURAÇÃO
db_file = "farmacia_clinica.db"

def find_excel_file():
    # Procura arquivos .xlsx com 'PAMC' no nome
    files = glob.glob("*PAMC*.xlsx")
    if not files:
        # Tenta qualquer xlsx se não achar específico
        files = glob.glob("*.xlsx")
    
    if not files: return None
    return files[0]

def clean_text(val):
    if pd.isna(val): return "-"
    text = str(val).replace('\n', ' ').replace('\r', '')
    # Remove caracteres de marca registrada para limpeza
    text = text.replace('®', '').replace('™', '')
    return text.strip()

def parse_range(text):
    """Extrai intervalo de '0,6-8mg/ml'"""
    if pd.isna(text) or str(text).strip() == '-': return 0.0, 0.0
    text = str(text).lower().replace(',', '.')
    
    # Padrão intervalo "num - num"
    match = re.findall(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', text)
    if match: return float(match[0][0]), float(match[0][1])
    
    # Padrão único (assume como máximo)
    match_single = re.findall(r'(\d+\.?\d*)', text)
    if match_single:
        val = float(match_single[0])
        return val, val
    return 0.0, 0.0

def parse_diluents(text):
    """Interpreta 'SF / SG'"""
    if pd.isna(text): return "-", "-"
    t = str(text).upper()
    
    sf = "Sim" if "SF" in t or "0,9" in t or "CLORETO" in t else "Não"
    sg = "Sim" if "SG" in t or "GLICOSE" in t or "5%" in t else "Não"
    
    if "NÃO DILUIR" in t or "PROIBIDO" in t:
        if "SF" in t: sf = "Não"
        if "SG" in t: sg = "Não"
        
    return sg, sf

def run():
    print("--- MOTOR DE IMPORTAÇÃO EXCEL (PAMC 2025) ---")
    
    excel_file = find_excel_file()
    if not excel_file:
        print("[ERRO] Nenhum arquivo .xlsx encontrado na pasta.")
        return

    print(f"Arquivo encontrado: '{excel_file}'")
    print("Lendo planilha... (Isso pode levar alguns segundos)")
    
    try:
        # Lê todas as abas para encontrar a certa
        xls = pd.ExcelFile(excel_file)
        target_sheet = None
        
        for sheet_name in xls.sheet_names:
            df_temp = pd.read_excel(xls, sheet_name=sheet_name, nrows=5)
            # Verifica se tem a coluna chave 'Fármaco'
            if 'Fármaco' in df_temp.columns or 'Farmaco' in df_temp.columns:
                target_sheet = sheet_name
                break
        
        if not target_sheet:
            print("[ERRO] Não encontrei a aba com a coluna 'Fármaco' no Excel.")
            return
            
        print(f"Importando da aba: '{target_sheet}'")
        df = pd.read_excel(xls, sheet_name=target_sheet)
        
        # Ajusta nome da coluna se tiver acento ou não
        col_farmaco = 'Fármaco' if 'Fármaco' in df.columns else 'Farmaco'
        
        # Filtra apenas linhas com medicamentos
        df_meds = df[df[col_farmaco].notna()].copy()
        print(f"Processando {len(df_meds)} registros...")

    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao ler Excel: {e}")
        return

    # Conecta ao Banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # RECONSTRUÇÃO TOTAL DA TABELA (Para garantir a estrutura da PAMC)
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
        raw_name = clean_text(row.get(col_farmaco))
        
        # Pula linhas de cabeçalho ou lixo
        if not raw_name or raw_name == '_' or 'Toxicidade' in raw_name: continue
        
        name = raw_name.capitalize()
        brand = clean_text(row.get('Nome Comercial', '-'))
        presentation = clean_text(row.get('Apresentação', '-'))
        
        # Coluna de Faixa (Ajuste o nome conforme sua planilha exata)
        # O print anterior mostrou '[ ] máx. de adm.'
        col_faixa = '[ ] máx. de adm.'
        if col_faixa not in df.columns: 
             # Tenta achar coluna parecida
             cols = [c for c in df.columns if 'max' in str(c).lower() or 'adm' in str(c).lower()]
             if cols: col_faixa = cols[0]

        c_min, c_max = parse_range(row.get(col_faixa, ''))
        
        # Diluentes
        sg, sf = parse_diluents(row.get('Diluentes', ''))
        
        # Observações Ricas
        obs_parts = []
        
        filtro = clean_text(row.get('Filtro', ''))
        if filtro and filtro.lower() not in ['-', '_', 'nao', 'não', 'nan']:
            obs_parts.append(f"Filtro: {filtro}")
            
        incomp = clean_text(row.get('Incompatibilidade', ''))
        if incomp and incomp.lower() not in ['-', '_', 'nan']:
            obs_parts.append(f"Incomp: {incomp}")
            
        fotossens = clean_text(row.get('Fotossensibilidade', ''))
        if 'sim' in str(fotossens).lower():
            obs_parts.append("Fotossensível")
            
        final_obs = " | ".join(obs_parts)
        
        # Estabilidade
        stab_rec = clean_text(row.get('Estab. após reconstituído ou frasco aberto', '-'))
        stab_dil = clean_text(row.get('Estab. após diluição', '-'))

        # Lógica Multi (Se a apresentação for texto longo ou tiver pipe)
        is_multi = 1 if (len(presentation) > 30 or '\n' in presentation) else 0
        
        # Categoria Automática
        cat = "Geral"
        n_low = name.lower()
        if "mab" in n_low: cat = "Anticorpos Monoclonais"
        elif "ib" in n_low: cat = "Inibidores"
        elif "platina" in n_low: cat = "Platinas"
        elif "taxel" in n_low: cat = "Taxanos"
        
        cursor.execute('''
            INSERT INTO medicamentos (
                name, brand_name, concentration, concentration_display, 
                has_multiple_presentations, concMin, concMax, sg5, sf09,
                observations, stability_reconst, stability_diluted, category, filter_req
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, brand, presentation, presentation, 
            is_multi, c_min, c_max, sg, sf, 
            final_obs, stab_rec, stab_dil, cat, filtro
        ))
        count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: Banco populado com {count} registros da PAMC 2025.")
    print("-" * 30)

if __name__ == '__main__':
    run()
