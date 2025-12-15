import sqlite3

def fix_all_categories():
    db_file = 'farmacia_clinica.db'
    
    print("--- CORRECAO GERAL DE CATEGORIAS ---")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Lista de correcoes: (Errado/Padrao SQL, Correto)
        corrections = [
            ("Antibiotico%", "Antibióticos"),
            ("Antimetab%", "Antimetabólitos"),
            ("Imunoterapico%", "Imunoterápicos"),
            ("Quimioterapicos%", "Quimioterápicos Clássicos")
        ]
        
        total_fixed = 0
        
        for pattern, correct in corrections:
            # Verifica quantos estao errados (diferentes do correto)
            cursor.execute(f"SELECT count(*) FROM medicamentos WHERE category LIKE '{pattern}' AND category != '{correct}'")
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute(f"UPDATE medicamentos SET category = '{correct}' WHERE category LIKE '{pattern}'")
                print(f"[FIX] {count} registros corrigidos para '{correct}'")
                total_fixed += count
            else:
                print(f"[OK] '{correct}' ja esta padronizado.")

        conn.commit()
        conn.close()
        print("-" * 30)
        print(f"TOTAL CORRIGIDO: {total_fixed}")
        print("-" * 30)
        
    except Exception as e:
        print(f"[ERRO] Falha: {e}")

if __name__ == '__main__':
    fix_all_categories()
