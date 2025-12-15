import sqlite3
import json
import os
import re

# Configuração
DB_FILE = 'farmacia_clinica.db'
JSON_FILE = 'informacoes_principais_medicamentos.json'

def normalize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def run():
    print("--- INICIANDO MOTOR COLUNA 1: MEDICAMENTO E APRESENTAÇÃO ---")

    # 1. Conectar ao banco e resetar a tabela (Começar do zero para garantir limpeza)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Drop table if exists para recriar com a estrutura correta para este módulo
    cursor.execute("DROP TABLE IF EXISTS medicamentos")
    
    # Criar tabela com campos específicos para o Módulo 1 (e placeholders para o futuro)
    cursor.execute('''
        CREATE TABLE medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            presentations TEXT,          -- JSON com a lista completa de apresentações
            presentation_display TEXT,   -- Texto que vai aparecer na coluna da tabela
            has_multiple INTEGER DEFAULT 0, -- 0 = Única, 1 = Múltipla
            
            -- Placeholders para colunas futuras (serão preenchidas pelos próximos motores)
            concMin REAL DEFAULT 0, 
            concMax REAL DEFAULT 0,
            sg5 TEXT DEFAULT '-', 
            sf09 TEXT DEFAULT '-',
            stabilityDiluted TEXT DEFAULT '-', 
            stabilityExtendedRF TEXT DEFAULT '-',
            specialGroups TEXT DEFAULT '-',
            specialCalculator TEXT DEFAULT '',
            diluentVolume REAL DEFAULT 0,
            concentracaoPadrao REAL DEFAULT 0
        )
    ''')
    
    print("Tabela 'medicamentos' recriada.")

    # 2. Ler o arquivo JSON fonte
    if not os.path.exists(JSON_FILE):
        print(f"ERRO: Arquivo '{JSON_FILE}' não encontrado.")
        return

    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERRO ao ler JSON: {e}")
        return

    print(f"Processando {len(data)} registros do JSON...")
    
    count_single = 0
    count_multiple = 0

    for item in data:
        # Extrair Nome
        name = item.get('farmaco') or item.get('principio_ativo') or ''
        name = name.strip()
        if not name: continue

        # Extrair Categoria (Lógica simples por enquanto)
        classe = item.get('classe', '')
        category = "Geral"
        n_low = name.lower()
        if "anticorpo" in classe.lower() or "mab" in n_low: category = "Anticorpos Monoclonais"
        elif "alquilante" in classe.lower() or "taxano" in classe.lower(): category = "Quimioterapicos Classicos"

        # PROCESSAR APRESENTAÇÕES (O CORAÇÃO DO MOTOR)
        raw_pres = item.get('apresentacoes', [])
        clean_list = []
        seen = set()

        if isinstance(raw_pres, list):
            for p in raw_pres:
                desc = p.get('descricao', '').strip()
                brand = p.get('tipo', 'Outro') # Se não tiver marca, usa o tipo
                if not desc: continue
                
                # Normaliza para evitar duplicatas (ex: "100mg" e "100 mg")
                h = normalize_text(desc)
                if h not in seen:
                    clean_list.append({"brand": brand, "description": desc})
                    seen.add(h)
        
        # Se lista vazia, tenta pegar do campo de texto simples
        if not clean_list:
            desc = item.get('apresentacao_frasco', '')
            if desc:
                clean_list.append({"brand": "Padrao", "description": desc})

        # DECISÃO: É ÚNICA OU MÚLTIPLA?
        if len(clean_list) > 1:
            has_multiple = 1
            presentation_display = "Diversas (Ver Menu)" # Texto fixo para múltiplas
            count_multiple += 1
        else:
            has_multiple = 0
            # Se tiver item na lista, usa a descrição dele. Se não, deixa vazio.
            presentation_display = clean_list[0]['description'] if clean_list else "-"
            count_single += 1

        # Inserir no banco
        cursor.execute('''
            INSERT INTO medicamentos (
                name, category, presentations, presentation_display, has_multiple
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            name, category, json.dumps(clean_list, ensure_ascii=False), presentation_display, has_multiple
        ))

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"SUCESSO: Motor Coluna 1 Finalizado.")
    print(f"Medicamentos com Múltiplas Apresentações: {count_multiple}")
    print(f"Medicamentos com Apresentação Única:      {count_single}")
    print("-" * 30)

if __name__ == '__main__':
    run()
