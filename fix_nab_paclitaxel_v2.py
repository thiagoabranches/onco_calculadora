import sqlite3

def run():
    print("--- CORREÇÃO CIRÚRGICA: NAB-PACLITAXEL (ABRAXANE) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()

    # 1. Ajustar Nab-paclitaxel (Abraxane)
    # Correção: Faixa fixa de 5.0 (suspensão), apenas 100mg, não diluir em glicose
    print("1. Aplicando dados corretos para Nab-paclitaxel...")
    cursor.execute('''
        UPDATE medicamentos 
        SET 
            brand_name = 'Abraxane®',
            concentration = 'Frasco 100 mg (Suspensão)', 
            concMin = 5.0,
            concMax = 5.0,
            sg5 = 'Não',   -- Incompatível/Não usual na diluição final (suspensão pronta)
            sf09 = 'Sim'   -- Reconstituição padrão
        WHERE name LIKE 'Nab-paclitaxel%' OR name LIKE 'Abraxane%'
    ''')

    # 2. Ajustar Paclitaxel Convencional (Taxol)
    # Correção: Faixa 0.3-1.2, múltiplas apresentações
    print("2. Aplicando dados corretos para Paclitaxel...")
    cursor.execute('''
        UPDATE medicamentos 
        SET 
            brand_name = 'Taxol® | Genéricos',
            concentration = 'Frasco 30 mg | Frasco 100 mg',
            concMin = 0.3,
            concMax = 1.2,
            sg5 = 'Sim',
            sf09 = 'Sim'
        WHERE name = 'Paclitaxel' 
    ''')

    conn.commit()
    
    # Validação visual no terminal
    print("-" * 30)
    cursor.execute("SELECT name, concentration, concMin, concMax FROM medicamentos WHERE name LIKE '%aclitaxel%'")
    for r in cursor.fetchall():
        print(f" > {r[0]}: {r[1]} (Faixa: {r[2]} - {r[3]})")
    print("-" * 30)

    conn.close()

if __name__ == '__main__':
    run()
