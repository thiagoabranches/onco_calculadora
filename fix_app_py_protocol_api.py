import re
import os

app_file = "app.py"

# O código da nova rota API
new_route_code = """
@app.route('/api/protocolos')
def get_protocolos():
    conn = sqlite3.connect('farmacia_clinica.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM protocolos")
    protocolos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(protocolos)
"""

def fix_app_py():
    if not os.path.exists(app_file):
        print(f"[ERRO] Arquivo '{app_file}' não encontrado.")
        return

    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Checa se a rota já existe (para evitar duplicatas)
    if "@app.route('/api/protocolos')" in content:
        print("[AVISO] Rota de protocolos já existe no app.py. Nenhuma alteração foi feita.")
        return

    # 2. Encontra o local para inserir: antes da última @app.route ou antes de 'if __name__ == '__main__':'.
    
    # Ponto de inserção preferencial: antes da última rota definida
    match_last_route = re.search(r'(@app\.route\s*\(.+?\)\s*def\s+\w+\s*\(.+?\):\s*(?:.|\n)*?)(?=\n@app\.route|\nif __name__)', content)
    
    if match_last_route:
        # Insere APÓS a última rota encontrada
        insertion_point = match_last_route.end()
        new_content = content[:insertion_point] + "\n" + new_route_code + content[insertion_point:]
        print("[SUCESSO] Rota de protocolos adicionada antes da próxima rota.")
    else:
        # Se não achou rotas, tenta inserir antes do bloco principal
        insertion_point = content.find("if __name__ == '__main__':")
        if insertion_point != -1:
            new_content = new_route_code + "\n" + content
            print("[SUCESSO] Rota de protocolos adicionada no início do app.py.")
        else:
            print("[ERRO] Não foi possível encontrar local seguro para inserir a rota no app.py.")
            return

    # 3. Salva o arquivo corrigido
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"O arquivo '{app_file}' foi atualizado com a nova API de protocolos.")

if __name__ == '__main__':
    fix_app_py()
