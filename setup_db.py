import sqlite3

def init_db():
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            class TEXT,
            concentration TEXT,
            sg5 TEXT,
            sf09 TEXT,
            tissueDamage TEXT,
            stabilityDiluted TEXT,
            cytotoxic TEXT,
            concentracaoPadrao REAL,
            concMin REAL,
            concMax REAL
        )
    ''')

    dados_iniciais = [
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Bleomicina", "Antibiótico Glicopeptídico", "1-3 U/mL", "Não", "Sim", "Irritante", "24h SR", "Sim", 3, 1, 3),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Carboplatina", "Composto de Platina", "0,5-2 mg/mL", "Sim", "Sim", "Irritante", "24h TA", "Sim", 10, 0.5, 2),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Ciclofosfamida", "Agente Alquilante", "< 40 mg/mL", "Sim", "Sim", "Neutro", "24h SR + 24h TA", "Sim", 20, 0, 40),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Cisplatina", "Composto de Platina", "0,1-0,4 mg/mL", "Sim (c/ NaCl)", "Sim", "Vesicante", "48h TA (luz)", "Sim", 1, 0.1, 0.4),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Docetaxel", "Taxano", "0,3-0,74 mg/mL", "Sim", "Sim", "Vesicante", "4h TA", "Sim", 20, 0.3, 0.74),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Doxorrubicina", "Antraciclina", "0,5-2 mg/mL", "Sim", "Sim", "Vesicante", "24h TA; 48h SR", "Sim", 2, 0.5, 2),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Doxorrubicina Lipossomal Peguilado", "Antraciclina", "0,2-0,9 mg/mL", "Sim", "Não", "Irritante", "Imediato/24h SR", "Sim", 2, 0.2, 0.9),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Etoposídeo", "Derivado da Podofilotoxina", "0,2-0,4 mg/mL", "Sim", "Sim", "Irritante", "96h TA/24h TA", "Sim", 20, 0.2, 0.4),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Gencitabina", "Análogo de Nucleosídeo", "0,1-10 mg/mL", "Não", "Sim", "Irritante", "24h TA", "Sim", 38, 0.1, 10),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Ifosfamida", "Agente Alquilante", "< 40 mg/mL", "Sim", "Sim", "Irritante", "24h SR + 24h TA", "Sim", 40, 0, 40),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Irinotecano", "Inibidor da Topoisomerase I", "0,12-2,8 mg/mL", "Sim", "Sim", "Irritante", "24h TA (luz)", "Sim", 20, 0.12, 2.8),
        ("Categoria 3: Agentes Adjuvantes e de Suporte", "Mesna", "Agente Citoprotetor", "20-100 mg/mL", "Sim", "Sim", "Irritante", "Não especificado", "Não", 100, 20, 100),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Paclitaxel", "Taxano", "0,3-1,2 mg/mL", "Sim", "Sim", "Vesicante", "27h TA", "Sim", 6, 0.3, 1.2),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Topotecana", "Inibidor da Topoisomerase I", "0,025-0,05 mg/mL", "Sim", "Sim", "Irritante", "24h SR", "Sim", 1, 0.025, 0.05),
        ("Categoria 1: Agentes Antineoplásicos Clássicos", "Vinorelbina", "Alcaloide da Vinca", "1-2 mg/mL", "Sim", "Sim", "Vesicante", "24h SR/48h TA", "Sim", 10, 1, 2),
        ("Categoria 2: Agentes de Terapia Alvo", "Pertuzumabe", "Anticorpo Monoclonal", "1,6-3,0 mg/mL", "Não", "Sim", "Não irritante", "Imediato", "Não", 30, 1.6, 3.0),
        ("Categoria 2: Agentes de Terapia Alvo", "Trastuzumabe", "Anticorpo Monoclonal", "0,5-1,6 mg/mL", "Não", "Sim", "Não irritante", "Imediato", "Não", 21, 0.5, 1.6),
        ("Categoria 3: Agentes Adjuvantes e de Suporte", "Ácido Zoledrônico", "Bisfosfonato", "0,04 mg/mL", "Sim", "Sim", "Irritante", "24h SR", "Não", 4, 0.04, 0.04)
    ]

    cursor.execute('SELECT count(*) FROM medicamentos')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO medicamentos (category, name, class, concentration, sg5, sf09, tissueDamage, stabilityDiluted, cytotoxic, concentracaoPadrao, concMin, concMax)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', dados_iniciais)
        print("Dados inseridos com sucesso.")
    else:
        print("Banco de dados já contém dados.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
