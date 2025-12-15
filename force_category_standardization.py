import sqlite3

def run():
    db_file = 'farmacia_clinica.db'
    print("--- INICIANDO PADRONIZACAO FORCADA DE CATEGORIAS ---")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Pega todos os itens para analisar um por um
        cursor.execute("SELECT id, name, category FROM medicamentos")
        rows = cursor.fetchall()
        
        updates = 0
        
        for row in rows:
            med_id = row[0]
            name = row[1]
            current_cat = row[2] if row[2] else ""
            
            # Normaliza para analise (minusculo)
            cat_lower = current_cat.lower()
            new_cat = current_cat # Padrao: mantem o que tem
            
            # REGRAS DE OURO (Soberania sobre o dado atual)
            
            # 1. Antimetabolitos
            if 'metab' in cat_lower:
                new_cat = "Antimetabólitos"
                
            # 2. Antibioticos
            elif 'bio' in cat_lower and 'tico' in cat_lower: # Pega antibiotico, antibiótico
                new_cat = "Antibióticos"
                
            # 3. Imunoterapicos
            elif 'imuno' in cat_lower:
                new_cat = "Imunoterápicos"
                
            # 4. Quimioterapicos Classicos (Alquilantes, Taxanos, Platinas, etc)
            elif 'quimio' in cat_lower or 'alquilante' in cat_lower or 'taxano' in cat_lower or 'platina' in cat_lower or 'vinca' in cat_lower or 'topoisomerase' in cat_lower or 'antraciclina' in cat_lower or 'antracenodiona' in cat_lower:
                new_cat = "Quimioterápicos Clássicos"
                
            # 5. Anticorpos Monoclonais (Mabs)
            elif 'anticorpo' in cat_lower or 'monoclonal' in cat_lower:
                new_cat = "Anticorpos Monoclonais"
                
            # 6. Terapias Alvo (Inibidores)
            elif 'inibidor' in cat_lower and 'topoisomerase' not in cat_lower and 'proteassoma' not in cat_lower:
                new_cat = "Terapias Alvo"

            # Aplica a mudanca apenas se for diferente
            if new_cat != current_cat:
                cursor.execute("UPDATE medicamentos SET category = ? WHERE id = ?", (new_cat, med_id))
                print(f" [FIX] {name}: '{current_cat}' -> '{new_cat}'")
                updates += 1

        conn.commit()
        conn.close()
        print("-" * 30)
        print(f"TOTAL PADRONIZADO: {updates} registros.")
        print("-" * 30)
        
    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == '__main__':
    run()
