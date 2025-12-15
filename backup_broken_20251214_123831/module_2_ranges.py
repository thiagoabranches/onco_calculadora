import sqlite3
import json
import re
from difflib import get_close_matches

def normalize(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def parse_range(text):
    """Extrai min e max de strings como '0.6 - 8.0 mg/mL'"""
    if not text: return 0.0, 0.0
    text = text.lower().replace(',', '.').strip()
    try:
        if '-' in text:
            parts = text.split('-')
            v1 = float(re.findall(r"[\d\.]+", parts[0])[0])
            v2 = float(re.findall(r"[\d\.]+", parts[1])[0])
            return min(v1, v2), max(v1, v2)
        
        nums = re.findall(r"[\d\.]+", text)
        if nums:
            val = float(nums[0])
            if 'max' in text or '<' in text: return 0.1, val
            return val * 0.8, val * 1.2
    except: pass
    return 0.0, 0.0

def parse_diluents(text):
    if not text: return "-", "-"
    text = text.lower()
    sg = "Sim" if "glicose" in text or "sg" in text else "Não"
    sf = "Sim" if "nacl" in text or "sf" in text or "cloreto" in text else "Não"
    
    if "proibido nacl" in text: sf = "Não"
    if "proibido glicose" in text: sg = "Não"
    
    return sg, sf

def run():
    db_file = 'farmacia_clinica.db'
    json_file = 'informacoes_principais_medicamentos.json'
    
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Carrega medicamentos existentes no banco para matching
    cursor.execute("SELECT id, name FROM medicamentos")
    db_meds = {normalize(row['name']): row['id'] for row in cursor.fetchall()}
    db_keys = list(db_meds.keys())

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"[MOTOR 2] Atualizando Faixas e Diluentes para {len(db_keys)} medicamentos...")
    
    updated = 0
    
    for item in data:
        # Tenta achar o nome no JSON
        name = item.get('farmaco') or item.get('principio_ativo') or ''
        if not name: continue
        
        # Encontra o ID correspondente no banco (Fuzzy Match Leve)
        norm_name = normalize(name)
        
        # Tenta match exato primeiro
        match_key = None
        if norm_name in db_meds:
            match_key = norm_name
        else:
            # Tenta match aproximado (ajuda com 'nabpaclitaxel' vs 'paclitaxelnab')
            matches = get_close_matches(norm_name, db_keys, n=1, cutoff=0.8)
            if matches: match_key = matches[0]
            
        if match_key:
            med_id = db_meds[match_key]
            
            # Extrai dados
            conc_range = item.get('faixa_concentracao_mg_ml') or item.get('intervalo_concentracao_infusao', '')
            c_min, c_max = parse_range(conc_range)
            
            # Diluentes
            # Tenta pegar do objeto estruturado ou do texto simples
            dil_text = item.get('diluente_padrao', '')
            if not dil_text and 'compatibilidade' in item:
                comp = item['compatibilidade']
                sg5 = "Sim" if "Compatível" in comp.get('sg_5%', '') else "Não"
                sf09 = "Sim" if "Compatível" in comp.get('sf_0.9%', '') else "Não"
            else:
                sg5, sf09 = parse_diluents(dil_text)
                
            # Estabilidade Diluído
            stab = "-"
            if 'estabilidade' in item and isinstance(item['estabilidade'], dict):
                stab = item['estabilidade'].get('diluido', '-')
            
            cursor.execute('''
                UPDATE medicamentos 
                SET concMin = ?, concMax = ?, sg5 = ?, sf09 = ?, stabilityDiluted = ?
                WHERE id = ?
            ''', (c_min, c_max, sg5, sf09, stab, med_id))
            
            updated += 1

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"[SUCESSO] Faixas e Diluentes atualizados em {updated} registros.")
    print("-" * 30)

if __name__ == '__main__':
    run()
