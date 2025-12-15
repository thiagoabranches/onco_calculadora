import os
import re

app_file = "app.py"

# --- Dados Essenciais (Para garantir que estão presentes) ---
essential_imports = [
    'from flask import Flask, jsonify, request',
    'import sqlite3',
    'import json' # Essencial para ler/escrever dados JSON/Dict
]
app_definition = 'app = Flask(__name__)'

def fix_structure():
    if not os.path.exists(app_file):
        print(f"[ERRO] Arquivo '{app_file}' não encontrado.")
        return

    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Extrair todas as partes do código em blocos
    
    # 1.1 Extrair imports e definições iniciais
    imports = []
    other_code = []
    
    # Busca por linhas de importação ou definição
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('import') or line.startswith('from'):
            imports.append(line.strip())
        elif line.strip() == app_definition:
            continue # Ignora a definição de app, vamos colocar no lugar certo
        else:
            # Tudo que não é importação ou a definição de app
            other_code.append(line)

    # 1.2 Extrair todas as rotas (@app.route) e suas funções
    route_blocks = []
    # Expressão regular para capturar blocos de rota completos
    route_pattern = re.compile(r'(@app\.route\s*\(.+?\)\s*def\s+\w+\s*\(.*?\):\s*(?:.|\n)*?)(?=\n@app\.route|\nif __name__)', re.MULTILINE)
    
    content_no_imports = "\n".join(other_code)
    
    # Remove o bloco principal para facilitar a busca de rotas
    main_block_start = content_no_imports.find("if __name__ == '__main__':")
    if main_block_start != -1:
        routes_section = content_no_imports[:main_block_start]
        main_block = content_no_imports[main_block_start:]
    else:
        routes_section = content_no_imports
        main_block = ""
    
    # Encontra e armazena todas as rotas
    for match in route_pattern.finditer(routes_section):
        route_blocks.append(match.group(0).strip())

    # 1.3 Limpar código remanescente que não é rota, import ou bloco principal
    for route_block in route_blocks:
        routes_section = routes_section.replace(route_block, '').strip()

    # 2. Montar o arquivo na ordem correta
    
    final_content = []
    
    # A. Imports
    final_content.extend(list(set(imports + essential_imports)))
    final_content.append("")
    
    # B. Definição do Servidor Flask
    final_content.append(app_definition)
    final_content.append("")
    
    # C. Código de configuração (O que sobrou da seção de rotas, geralmente funções auxiliares)
    if routes_section:
        final_content.append(routes_section.strip())
        final_content.append("")

    # D. Todas as rotas (@app.route), incluindo a nova
    final_content.extend(route_blocks)
    final_content.append("")
    
    # E. Bloco Principal (if __name__ == '__main__':)
    final_content.append(main_block.strip())

    # 3. Salvar o arquivo
    new_content = "\n".join(final_content)
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("-" * 40)
    print(f"SUCESSO: A estrutura do '{app_file}' foi corrigida.")
    print("O erro 'NameError: name 'app' is not defined' deve ter sido resolvido.")
    print("-" * 40)

if __name__ == '__main__':
    fix_structure()
