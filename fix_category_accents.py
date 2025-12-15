import sqlite3

def fix_categories():
    db_file = 'farmacia_clinica.db'
    
    print("--- CORRECAO DE CATEGORIAS ---")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 1. Identificar registros incorretos
        cursor.execute("SELECT count(*) FROM medicamentos WHERE category LIKE 'Antimetab_lito%' OR category LIKE 'Antimetabolito%'")
        count_wrong = cursor.fetchone()[0]
        
        if count_wrong > 0:
            print(f"Encontrados {count_wrong} registros incorretos.")
            
            # 2. Atualizar para a forma correta com acento
            cursor.execute('''
                UPDATE medicamentos 
                SET category = 'Antimetabólitos' 
                WHERE category LIKE 'Antimetab_lito%' 
                   OR category LIKE 'Antimetabolito%'
            ''')
            
            print(f"[SUCESSO] Corrigido: Todos agora sao 'Antimetabólitos'.")
        else:
            print("Nenhuma categoria incorreta encontrada.")

        # Padronizar outras categorias comuns
        cursor.execute("UPDATE medicamentos SET category = 'Antibióticos' WHERE category LIKE 'Antibiotico%'")
        cursor.execute("UPDATE medicamentos SET category = 'Imunoterápicos' WHERE category LIKE 'Imunoterapico%'")
        cursor.execute("UPDATE medicamentos SET category = 'Quimioterápicos Clássicos' WHERE category LIKE 'Quimioterapicos%'")

        conn.commit()
        conn.close()
        print("--- FIM DA CORRECAO ---")
        
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")

if __name__ == '__main__':
    fix_categories()
