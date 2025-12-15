import sqlite3
import re

# DADOS EXTRAÍDOS DO RELATÓRIO TÉCNICO (Referência Cruzada)
# Formato: "Fármaco": [Min, Max]
faixas_oficiais = {
    "aflibercepte": [0.6, 8.0],          # 
    "amivantamabe": [0.5, 20.0],         # [cite: 47]
    "atezolizumabe": [3.2, 16.8],        # [cite: 58]
    "avelumabe": [0.5, 5.0],             # [cite: 67]
    "azacitidina": [1.0, 4.0],           # [cite: 80]
    "belinostat": [1.0, 2.0],            # [cite: 100]
    "bendamustina": [0.2, 0.6],          # [cite: 110]
    "bevacizumabe": [1.4, 16.5],         # [cite: 130]
    "bleomicina": [3.0, 15.0],           # [cite: 138]
    "brentuximabe vedotina": [0.4, 1.8], # [cite: 163]
    "cabazitaxel": [0.10, 0.26],         # [cite: 185]
    "carboplatina": [0.5, 2.0],          # [cite: 193]
    "cemiplimabe": [1.0, 20.0],          # [cite: 217]
    "cisplatina": [0.5, 1.0],            # [cite: 252]
    "citarabina": [0.1, 100.0],          # [cite: 259]
    "cladribina": [0.015, 0.1],          # [cite: 268]
    "dacarbazina": [1.5, 4.0],           # [cite: 276]
    "daratumumab": [0.4, 3.6],           # [cite: 289]
    "docetaxel": [0.3, 0.74],            # [cite: 311]
    "dostarlimabe": [2.0, 10.0],         # [cite: 320]
    "doxorrubicina lipossomal": [0.4, 1.2], # [cite: 323]
    "durvalumabe": [1.0, 15.0],          # [cite: 331]
    "enfortumabe vedotina": [0.3, 4.0],  # [cite: 352]
    "eribulina": [0.02, 0.44],           # [cite: 371]
    "etoposideo": [0.2, 0.4],            # [cite: 378] (Considerando estabilidade crítica)
    "gencitabina": [0.1, 38.0],          # [cite: 416]
    "gentuzumabe ozogamicina": [0.075, 0.234], # [cite: 423]
    "ifosfamida": [0.6, 20.0],           # [cite: 436]
    "inotuzumabe ozogamicina": [0.01, 0.1], # [cite: 443]
    "ipilimumabe": [1.0, 4.0],           # [cite: 457]
    "irinotecano": [0.12, 2.8],          # [cite: 464]
    "melfalano": [0.1, 0.45],            # [cite: 486]
    "nivolumabe": [1.0, 10.0],           # [cite: 524]
    "obinutuzumabe": [0.4, 4.0],         # [cite: 538]
    "oxaliplatina": [0.2, 2.0],          # 
    "paclitaxel": [0.3, 1.2],            # [cite: 552]
    "pembrolizumabe": [1.0, 10.0],       # [cite: 570]
    "polatuzumabe vedotina": [0.72, 22.0], # [cite: 597]
    "rituximabe": [1.0, 4.0],            # [cite: 611]
    "sacituzumabe govitecano": [1.1, 3.4], # [cite: 618]
    "tafasitamabe": [2.0, 8.0],          # [cite: 624]
    "trastuzumabe deruxtecan": [0.4, 2.0], # [cite: 680]
    "vinflunina": [3.0, 12.0],           # [cite: 716]
    "vinorelbina": [1.5, 3.0]            # [cite: 721]
}

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def run():
    print("--- MOTOR 2: ATUALIZANDO FAIXAS (mg/mL) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    for r in rows:
        mid = r[0]
        name = r[1]
        key = normalize(name)
        
        # Busca exata ou parcial
        match_vals = None
        for k_ref, vals in faixas_oficiais.items():
            if normalize(k_ref) in key or key in normalize(k_ref):
                match_vals = vals
                break
        
        if match_vals:
            # ATUALIZA APENAS COLUNAS DE FAIXA (MÓDULO 2)
            cursor.execute("UPDATE medicamentos SET concMin = ?, concMax = ? WHERE id = ?", (match_vals[0], match_vals[1], mid))
            print(f"[FAIXA] {name}: {match_vals[0]} - {match_vals[1]} mg/mL")
            count += 1
        else:
            # Se não tiver dados no relatório, zera ou mantem anterior? Vamos manter o que tem se não achar.
            pass

    conn.commit()
    conn.close()
    print(f"--- MÓDULO 2 CONCLUÍDO: {count} faixas atualizadas. ---")

if __name__ == '__main__':
    run()
