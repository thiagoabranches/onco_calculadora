import sqlite3
import re

def clean_med_name(name):
    if not name: return ""
    
    # 1. Remove quebras de linha e tabs
    clean = name.replace('\n', ' ').replace('\r', '').strip()
    
    # 2. Remove conteúdo entre parenteses (ex: (5-FU), (Taxol))
    clean = re.sub(r'\s*\(.*?\)', '', clean)
    
    # 3. Remove aspas extras
    clean = clean.replace('"', '').replace("'", "")
    
    # 4. Remove espaços duplos
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # 5. Capitalização Inteligente
    uppercase_exceptions = ["BCG", "5-FU", "CHOP", "R-CHOP", "ABVD"] 
    if clean.upper() in uppercase_exceptions:
        return clean.upper()
        
    # Capitaliza primeira letra de cada palavra relevante, ou apenas a primeira
    # Aqui optamos por Capitalize (Só a primeira maiúscula) para consistência
    return clean.capitalize()

def run():
    db_file = 'farmacia_clinica.db'
    print("--- MOTOR DE NOMES (HIGIENIZAÇÃO) ---")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM medicamentos")
        rows = cursor.fetchall()
        
        count = 0
        for row in rows:
            old_name = row[1]
            new_name = clean_med_name(old_name)
            
            if old_name != new_name:
                cursor.execute("UPDATE medicamentos SET name = ? WHERE id = ?", (new_name, row[0]))
                print(f" [FIX] {old_name} -> {new_name}")
                count += 1
                
        conn.commit()
        conn.close()
        print(f"--- CONCLUÍDO: {count} nomes corrigidos. ---")
        
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao banco: {e}")

if __name__ == '__main__':
    run()
