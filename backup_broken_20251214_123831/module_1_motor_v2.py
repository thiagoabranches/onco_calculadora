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

    # 1. Reset Total da Tabela
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS medicamentos")
    
    # Cria tabela com estrutura base sólida
    cursor.execute('''
        CREATE TABLE medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            presentations TEXT,          -- JSON com a lista real
            concentration_display TEXT,  -- O que o usuário vê na coluna
            has_multiple INTEGER DEFAULT 0, -- Flag crucial: 0 ou 1
            
            -- Placeholders para módulos futuros (vazios por enquanto)
            concMin REAL DEFAULT 0, concMax REAL DEFAULT 0,
            sg5 TEXT DEFAULT '-', sf09 TEXT DEFAULT '-',
            stabilityDiluted TEXT DEFAULT '-', stabilityExtendedRF TEXT DEFAULT '-',
            specialGroups TEXT DEFAULT '-', specialCalculator TEXT DEFAULT '',
            diluentVolume REAL DEFAULT 0, concentracaoPadrao REAL DEFAULT 0
        )
    ''')

    if not os.path.exists(json_file):
        print(f"[ERRO] {json_file} nao encontrado.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processando {len(data)} itens...")
    
    multi_count = 0
    single_count = 0

    for item in data:
        # 1. Nome e Categoria
        name = item.get('farmaco') or item.get('principio_ativo') or ''
        name = name.strip()
        if not name: continue
        
        classe = item.get('classe', '')
        category = "Geral"
        n_low = name.lower()
        if "anticorpo" in classe.lower() or "mab" in n_low: category = "Anticorpos Monoclonais"
        elif "alquilante" in classe.lower() or "taxano" in classe.lower(): category = "Quimioterapicos Classicos"

        # 2. Lógica de Apresentações (O Coração do Motor)
        raw_pres = item.get('apresentacoes', [])
        clean_list = []
        seen = set()

        if isinstance(raw_pres, list):
            for p in raw_pres:
                desc = p.get('descricao', '').strip()
                brand = p.get('tipo', 'Outro')
                if not desc: continue
                
                # Remove duplicatas exatas
                h = normalize_text(desc)
                if h not in seen:
                    clean_list.append({"brand": brand, "description": desc})
                    seen.add(h)
        
        # Fallback se lista vazia
        if not clean_list:
            desc = item.get('apresentacao_frasco', '')
            if desc:
                # Tenta quebrar strings como "Frasco 100mg e 500mg" se necessário, 
                # mas por segurança, tratamos como única se vier numa string só.
                clean_list.append({"brand": "Padrao", "description": desc})

        # 3. Decisão: Múltiplo ou Único?
        is_multi = 1 if len(clean_list) > 1 else 0
        
        if is_multi:
            display_text = "Diversas (Ver Menu)"
            multi_count += 1
        else:
            display_text = clean_list[0]['description'] if clean_list else "-"
            single_count += 1

        # 4. Calculadoras (Marcadores iniciais)
        spec_calc = ''
        if 'carboplatina' in n_low: spec_calc = 'auc'
        elif 'cisplatina' in n_low: spec_calc = 'renal'

        cursor.execute('''
            INSERT INTO medicamentos (
                name, category, presentations, concentration_display, 
                has_multiple, specialCalculator
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name, category, json.dumps(clean_list, ensure_ascii=False),
            display_text, is_multi, spec_calc
        ))

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"SUCESSO: Motor 1 finalizado.")
    print(f"Múltiplos (Com ícone): {multi_count}")
    print(f"Únicos (Sem ícone):    {single_count}")
    print("-" * 30)

if __name__ == '__main__':
    run()
