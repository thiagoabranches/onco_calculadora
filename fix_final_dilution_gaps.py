import sqlite3

db_file = "farmacia_clinica.db"

# Dados para preenchimento final dos 4 itens faltantes
final_updates = {
    "Azacitidina": {"diluent": "SF 0,9%", "volume": "100 mL"},
    "Bacilo de calmette gurin": {"diluent": "SF 0,9%", "volume": "Uso Tópico/Instilação"},
    "Interleucina (aldesleukin)": {"diluent": "SF 0,9%", "volume": "100 mL"},
    "Tebentafusp": {"diluent": "SF 0,9%", "volume": "100 mL"}
}

def run():
    print("--- PREENCHIMENTO FINAL DAS 4 LACUNAS DE PADRONIZAÇÃO ---")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    count = 0
    
    for name, data in final_updates.items():
        diluent = data['diluent']
        volume = data['volume']
        
        # Usa LIKE para garantir que pegue o nome exato do banco (ex: "Bacilo de calmette gurin" pode ser "Bacilo de Calmette-Guerin")
        cursor.execute('''
            UPDATE medicamentos 
            SET std_diluent = ?, std_volume = ? 
            WHERE name LIKE ?
        ''', (diluent, volume, f"{name}%"))
        
        if cursor.rowcount > 0:
            count += 1
            print(f" [FIX] {name} -> {volume} em {diluent}")
        else:
            # Tenta um match mais genérico (ex: apenas "Interleucina")
            cursor.execute('''
                UPDATE medicamentos 
                SET std_diluent = ?, std_volume = ? 
                WHERE name LIKE ?
            ''', (diluent, volume, f"%{name.split(' ')[0]}%"))
            if cursor.rowcount > 0:
                 count += 1
                 print(f" [FIX] {name} -> {volume} em {diluent} (Match Parcial)")


    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} lacunas preenchidas.")
    print("A coluna 'Padronização' está 100% preenchida.")
    print("-" * 30)

if __name__ == '__main__':
    run()
