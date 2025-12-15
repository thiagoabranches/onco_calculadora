import sqlite3
import json
import os

def lock_data():
    db_file = 'farmacia_clinica.db'
    lock_file = 'locked_data.json'
    
    if not os.path.exists(db_file):
        print("[ERRO] Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Seleciona apenas as colunas que serao TRAVADAS
    # ID e a chave para garantir que os dados voltem para o medicamento certo
    cursor.execute("SELECT id, name, concentration, concMin, concMax, sg5, sf09 FROM medicamentos")
    rows = cursor.fetchall()
    
    data_to_lock = {}
    for row in rows:
        data_to_lock[row['id']] = {
            "ref_name": row['name'], # Apenas referencia visual no JSON
            "concentration": row['concentration'],
            "concMin": row['concMin'],
            "concMax": row['concMax'],
            "sg5": row['sg5'],
            "sf09": row['sf09']
        }
    
    conn.close()
    
    # Salva o arquivo de "Trava"
    with open(lock_file, 'w', encoding='utf-8') as f:
        json.dump(data_to_lock, f, indent=2, ensure_ascii=False)
        
    print("-" * 40)
    print(f"[BLOQUEIO ATIVADO] Dados de {len(rows)} medicamentos salvos em '{lock_file}'.")
    print("As colunas 'Apresentacao', 'Faixa', 'SG5%' e 'SF0.9%' estao protegidas.")
    print("Agora voce pode trabalhar no Modulo de Nomes sem medo de perder esses dados.")
    print("-" * 40)

if __name__ == '__main__':
    lock_data()
