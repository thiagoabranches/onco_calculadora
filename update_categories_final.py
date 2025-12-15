import sqlite3

db_file = "farmacia_clinica.db"

# DEFINIÇÃO DOS GRUPOS (Conforme solicitado)
updates = {
    "Alcaloides da Vinca": [
        "Vimblastina", "Vinorelbina", "Vinflunina", "Vincristina"
    ],
    "Derivados da Camptotecina": [
        "Irinotecano", "Topotecano"
    ],
    "Antibióticos Antitumorais": [ # Ajustado para nome técnico correto
        "Dactinomicina", "Bleomicina", "Mitomicina"
    ],
    "Antraciclinas": [
        "Daunorrubicina", "Doxorrubicina", "Epirrubicina", "Idarrubicina"
    ],
    "Mostardas Nitrogenadas": [
        "Ciclofosfamida", "Ifosfamida"
    ]
}

def run():
    print("--- RECLASSIFICAÇÃO FARMACOLÓGICA E CITOTÓXICA ---")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    count = 0
    
    for category, drugs in updates.items():
        print(f"Processando Grupo: {category}...")
        for drug in drugs:
            # Atualiza Categoria e Força Citotoxicidade (Vermelho)
            # Usa LIKE para pegar variações (ex: Doxorrubicina Lipossomal)
            cursor.execute('''
                UPDATE medicamentos 
                SET category = ?, is_cytotoxic = 1 
                WHERE name LIKE ?
            ''', (category, f"%{drug}%"))
            
            if cursor.rowcount > 0:
                print(f"  -> {drug}: Atualizado.")
                count += cursor.rowcount
            else:
                print(f"  [AVISO] {drug} não encontrado no banco.")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"SUCESSO: {count} medicamentos reclassificados e marcados como citotóxicos.")
    print("-" * 30)

if __name__ == '__main__':
    run()
