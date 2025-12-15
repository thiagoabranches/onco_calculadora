import pandas as pd
import sqlite3
import unicodedata
import os

# CONFIGURAÇÃO
safe_filename = "padronizacao_final.csv"
db_file = "farmacia_clinica.db"

# MAPA MANUAL (Nomes Planilha -> Nomes Banco)
manual_map = {
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
    "RITUXIMABE (MABTHERA)": "Rituximabe",
    "TRASTUZUMABE DERUXTECANA": "Trastuzumabe deruxtecan",
    "TRASTUZUMABE ENTANSINA": "Trastuzumabe entansina"
}

def normalize(text):
    if not isinstance(text, str): return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().strip()

def find_and_rename():
    print("--- 1. BUSCANDO ARQUIVO DE PADRONIZAÇÃO ---")
    
    # Lista todos os arquivos da pasta
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    target = None
    
    for f in files:
        # Busca por partes do nome que não costumam mudar com erro de acento
        # "Dilui" de Diluições, "Padroniza" de Padronização
        if "Padroniza" in f or "Dilui" in f:
            if f.endswith(".csv"):
                target = f
                break
    
    if not target:
        # Se não achou pelo nome, tenta ver se já foi renomeado
        if os.path.exists(safe_filename):
            print(f" [OK] Arquivo seguro '{safe_filename}' já existe.")
            return safe_filename
        print("[ERRO] Arquivo não encontrado. Verifique se ele está na pasta.")
        return None
        
    print(f" [ENCONTRADO] '{target}'")
    
    if target != safe_filename:
        try:
            os.rename(target, safe_filename)
            print(f" [RENOMEADO] Para: '{safe_filename}' (Seguro)")
        except Exception as e:
            print(f" [ERRO] Não foi possível renomear: {e}")
            return target # Tenta usar o nome original mesmo assim
            
    return safe_filename

def run():
    # 1. Preparar Arquivo
    csv_file = find_and_rename()
    if not csv_file: return

    # 2. Ler Dados
    print("--- 2. LENDO DADOS DE DILUIÇÃO ---")
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV: {e}")
        return

    dilution_data = []
    
    # Índices das colunas duplas (A,B,C e F,G,H)
    blocks = [(0, 1, 2), (5, 6, 7)]
    
    for c_med, c_soro, c_vol in blocks:
        if c_vol < len(df.columns):
            sub = df.iloc[:, [c_med, c_soro, c_vol]].copy()
            sub.columns = ['nome', 'soro', 'vol']
            
            for _, row in sub.iterrows():
                n = str(row['nome'])
                if pd.isna(row['nome']) or 'MEDICAMENTO' in n.upper(): continue
                
                dilution_data.append({
                    'norm_name': normalize(n),
                    'soro': str(row['soro']).strip(),
                    'vol': str(row['vol']).strip()
                })

    print(f" [OK] Carregados {len(dilution_data)} padrões de diluição.")

    # 3. Atualizar Banco
    print("--- 3. APLICANDO NO BANCO DE DADOS ---")
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
        
        # A. Mapa Manual
        for k_csv, k_db in manual_map.items():
            if normalize(k_db) == db_norm:
                match = next((d for d in dilution_data if normalize(k_csv) == d['norm_name']), None)
                break
        
        # B. Match Exato
        if not match:
            match = next((d for d in dilution_data if d['norm_name'] == db_norm), None)
            
        # C. Match Parcial
        if not match:
            match = next((d for d in dilution_data if db_norm in d['norm_name'] or d['norm_name'] in db_norm), None)

        if match:
            s = match['soro'].replace('nan', '-').replace('_', '-')
            v = match['vol'].replace('nan', '-').replace('_', '-')
            
            # Só atualiza se tiver dados válidos
            if (s != '-' and s != '') or (v != '-' and v != ''):
                cursor.execute("UPDATE medicamentos SET std_diluent = ?, std_volume = ? WHERE id = ?", (s, v, mid))
                count += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO FINAL: {count} medicamentos atualizados com diluição padronizada.")
    print("-" * 30)

if __name__ == '__main__':
    run()
