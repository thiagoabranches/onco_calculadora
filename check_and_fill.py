import sqlite3
import json

# Lista COMPLETA de 101 Medicamentos (Extraida e Consolidada)
lista_completa = [
    {"nome": "Aflibercepte", "cat": "Antiangiogênico", "apres": "Frasco 100 mg/4 mL | 200 mg/8 mL"},
    {"nome": "Alfapeginterferona 2a", "cat": "Imunoestimulante", "apres": "Seringa 180 mcg"},
    {"nome": "Amivantamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 350 mg/7 mL"},
    {"nome": "Atezolizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 1200 mg | 840 mg"},
    {"nome": "Avelumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 200 mg/10 mL"},
    {"nome": "Azacitidina", "cat": "Hipometilante", "apres": "Frasco 100 mg"},
    {"nome": "Bacilo de Calmette Guérin", "cat": "Imunoterápico", "apres": "Frasco 40 mg"},
    {"nome": "Belinostat", "cat": "Inibidor HDAC", "apres": "Frasco 500 mg"},
    {"nome": "Bendamustina", "cat": "Alquilante", "apres": "Frasco 25 mg | 100 mg"},
    {"nome": "Betadinutuximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 20 mg"},
    {"nome": "Bevacizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 400 mg"},
    {"nome": "Bleomicina", "cat": "Antibiótico", "apres": "Frasco 15 UI"},
    {"nome": "Blinatumomabe", "cat": "BiTE", "apres": "Frasco 38.5 mcg"},
    {"nome": "Bortezomibe", "cat": "Inibidor Proteassoma", "apres": "Frasco 3.5 mg"},
    {"nome": "Brentuximabe vedotina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 50 mg"},
    {"nome": "Bussulfano", "cat": "Alquilante", "apres": "Frasco 60 mg"},
    {"nome": "Cabazitaxel", "cat": "Taxano", "apres": "Frasco 60 mg"},
    {"nome": "Carboplatina", "cat": "Platina", "apres": "Frasco 50 | 150 | 450 mg"},
    {"nome": "Carfilzomib", "cat": "Inibidor Proteassoma", "apres": "Frasco 10 | 30 | 60 mg"},
    {"nome": "Carmustina", "cat": "Alquilante", "apres": "Frasco 100 mg"},
    {"nome": "Cemiplimabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 350 mg"},
    {"nome": "Cetuximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 | 500 mg"},
    {"nome": "Ciclofosfamida", "cat": "Alquilante", "apres": "Frasco 1g | 200 mg"},
    {"nome": "Cidofovir", "cat": "Antiviral", "apres": "Frasco 375 mg"},
    {"nome": "Cisplatina", "cat": "Platina", "apres": "Frasco 10 mg | 50 mg"},
    {"nome": "Citarabina", "cat": "Antimetabólito", "apres": "Frasco 100 mg | 500 mg"},
    {"nome": "Cladribina", "cat": "Antimetabólito", "apres": "Frasco 10 mg"},
    {"nome": "Dacarbazina", "cat": "Alquilante", "apres": "Frasco 100 mg | 200 mg"},
    {"nome": "Dactinomicina", "cat": "Antibiótico", "apres": "Frasco 500 mcg"},
    {"nome": "Daratumumab", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 400 mg"},
    {"nome": "Daunorrubicina", "cat": "Antraciclina", "apres": "Frasco 20 mg"},
    {"nome": "Decitabina", "cat": "Hipometilante", "apres": "Frasco 50 mg"},
    {"nome": "Docetaxel", "cat": "Taxano", "apres": "Frasco 20 mg | 80 mg"},
    {"nome": "Dostarlimabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 500 mg"},
    {"nome": "Doxorrubicina", "cat": "Antraciclina", "apres": "Frasco 10 mg | 50 mg"},
    {"nome": "Doxorrubicina Lipossomal", "cat": "Antraciclina", "apres": "Frasco 20 mg | 50 mg"},
    {"nome": "Durvalumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 120 mg | 500 mg"},
    {"nome": "Elotuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 300 mg | 400 mg"},
    {"nome": "Elranatamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 44 mg | 76 mg"},
    {"nome": "Enfortumabe vedotina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 20 mg | 30 mg"},
    {"nome": "Epcoritamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 4 mg | 48 mg"},
    {"nome": "Epirrubicina", "cat": "Antraciclina", "apres": "Frasco 10 mg | 50 mg"},
    {"nome": "Eribulina", "cat": "Inibidor Microtúbulos", "apres": "Frasco 0.88 mg"},
    {"nome": "Etoposídeo", "cat": "Inibidor Topoisomerase", "apres": "Frasco 100 mg"},
    {"nome": "Fludarabina", "cat": "Antimetabólito", "apres": "Frasco 50 mg"},
    {"nome": "Fluorouracil", "cat": "Antimetabólito", "apres": "Frasco 250 mg | 2.5 g"},
    {"nome": "Foscarnet", "cat": "Antiviral", "apres": "Frasco 6 g/250 mL"},
    {"nome": "Fotemustine", "cat": "Alquilante", "apres": "Frasco 208 mg"},
    {"nome": "Ganciclovir", "cat": "Antiviral", "apres": "Frasco 500 mg"},
    {"nome": "Gencitabina", "cat": "Antimetabólito", "apres": "Frasco 200 mg | 1 g"},
    {"nome": "Gentuzumabe ozogamicina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 4.5 mg"},
    {"nome": "Idarrubicina", "cat": "Antraciclina", "apres": "Frasco 5 mg | 10 mg"},
    {"nome": "Ifosfamida", "cat": "Alquilante", "apres": "Frasco 1 g"},
    {"nome": "Inotuzumabe ozogamicina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 1 mg"},
    {"nome": "Interleucina", "cat": "Citocina", "apres": "Frasco 18/22 M UI"},
    {"nome": "Ipilimumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 50 mg | 200 mg"},
    {"nome": "Irinotecano", "cat": "Inibidor Topoisomerase", "apres": "Frasco 40 mg | 100 mg"},
    {"nome": "Isatuximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 500 mg"},
    {"nome": "Lurbinectedin", "cat": "Alquilante", "apres": "Frasco 4 mg"},
    {"nome": "Melfalano", "cat": "Alquilante", "apres": "Frasco 50 mg"},
    {"nome": "Metotrexato", "cat": "Antimetabólito", "apres": "Frasco 50 mg | 500 mg"},
    {"nome": "Mitomicina", "cat": "Antibiótico", "apres": "Frasco 5 mg | 20 mg"},
    {"nome": "Mitoxantrona", "cat": "Antracenodiona", "apres": "Frasco 20 mg"},
    {"nome": "Nab-paclitaxel", "cat": "Taxano", "apres": "Frasco 100 mg"},
    {"nome": "Naxitamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 40 mg"},
    {"nome": "Nivolumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 40 mg | 100 mg"},
    {"nome": "Nivolumabe + Relatlimabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 240/80 mg"},
    {"nome": "Obinutuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 1000 mg"},
    {"nome": "Oxaliplatina", "cat": "Platina", "apres": "Frasco 50 mg | 100 mg"},
    {"nome": "Paclitaxel", "cat": "Taxano", "apres": "Frasco 30 mg | 100 mg"},
    {"nome": "Panitumumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 400 mg"},
    {"nome": "Pegaspargase", "cat": "Enzima", "apres": "Frasco 3750 UI"},
    {"nome": "Pembrolizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg"},
    {"nome": "Pemetrexede", "cat": "Antimetabólito", "apres": "Frasco 100 mg | 500 mg"},
    {"nome": "Pertuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 420 mg"},
    {"nome": "Pertuzumabe + Trastuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 600/600 mg"},
    {"nome": "Polatuzumabe vedotina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 30 mg | 140 mg"},
    {"nome": "Ramucirumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 500 mg"},
    {"nome": "Rituximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 500 mg"},
    {"nome": "Sacituzumabe govitecano", "cat": "Anticorpo Monoclonal", "apres": "Frasco 180 mg"},
    {"nome": "Tafasitamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 200 mg"},
    {"nome": "Talquetamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 2 mg | 40 mg"},
    {"nome": "Tarlatamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 1 mg | 10 mg"},
    {"nome": "Tebentafusp", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mcg"},
    {"nome": "Teclistamabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 30 mg | 153 mg"},
    {"nome": "Temozolomida", "cat": "Alquilante", "apres": "Frasco 100 mg (IV)"},
    {"nome": "Tensirolimo", "cat": "Inibidor mTOR", "apres": "Frasco 25 mg"},
    {"nome": "Tiotepa", "cat": "Alquilante", "apres": "Frasco 15 mg | 100 mg"},
    {"nome": "Topotecano", "cat": "Inibidor Topoisomerase", "apres": "Frasco 4 mg"},
    {"nome": "Trabectedina", "cat": "Alquilante", "apres": "Frasco 1 mg"},
    {"nome": "Trastuzumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 150 mg | 440 mg"},
    {"nome": "Trastuzumabe deruxtecan", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg"},
    {"nome": "Trastuzumabe entansina", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg | 160 mg"},
    {"nome": "Tremelimumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 25 mg | 300 mg"},
    {"nome": "Trióxido de arsênio", "cat": "Outros", "apres": "Frasco 10 mg"},
    {"nome": "Vedolizumabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 300 mg"},
    {"nome": "Vimblastina", "cat": "Alcaloide da Vinca", "apres": "Frasco 10 mg"},
    {"nome": "Vincristina", "cat": "Alcaloide da Vinca", "apres": "Frasco 1 mg"},
    {"nome": "Vinflunina", "cat": "Alcaloide da Vinca", "apres": "Frasco 50 mg | 250 mg"},
    {"nome": "Vinorelbina", "cat": "Alcaloide da Vinca", "apres": "Frasco 10 mg | 50 mg"},
    {"nome": "Zolbetuximabe", "cat": "Anticorpo Monoclonal", "apres": "Frasco 100 mg"}
]

conn = sqlite3.connect('farmacia_clinica.db')
cursor = conn.cursor()

# Verifica quantos temos
cursor.execute("SELECT count(*) FROM medicamentos")
atual = cursor.fetchone()[0]
print(f"Estado Atual: {atual} medicamentos.")

# Verifica quais faltam pelo nome
cursor.execute("SELECT name FROM medicamentos")
nomes_no_banco = [row[0] for row in cursor.fetchall()]

adicionados = 0
for med in lista_completa:
    # Checagem simples (exata) - Poderiamos usar fuzzy, mas vamos garantir o basico primeiro
    if med['nome'] not in nomes_no_banco:
        cursor.execute('''
            INSERT INTO medicamentos (name, category, concentration)
            VALUES (?, ?, ?)
        ''', (med['nome'], med['cat'], med['apres']))
        adicionados += 1
        print(f"   [+] Adicionado: {med['nome']}")

conn.commit()
conn.close()

print("-" * 40)
print(f"Concluido. Adicionados {adicionados} novos registros.")
print(f"Total esperado agora: {atual + adicionados}")
print("-" * 40)
