import pandas as pd
import sqlite3
import re
import unicodedata
import os

# CONFIGURAÇÃO
csv_diluicao = "PAMC versão 06.2025 - Editado.xlsx - Padronização de Diluições.csv"
db_file = "farmacia_clinica.db"

# DICIONÁRIO MANUAL DE CORREÇÃO (Onde o nome é muito diferente)
manual_map = {
    # "Nome na Planilha Diluição": "Nome no Banco de Dados"
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
    "RITUXIMABE (MABTHERA)": "Rituximabe"
}

def normalize(text):
    """Remove acentos, espaços extras e põe em minúsculo"""
    if not isinstance(text, str): return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().strip()

def run():
    print("--- CORRIGINDO LACUNAS DE DILUIÇÃO (FINAL) ---")
    
    # 1. Carregar CSV da Aba Padronização
    # Tenta achar o arquivo na pasta
    target_file = None
    for f in os.listdir('.'):
        if 'Padronização' in f and f.endswith('.csv'):
            target_file = f
            break
            
    if not target_file:
        print("[ERRO] CSV de Padronização não encontrado.")
        return

    print(f"Lendo: {target_file}")
    try:
        df = pd.read_csv(target_file)
    except:
        print("[ERRO] Falha ao ler CSV.")
        return

    # 2. Extrair dados (colunas duplas)
    # A planilha tem blocos: Med | Soro | Vol ... Med | Soro | Vol
    # Vamos empilhar tudo numa lista única: [ {nome, soro, vol}, ... ]
    
    dilution_data = []
    
    # Identifica pares de colunas (Nome, Soro, Volume)
    # Geralmente colunas 0,1,2 e 5,6,7
    blocks = [
        (0, 1, 2), # Primeiro bloco
        (5, 6, 7)  # Segundo bloco (se existir)
    ]
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            # Pega as colunas pelo índice
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            
            for _, row in sub.iterrows():
                n = str(row['nome'])
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                dilution_data.append({
                    'raw_name': n.strip(),
                    'norm_name': normalize(n),
                    'soro': str(row['soro']).strip(),
                    'vol': str(row['vol']).strip()
                })

    print(f"Encontrados {len(dilution_data)} padrões de diluição na planilha.")

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
        
        # Estratégia 1: Mapa Manual (Prioridade)
        for k_csv, k_db in manual_map.items():
            if k_db == db_name:
                # Procura k_csv na lista de dados
                match = next((d for d in dilution_data if normalize(k_csv) == d['norm_name']), None)
                break
        
        # Estratégia 2: Match Exato Normalizado
        if not match:
            match = next((d for d in dilution_data if d['norm_name'] == db_norm), None)
            
        # Estratégia 3: Contém (ex: "Paclitaxel" in "Paclitaxel (Taxol)")
        if not match:
            match = next((d for d in dilution_data if db_norm in d['norm_name'] or d['norm_name'] in db_norm), None)

        if match:
            # Limpeza final dos valores
            s = match['soro'].replace('nan', '-').replace('_', '-')
            v = match['vol'].replace('nan', '-').replace('_', '-')
            
            if s != '-' or v != '-':
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", (s, v, mid))
                count += 1
                # print(f" [FIX] {db_name}: {s} {v}")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} lacunas preenchidas com dados da planilha.")
    print("-" * 30)

if __name__ == '__main__':
    run()
