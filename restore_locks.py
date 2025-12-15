import sqlite3
import json
import os

def run():
    print("--- RESTAURANDO COLUNAS TRAVADAS (SG/SF/MARCAS) ---")
    
    if not os.path.exists('lock_modulo_1.json'):
        print("[ERRO CRÍTICO] Arquivo 'lock_modulo_1.json' não encontrado!")
        print("Não é possível restaurar o estado anterior sem o backup.")
        return

    # 1. Carregar Backup
    with open('lock_modulo_1.json', 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
        
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    count = 0
    for med_id, dados in backup_data.items():
        # Restaura APENAS as colunas que deveriam estar travadas
        # IGNORA concMin e concMax (que são o foco do Módulo 2 atual)
        cursor.execute('''
            UPDATE medicamentos 
            SET 
                brand_name = ?,
                name = ?,
                concentration = ?,
                sg5 = ?,
                sf09 = ?
            WHERE id = ?
        ''', (
            dados.get('brand_name'),
            dados.get('name'),
            dados.get('concentration'),
            dados.get('sg5'),
            dados.get('sf09'),
            med_id
        ))
        count += 1

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"[SUCESSO] {count} registros restaurados.")
    print("As colunas 'Faixa' (Módulo 2) foram MANTIDAS com as novas atualizações.")
    print("As colunas 'SG', 'SF', 'Marca' e 'Apresentação' voltaram ao estado travado.")
    print("-" * 30)

if __name__ == '__main__':
    run()
