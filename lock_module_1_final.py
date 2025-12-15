import sqlite3
import json
import os

def lock():
    print("--- TRAVANDO MÓDULO 1 (IDENTIFICAÇÃO) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Seleciona as colunas blindadas
    cursor.execute("SELECT id, name, brand_name, concentration, sg5, sf09 FROM medicamentos")
    rows = cursor.fetchall()
    
    data = {}
    for r in rows:
        data[r['id']] = dict(r)
        
    with open('lock_modulo_1.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"[TRAVA ATIVADA] {len(data)} registros protegidos em 'lock_modulo_1.json'.")
    print("As colunas 'Nome Comercial', 'Medicamento', 'Apresentação', 'SG' e 'SF' estão salvas.")

if __name__ == '__main__':
    lock()
