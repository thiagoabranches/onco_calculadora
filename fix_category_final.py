import sqlite3

def run():
    db = 'farmacia_clinica.db'
    print("--- INICIANDO CORRECAO DE CATEGORIAS ---")
    
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        # 1. Diagnostico: Ver o que existe agora
        print("Categorias Atuais:")
        cursor.execute("SELECT DISTINCT category FROM medicamentos")
        cats = cursor.fetchall()
        for c in cats:
            print(f" -> '{c[0]}'")

        print("-" * 30)

        # 2. Varredura e Correcao Linha a Linha
        cursor.execute("SELECT id, name, category FROM medicamentos")
        rows = cursor.fetchall()
        
        updates = 0
        for row in rows:
            mid = row[0]
            name = row[1]
            cat_original = row[2] if row[2] else ""
            cat_lower = cat_original.lower()
            
            new_cat = cat_original

            # Regra para Antibioticos (pega com ou sem acento)
            if 'biotico' in cat_lower or 'biótico' in cat_lower:
                new_cat = "Antibióticos"
            
            # Regra para Antimetabolitos
            elif 'metabo' in cat_lower or 'metabó' in cat_lower:
                new_cat = "Antimetabólitos"

            # Regra para Imunoterapicos
            elif 'imuno' in cat_lower:
                new_cat = "Imunoterápicos"

            # Regra para Quimioterapicos
            elif 'quimio' in cat_lower or 'classico' in cat_lower or 'clássico' in cat_lower:
                new_cat = "Quimioterápicos Clássicos"

            # Se mudou, atualiza
            if new_cat != cat_original:
                cursor.execute("UPDATE medicamentos SET category = ? WHERE id = ?", (new_cat, mid))
                print(f"[FIX] {name}: '{cat_original}' -> '{new_cat}'")
                updates += 1

        conn.commit()
        
        print("-" * 30)
        print(f"Total corrigido: {updates}")
        
        # 3. Verificacao Final
        print("Categorias Finais (Unificadas):")
        cursor.execute("SELECT DISTINCT category FROM medicamentos")
        final_cats = cursor.fetchall()
        for c in final_cats:
            print(f" -> '{c[0]}'")
            
        conn.close()
        
    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == '__main__':
    run()
