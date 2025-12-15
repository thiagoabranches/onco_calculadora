import sqlite3
import re

# DADOS COMPLETOS EXTRAÍDOS DO RELATÓRIO
# Formato: "Nome Fármaco": "Marca Principal | Outras Marcas"
dados_completos = {
    "aflibercepte": "Zaltrap®",
    "alfapeginterferona 2a": "Pegasys®",
    "amivantamabe": "Rybrevant®",
    "atezolizumabe": "Tecentriq®",
    "avelumabe": "Bavencio®",
    "azacitidina": "Vidaza®|Genéricos (Accord, Eurofarma)",
    "bacilo de calmette guerin": "Imuno BCG®|Onco BCG®",
    "belinostat": "Beleodaq®",
    "bendamustina": "Ribomustin®|Bendamustina Genéricos",
    "betadinutuximabe": "Qarziba®",
    "bevacizumabe": "Avastin®|Mvasi®|Zirabev®|Oyaved®",
    "bleomicina": "Bonar®|Tecnomet®",
    "blinatumomabe": "Blincyto®",
    "bortezomibe": "Velcade®|Mielocade®|Genéricos",
    "brentuximabe vedotina": "Adcetris®",
    "bussulfano": "Busilvex®",
    "cabazitaxel": "Jevtana®",
    "carboplatina": "Paraplatin® (Histórico)|Genéricos (Accord, Blau)",
    "carfilzomib": "Kyprolis®",
    "carmustina": "Becenun®",
    "cemiplimabe": "Libtayo®",
    "cetuximabe": "Erbitux®",
    "ciclofosfamida": "Genuxal®|Genéricos",
    "cidofovir": "Vistide®",
    "cisplatina": "Platistine®|Genéricos",
    "citarabina": "Aracytin®|Genéricos",
    "cladribina": "Leustatin®",
    "dacarbazina": "Dacarb®|Genéricos",
    "dactinomicina": "Cosmegen®",
    "daratumumab": "Darzalex®",
    "daunorrubicina": "Daunoblastina®",
    "decitabina": "Dacogen®",
    "docetaxel": "Taxotere®|Genéricos",
    "dostarlimabe": "Jemperli®",
    "doxorrubicina": "Adriblastina®|Fauldoxo®",
    "doxorrubicina lipossomal": "Caelyx®|Doxopeg®",
    "durvalumabe": "Imfinzi®",
    "elotuzumabe": "Empliciti®",
    "elranatamabe": "Elrexfio®",
    "enfortumabe vedotina": "Padcev®",
    "epcoritamabe": "Epkinly®",
    "epirrubicina": "Farmorubicina®",
    "eribulina": "Halaven®",
    "etoposideo": "Vepesid®|Etopul®",
    "fludarabina": "Fludara®",
    "fluorouracil": "Genéricos (Faulding, Accord)",
    "foscarnet": "Foscavir®",
    "fotemustine": "Muphoran®",
    "ganciclovir": "Cymevene®",
    "gencitabina": "Gemzar®|Genéricos",
    "gentuzumabe ozogamicina": "Mylotarg®",
    "idarrubicina": "Zavedos®",
    "ifosfamida": "Holoxane®",
    "inotuzumabe ozogamicina": "Besponsa®",
    "interleucina": "Proleukin®",
    "ipilimumabe": "Yervoy®",
    "irinotecano": "Camptosar®|Genéricos",
    "isatuximabe": "Sarclisa®",
    "lurbinectedin": "Zepzelca®",
    "melfalano": "Alkeran®",
    "metotrexato": "Mathera®|Genéricos",
    "mitomicina": "Mitocin®",
    "mitoxantrona": "Evomixan®|Genéricos",
    "nab-paclitaxel": "Abraxane®",
    "naxitamabe": "Danyelza®",
    "nivolumabe": "Opdivo®",
    "nivolumabe + relatlimabe": "Opdualag®",
    "obinutuzumabe": "Gazyva®",
    "oxaliplatina": "Eloxatin®|Genéricos",
    "paclitaxel": "Taxol®|Genéricos",
    "panitumumabe": "Vectibix®",
    "pegaspargase": "Oncaspar®",
    "pembrolizumabe": "Keytruda®",
    "pemetrexede": "Alimta®|Genéricos",
    "pertuzumabe": "Perjeta®",
    "pertuzumabe + trastuzumabe": "Phesgo®",
    "polatuzumabe vedotina": "Polivy®",
    "ramucirumabe": "Cyramza®",
    "rituximabe": "MabThera®|Truxima®|Riximyo®|Vivaxxia®|Novex®",
    "sacituzumabe govitecano": "Trodelvy®",
    "tafasitamabe": "Monjuvi®",
    "talquetamabe": "Talvey®",
    "tarlatamabe": "Imdelltra®",
    "tebentafusp": "Kimmtrak®",
    "teclistamabe": "Tecvayli®",
    "temozolomida": "Temodal®",
    "tensirolimo": "Torisel®",
    "tiotepa": "Tepadina®",
    "topotecano": "Hycamtin®",
    "trabectedina": "Yondelis®",
    "trastuzumabe": "Herceptin®|Zedora®|Kanjinti®|Trazimera®|Herzuma®",
    "trastuzumabe deruxtecan": "Enhertu®",
    "trastuzumabe entansina": "Kadcyla®",
    "tremelimumabe": "Imjudo®",
    "trioxido de arsenio": "Trisenox®",
    "vedolizumabe": "Entyvio®",
    "vimblastina": "Fauldblastina®",
    "vincristina": "Tecnocris®|Fauldvincri®",
    "vinflunina": "Javlor®",
    "vinorelbina": "Navelbine®|Genéricos",
    "zolbetuximabe": "Vyloy®"
}

def normalize(text):
    if not text: return ""
    text = re.sub(r'\s*\(.*?\)', '', text) # Remove parenteses ex: (5-FU)
    text = re.sub(r'[^a-zA-Z0-9]', '', text.lower()) # Remove acentos/espacos
    # Correcoes especificas para matching
    text = text.replace('etoposideo', 'etoposide').replace('etoposide', 'etoposideo')
    text = text.replace('trioxidodearsenio', 'trioxido')
    return text

def run():
    print("--- ATUALIZANDO MARCAS (LISTA COMPLETA 101+) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # Busca nomes do banco
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    updated_names = []
    
    for r in rows:
        mid = r[0]
        nome_db = r[1]
        key_db = normalize(nome_db)
        
        # Tenta encontrar correspondencia
        found_brand = "-"
        
        # 1. Tentativa Exata
        for k_ref, v_ref in dados_completos.items():
            key_ref = normalize(k_ref)
            if key_ref == key_db:
                found_brand = v_ref
                break
        
        # 2. Tentativa Parcial (se nao achou exata)
        if found_brand == "-":
            for k_ref, v_ref in dados_completos.items():
                key_ref = normalize(k_ref)
                if key_ref in key_db or key_db in key_ref:
                    # Evita falsos positivos curtos
                    if len(key_ref) > 4: 
                        found_brand = v_ref
                        break

        if found_brand != "-":
            cursor.execute("UPDATE medicamentos SET brand_name = ? WHERE id = ?", (found_brand, mid))
            count += 1
            updated_names.append(nome_db)
        else:
            print(f"[ALERTA] Marca nao encontrada para: {nome_db}")

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print(f"Total atualizado: {count} medicamentos.")
    print("-" * 30)

if __name__ == '__main__':
    run()
