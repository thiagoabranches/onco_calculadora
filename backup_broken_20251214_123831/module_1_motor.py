import sqlite3
import json
import os
import re

def normalize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def run():
    db_file = 'farmacia_clinica.db'
    json_file = 'informacoes_principais_medicamentos.json'

    # 1. Resetar Tabela
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS medicamentos")
    cursor.execute('''
        CREATE TABLE medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            presentations TEXT,
            concentration_display TEXT,
            has_multiple_presentations INTEGER DEFAULT 0,
            
            concMin REAL DEFAULT 0, concMax REAL DEFAULT 0,
            sg5 TEXT DEFAULT '-', sf09 TEXT DEFAULT '-',
            stabilityDiluted TEXT DEFAULT '-', stabilityExtendedRF TEXT DEFAULT '-',
            specialGroups TEXT DEFAULT '-', specialCalculator TEXT DEFAULT '',
            diluentVolume REAL DEFAULT 0, concentracaoPadrao REAL DEFAULT 0
        )
    ''')

    # 2. Ler JSON
    if not os.path.exists(json_file):
        print(f"ERRO: {json_file} nao encontrado.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Lendo {len(data)} itens do arquivo JSON...")
    
    multi_count = 0
    single_count = 0

    for item in data:
        # Tenta todas as chaves possíveis para o nome
        name = item.get('farmaco') or item.get('principio_ativo') or item.get('MEDICAMENTO') or ''
        name = name.strip()
        
        if not name:
            continue
        
        # Categoria (Tenta 'classe' ou infere pelo nome)
        classe = item.get('classe', '')
        category = "Geral"
        name_lower = name.lower()
        if "anticorpo" in classe.lower() or "mab" in name_lower or "mabe" in name_lower: 
            category = "Anticorpos Monoclonais"
        elif "alquilante" in classe.lower() or "taxano" in classe.lower() or "platina" in classe.lower() or "rubicina" in name_lower:
            category = "Quimioterapicos Classicos"
        elif "inibidor" in classe.lower() or "tinibe" in name_lower:
            category = "Terapias Alvo"

        # Logica de Apresentacoes
        raw_pres = item.get('apresentacoes', [])
        clean_presentations = []
        seen_hashes = set()

        if isinstance(raw_pres, list):
            for p in raw_pres:
                desc = p.get('descricao', '').strip()
                brand = p.get('tipo', 'Outro') # Se nao tiver marca, usa o tipo
                if not desc: continue
                
                # Remove duplicatas visuais
                h = normalize_text(desc)
                if h not in seen_hashes:
                    clean_presentations.append({"brand": brand, "description": desc})
                    seen_hashes.add(h)
        
        # Fallback se lista vazia
        if not clean_presentations:
            desc = item.get('apresentacao_frasco', '')
            if desc:
                clean_presentations.append({"brand": "Padrao", "description": desc})

        # Define se e Multiplo
        is_multi = 1 if len(clean_presentations) > 1 else 0
        
        # Texto para a coluna
        if is_multi:
            display_text = "Diversas (Ver Menu)"
            multi_count += 1
        else:
            display_text = clean_presentations[0]['description'] if clean_presentations else "-"
            single_count += 1

        # Calculadoras Especiais
        spec_calc = ''
        if 'carboplatina' in name_lower: spec_calc = 'auc'
        elif 'cisplatina' in name_lower or 'ifosfamida' in name_lower: spec_calc = 'renal'
        elif 'zoledr' in name_lower: spec_calc = 'zoledronic'

        cursor.execute('''
            INSERT INTO medicamentos (
                name, category, presentations, concentration_display, 
                has_multiple_presentations, specialCalculator
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name, category, json.dumps(clean_presentations, ensure_ascii=False),
            display_text, is_multi, spec_calc
        ))

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"SUCESSO: Base recriada!")
    print(f"Medicamentos Multiplos: {multi_count}")
    print(f"Medicamentos Unicos:    {single_count}")
    print(f"TOTAL IMPORTADO:        {multi_count + single_count}")
    print("-" * 30)

if __name__ == '__main__':
    run()
