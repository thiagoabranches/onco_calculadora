import sqlite3
import re

# DADOS FORNECIDOS PELO USUÁRIO
dados_marcas = {
    "aflibercepte": "Zaltrap® Sanofi",
    "alfapeginterferona 2a": "Pegasys® Roche", # Ajustado chave
    "amivantamabe": "Rybrevant® Jansen Cilag",
    "atezolizumabe": "Tecentriq® Roche",
    "avelumabe": "Bavencio® Merck",
    "azacitidina": "Vidaza® United Medical | Winduza® Dr. Reddys",
    "bacilo de calmette guerin": "Urohipe® Uno Health Care",
    "belinostat": "Beleodaq® Pint Pharma",
    "bendamustina": "Ribomustin® Janssen-Cilag | Benalq® Jan",
    "betadinutuximabe": "Qarziba® Global",
    "bevacizumabe": "Avastin® Roche",
    "bleomicina": "Bonar® Biossintética | Bleomycin® Fresenius Kabi",
    "blinatumomabe": "Blincyto® Amgen",
    "bortezomibe": "Mielocade® Bergamo | Velcade® Janssen | Verazo® Libbs",
    "brentuximabe vedotina": "Adcetris® Takeda",
    "bussulfano": "Busilvex® Pierre Fabre",
    "cabazitaxel": "Jevtana® Sanofi | Caab® Accord | Proazitax® Eurofarma",
    "carboplatina": "Fauldcarbo® Libbs | B-Platin® Blau",
    "carfilzomib": "Kyprolis® Amgen",
    "carmustina": "Bicnu® Emcure | Nibisnu® Dr. Reddys",
    "cemiplimabe": "Libtayo® Sanofi",
    "cetuximabe": "Erbitux® Merck",
    "ciclofosfamida": "Genuxal® Baxter",
    "cidofovir": "Vistide® Pharmacia Brasil",
    "cisplatina": "Faulcispla® Libbs",
    "citarabina": "Fauldcita® Libbs",
    "cladribina": "Leustatin® Janssen Cilag",
    "dacarbazina": "Fauldacar® Libbs | Dacarb® Eurofarma | Dacarbazina® Bergamo | Evodazin® Farmarin",
    "dactinomicina": "Dacilon® Celon Labs",
    "daratumumab": "Dalinvi® Janssen Cilag",
    "daunorrubicina": "Evoclass® Farmarin",
    "decitabina": "Dacogen® Janssen Cilag | Deci® Sun | Redtibin® Dr. Reddys",
    "docetaxel": "Taxotere® Sanofi | Docetaxel® Accord | Docelibbs® Libbs | Docetaxel® Glenmark",
    "dostarlimabe": "Jemperli® GSK",
    "doxorrubicina": "Cloridrato® Eurofarma | Rubidox® Bergamo | Fauldoxo® Libbs | Docks® Accord",
    "doxorrubicina lipossomal": "Doxopeg® Zodiac",
    "durvalumabe": "Imfinzi® AstraZeneca",
    "elotuzumabe": "Empliciti® Bristol-Myers",
    "elranatamabe": "Elrexfio® Pfizer",
    "enfortumabe vedotina": "Padcev® Zodiac",
    "epcoritamabe": "Epkinly® Abbvie",
    "epirrubicina": "Brecila® Accord | Farmorubicina® Pfizer",
    "eribulina": "Halaven® United Medical",
    "etoposideo": "Epósido® Blau | Evoposdo® Farmarin", # Normalizado sem acento para match
    "fludarabina": "Fludalibbs® Libbs",
    "fluorouracil": "Fauldfluor® Libbs | Flusan® Eurofarma | Fluorouracil® Accord",
    "foscarnet": "Sol. Foscavir® Clinigen | Scarnet® Mediclone",
    "fotemustine": "Muphoran® Servier",
    "ganciclovir": "Cymevene® Roche | Ganciclotrat® União Quimica"
}

def normalize(text):
    if not text: return ""
    # Remove parenteses e conteúdo (ex: (VP-16))
    text = re.sub(r'\s*\(.*?\)', '', text)
    # Remove acentos e caracteres especiais para comparação
    text = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    # Correção específica para 'etoposideo' vs 'etoposide'
    text = text.replace('etoposideo', 'etoposide').replace('etoposide', 'etoposideo')
    return text

def run():
    print("--- ATUALIZANDO MARCAS (MANUAL) ---")
    db_file = 'farmacia_clinica.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 1. Garante coluna
    try:
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN brand_name TEXT DEFAULT '-'")
    except:
        pass

    # 2. Atualiza
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        mid = row[0]
        name = row[1]
        
        # Normaliza o nome do banco para tentar achar na lista
        # Precisamos ser flexiveis. Ex: "Etoposídeo" no banco -> "etoposideo" na chave
        key_db = normalize(name)
        
        # Tenta encontrar correspondencia
        found_brand = "-"
        
        # Busca direta nas chaves normalizadas do dicionario
        for k, v in dados_marcas.items():
            if normalize(k) in key_db or key_db in normalize(k):
                found_brand = v
                break
        
        if found_brand != "-":
            cursor.execute("UPDATE medicamentos SET brand_name = ? WHERE id = ?", (found_brand, mid))
            count += 1
            print(f"[FIX] {name}: {found_brand[:30]}...")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"Total atualizado: {count}")
    print("-" * 30)

if __name__ == '__main__':
    run()
