import sqlite3
import re

# DADOS AGRUPADOS DA SUA LISTA
dados_agrupados = {
    "aflibercepte": "Zaltrap® Sanofi",
    "alfapeginterferona 2a": "Pegasys® Roche",
    "amivantamabe": "Rybrevant® Jansen Cilag",
    "atezolizumabe": "Tecentriq® Roche",
    "avelumabe": "Bavencio® Merck",
    "azacitidina": "Vidaza® United Medical|Winduza® Dr. Reddy's",
    "bacilo de calmette guerin": "Urohipe® Uno Health Care",
    "belinostat": "Beleodaq® Pint Pharma",
    "bendamustina": "Ribomustin® Janssen-Cilag|Benalq® Jan",
    "betadinutuximabe": "Qarziba® Global",
    "bevacizumabe": "Avastin® Roche",
    "bleomicina": "Bonar® Biossintética|Bleomycin® Fresenius Kabi",
    "blinatumomabe": "Blincyto® Amgen",
    "bortezomibe": "Mielocade® Bergamo|Velcade® Janssen|Verazo® Libbs",
    "brentuximabe vedotina": "Adcetris® Takeda",
    "bussulfano": "Busilvex® Pierre Fabre",
    "cabazitaxel": "Jevtana® Sanofi|Caab® Accord|Proazitax® Eurofarma",
    "carboplatina": "Fauldcarbo® Libbs|B-Platin® Blau",
    "carfilzomib": "Kyprolis® Amgen",
    "carmustina": "Bicnu® Emcure|Nibisnu® Dr. Reddy's",
    "cemiplimabe": "Libtayo® Sanofi",
    "cetuximabe": "Erbitux® Merck",
    "ciclofosfamida": "Genuxal® Baxter",
    "cidofovir": "Vistide® Pharmacia Brasil",
    "cisplatina": "Faulcispla® Libbs",
    "citarabina": "Fauldcita® Libbs",
    "cladribina": "Leustatin® Janssen Cilag",
    "dacarbazina": "Fauldacar® Libbs|Dacarb® Eurofarma|Dacarbazina® Bergamo|Evodazin® Farmarin",
    "dactinomicina": "Dacilon® Celon Labs",
    "daratumumab": "Dalinvi® Janssen Cilag",
    "daunorrubicina": "Evoclass® Farmarin",
    "decitabina": "Dacogen® Janssen Cilag|Deci® Sun|Redtibin® Dr. Reddy's",
    "docetaxel": "Taxotere® Sanofi|Docetaxel® Accord|Docelibbs® Libbs|Docetaxel® Glenmark",
    "dostarlimabe": "Jemperli® GSK",
    "doxorrubicina": "Cloridrato® Eurofarma|Cloridrato® Glenmark|Evorrubicin® Farmarin|Rubidox® Bergamo|Fauldoxo® Libbs|Docks® Accord",
    "doxorrubicina lipossomal": "Doxopeg® Zodiac",
    "durvalumabe": "Imfinzi® AstraZeneca",
    "elotuzumabe": "Empliciti® Bristol-Myers",
    "elranatamabe": "Elrexfio® Pfizer",
    "enfortumabe vedotina": "Padcev® Zodiac",
    "epcoritamabe": "Epkinly® Abbvie",
    "epirrubicina": "Brecila® Accord|Cloridrato® Accord|Farmorubicina® Pfizer",
    "eribulina": "Halaven® United Medical",
    "etoposideo": "Epósido® Blau|Evoposdo® Farmarin",
    "fludarabina": "Fludalibbs® Libbs",
    "fluorouracil": "Fauldfluor® Libbs|Flusan® Eurofarma|Fluorouracil® Accord",
    "foscarnet": "Sol. Foscavir® Clinigen|Scarnet® Mediclone",
    "fotemustine": "Muphoran® Servier",
    "ganciclovir": "Cymevene® Roche|Ganciclotrat® União Quimica"
}

def normalize(text):
    if not text: return ""
    text = re.sub(r'\s*\(.*?\)', '', text) # Remove (siglas)
    text = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    text = text.replace('etoposideo', 'etoposide').replace('etoposide', 'etoposideo')
    return text

def run():
    print("--- AGRUPANDO MARCAS NO BANCO DE DADOS ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # Busca nomes atuais
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    for r in rows:
        mid = r[0]
        nome_db = r[1]
        key = normalize(nome_db)
        
        # Procura correspondencia parcial
        match_marcas = "-"
        for k_ref, v_ref in dados_agrupados.items():
            if normalize(k_ref) in key or key in normalize(k_ref):
                match_marcas = v_ref
                break
        
        if match_marcas != "-":
            cursor.execute("UPDATE medicamentos SET brand_name = ? WHERE id = ?", (match_marcas, mid))
            count += 1
            if '|' in match_marcas:
                print(f"[MULTI] {nome_db}: {match_marcas.count('|')+1} marcas")

    conn.commit()
    conn.close()
    print(f"--- FIM: {count} medicamentos atualizados com marcas. ---")

if __name__ == '__main__':
    run()
