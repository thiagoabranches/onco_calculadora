import sqlite3

db_file = "farmacia_clinica.db"

def run():
    print("--- AUDITORIA: COLUNA PADRONIZAÇÃO ---")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Busca itens onde a padronização está vazia ou com traço
    cursor.execute('''
        SELECT name FROM medicamentos 
        WHERE std_volume IS NULL 
           OR std_volume = '' 
           OR std_volume = '-' 
           OR std_volume = 'nan'
        ORDER BY name ASC
    ''')
    
    missing = cursor.fetchall()
    
    # Busca itens preenchidos para comparar
    cursor.execute('''
        SELECT count(*) FROM medicamentos 
        WHERE std_volume IS NOT NULL 
          AND std_volume != '' 
          AND std_volume != '-' 
          AND std_volume != 'nan'
    ''')
    filled_count = cursor.fetchone()[0]
    
    print(f"STATUS ATUAL:")
    print(f" - Padronizados (OK): {filled_count}")
    print(f" - Pendentes (Vazio): {len(missing)}")
    print("-" * 30)
    
    if len(missing) > 0:
        print("LISTA DE MEDICAMENTOS SEM PADRONIZAÇÃO (Cole esta lista):")
        print("-" * 30)
        for m in missing:
            print(f"{m[0]}")
        print("-" * 30)
    else:
        print(" [SUCESSO] Todos os medicamentos estão padronizados!")

    conn.close()

if __name__ == '__main__':
    run()
