import sqlite3

def run():
    print("--- CORRIGINDO MIXUP: PACLITAXEL vs NAB-PACLITAXEL ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()

    # 1. CORRIGIR NAB-PACLITAXEL (ABRAXANE)
    # Dados: Frasco 100mg | Faixa Fixa 5.0 mg/mL | Não diluir
    print("1. Ajustando Nab-paclitaxel (Abraxane)...")
    cursor.execute('''
        UPDATE medicamentos 
        SET 
            brand_name = 'Abraxane®',
            concentration = 'Frasco 100 mg (Suspensão)',
            concentration_display = 'Frasco 100 mg (Suspensão)',
            concMin = 5.0,
            concMax = 5.0,
            sg5 = 'Não',   -- Diluente é NaCl 0.9% na reconstituição, não vai em bolsa de Glicose
            sf09 = 'Sim'   -- Reconstitui com NaCl
        WHERE name LIKE 'Nab-paclitaxel%' OR name LIKE 'Abraxane%'
    ''')

    # 2. CORRIGIR PACLITAXEL CONVENCIONAL (TAXOL)
    # Dados: Frasco 30mg/100mg | Faixa 0.3 - 1.2 mg/mL
    print("2. Ajustando Paclitaxel Convencional (Taxol)...")
    cursor.execute('''
        UPDATE medicamentos 
        SET 
            brand_name = 'Taxol® | Genéricos',
            concentration = 'Frasco 30 mg | 100 mg (Solução)',
            concentration_display = 'Frasco 30 mg | 100 mg (Solução)',
            concMin = 0.3,
            concMax = 1.2,
            sg5 = 'Sim',
            sf09 = 'Sim'
        WHERE name = 'Paclitaxel' 
    ''')

    conn.commit()
    
    # Verificação
    cursor.execute("SELECT name, concMin, concMax, concentration FROM medicamentos WHERE name LIKE '%aclitaxel%'")
    for r in cursor.fetchall():
        print(f"   > {r[0]}: Faixa {r[1]}-{r[2]} | {r[3]}")

    conn.close()
    print("--- CORREÇÃO CONCLUÍDA ---")

if __name__ == '__main__':
    run()
