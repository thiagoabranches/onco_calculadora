import sqlite3
import re

# DADOS VALIDADOS PELO RELATÓRIO TÉCNICO (FONTE: SEU ARQUIVO)
# Formato: Chave: [Min, Max, SG5, SF09]
# SG5/SF09: "Sim", "Não" ou "-" (se irrelevante/não citado)
dados_auditados = {
    # GRUPO A
    "aflibercepte": [0.6, 8.0, "Sim", "Sim"],          # [cite: 27]
    "alfapeginterferona": [0, 0, "-", "-"],            # SC Direto [cite: 36, 37]
    "amivantamabe": [0.5, 20.0, "Sim", "Sim"],         # [cite: 47]
    "atezolizumabe": [3.2, 16.8, "Não", "Sim"],        # Diluição em NaCl [cite: 57, 58]
    "avelumabe": [0.5, 5.0, "Não", "Sim"],             # NaCl 0.45 ou 0.9 [cite: 66, 67]
    "azacitidina": [1.0, 4.0, "Não", "Sim"],           # IV: 1-4 mg/mL[cite: 80]. SC é 25 fixo.
    
    # GRUPO B
    "bacilo de calmette": [0.8, 1.6, "-", "Sim"],      # Intravesical (~40-80mg/50mL) [cite: 90]
    "belinostat": [1.0, 2.0, "Não", "Sim"],            # NaCl 0.9 [cite: 99, 100]
    "bendamustina": [0.2, 0.6, "Não", "Sim"],          # NaCl 0.9 [cite: 109, 110]
    "betadinutuximabe": [0, 0, "Não", "Sim"],          # Variavel, NaCl [cite: 118]
    "bevacizumabe": [1.4, 16.5, "Não", "Sim"],         # Apenas NaCl [cite: 129, 130]
    "bleomicina": [3.0, 15.0, "Sim", "Sim"],           # NaCl ou Água [cite: 137, 138]
    "blinatumomabe": [0, 0, "-", "Sim"],               # Microdose ng/mL [cite: 146]
    "bortezomibe": [1.0, 2.5, "Não", "Sim"],           # IV 1.0, SC 2.5 [cite: 153, 154]
    "brentuximabe": [0.4, 1.8, "Sim", "Sim"],          # [cite: 163]
    "bussulfano": [0.5, 0.6, "Sim", "Sim"],            # Aprox 0.5, precipita >0.6 [cite: 171, 172]
    
    # GRUPO C
    "cabazitaxel": [0.10, 0.26, "Sim", "Sim"],         # [cite: 185]
    "carboplatina": [0.5, 2.0, "Sim", "Sim"],          # [cite: 193]
    "carfilzomib": [2.0, 2.0, "Sim", "Não"],           # Glicose 5% pref [cite: 202]
    "carmustina": [0.2, 0.2, "Sim", "Não"],            # 0.2 mg/mL [cite: 209]
    "cemiplimabe": [1.0, 20.0, "Sim", "Sim"],          # [cite: 217]
    "cetuximabe": [5.0, 5.0, "Não", "Sim"],            # Não diluir ou NaCl [cite: 225]
    "ciclofosfamida": [2.0, 20.0, "Sim", "Sim"],       # [cite: 233]
    "cidofovir": [3.0, 4.0, "Não", "Sim"],             # ~3-4 mg/mL NaCl [cite: 242, 243]
    "cisplatina": [0.5, 1.0, "Não", "Sim"],            # Nunca Glicose pura [cite: 251, 252]
    "citarabina": [0.1, 100.0, "Sim", "Sim"],          # [cite: 259]
    "cladribina": [0.015, 0.1, "Não", "Sim"],          # NaCl [cite: 267, 268]
    
    # GRUPO D
    "dacarbazina": [1.5, 4.0, "Sim", "Sim"],           # [cite: 276]
    "dactinomicina": [0.5, 0.5, "Sim", "Sim"],         # 500mcg/mL direto [cite: 282]
    "daratumumab": [0.4, 3.6, "Não", "Sim"],           # IV[cite: 289]. SC é fixo.
    "daunorrubicina": [2.0, 2.0, "Sim", "Sim"],        # [cite: 297]
    "decitabina": [0.1, 1.0, "Sim", "Sim"],            # NaCl [cite: 305]
    "docetaxel": [0.3, 0.74, "Sim", "Sim"],            # Max 0.74 [cite: 311]
    "dostarlimabe": [2.0, 10.0, "Sim", "Sim"],         # [cite: 320]
    "doxorrubicina": [0.1, 2.0, "Sim", "Sim"],         # Variável [cite: 323]
    "doxorrubicina lipossomal": [0.4, 1.2, "Sim", "Não"], # Apenas Glicose 5% [cite: 323]
    "durvalumabe": [1.0, 15.0, "Sim", "Sim"],          # [cite: 331]
    
    # GRUPO E
    "elotuzumabe": [25.0, 25.0, "Sim", "Sim"],         # Reconstituído [cite: 338]
    "elranatamabe": [0, 0, "-", "-"],                  # SC Direto [cite: 345]
    "enfortumabe": [0.3, 4.0, "Sim", "Sim"],           # [cite: 352]
    "epcoritamabe": [0, 0, "-", "-"],                  # SC Direto [cite: 358]
    "epirrubicina": [2.0, 2.0, "Sim", "Sim"],          # [cite: 362]
    "eribulina": [0.02, 0.44, "Não", "Sim"],           # NaCl 0.9 [cite: 370, 371]
    "etoposideo": [0.2, 0.4, "Sim", "Sim"],            # Crítico >0.4 precipita [cite: 378]
    
    # GRUPO F-G
    "fludarabina": [0.04, 1.0, "Sim", "Sim"],          # [cite: 384]
    "fluorouracil": [25.0, 25.0, "Sim", "Sim"],        # Padrão puro ou diluído [cite: 388]
    "foscarnet": [12.0, 24.0, "Sim", "Sim"],           # 24 (Central) ou 12 (Periférico) [cite: 397]
    "fotemustine": [52.0, 52.0, "Sim", "Não"],         # Glicose 5% [cite: 402]
    "ganciclovir": [1.0, 10.0, "Sim", "Sim"],          # Max 10 [cite: 409]
    "gencitabina": [0.1, 38.0, "Não", "Sim"],          # NaCl [cite: 415, 416]
    "gentuzumabe": [0.075, 0.234, "Não", "Sim"],       # [cite: 423]
    
    # GRUPO I-M
    "idarrubicina": [1.0, 1.0, "Sim", "Sim"],          # [cite: 429]
    "ifosfamida": [0.6, 20.0, "Sim", "Sim"],           # [cite: 436]
    "inotuzumabe": [0.01, 0.1, "Sim", "Sim"],          # [cite: 443]
    "ipilimumabe": [1.0, 4.0, "Sim", "Sim"],           # [cite: 457]
    "irinotecano": [0.12, 2.8, "Sim", "Sim"],          # [cite: 464]
    "isatuximabe": [1.0, 4.0, "Sim", "Sim"],           # Diluição bolsa 250 [cite: 472]
    "lurbinectedin": [0.02, 0.5, "Sim", "Sim"],        # [cite: 479]
    "melfalano": [0.1, 0.45, "Não", "Sim"],            # NaCl, Max 0.45 [cite: 486]
    "metotrexato": [25.0, 25.0, "Sim", "Sim"],         # Variável [cite: 492]
    "mitomicina": [0.5, 1.0, "Sim", "Sim"],            # [cite: 498]
    "mitoxantrona": [2.0, 2.0, "Sim", "Sim"],          # [cite: 502]
    
    # GRUPO N-O
    "nab-paclitaxel": [5.0, 5.0, "Não", "Sim"],        # Não diluir em bolsa 
    "naxitamabe": [0.1, 4.0, "Não", "Sim"],            # NaCl [cite: 518]
    "nivolumabe": [1.0, 10.0, "Sim", "Sim"],           # [cite: 524]
    "obinutuzumabe": [0.4, 4.0, "Não", "Sim"],         # NaCl [cite: 537, 538]
    "oxaliplatina": [0.2, 2.0, "Sim", "Não"],          # APENAS GLICOSE 
    
    # GRUPO P
    "paclitaxel": [0.3, 1.2, "Sim", "Sim"],            # [cite: 552]
    "panitumumabe": [1.0, 10.0, "Não", "Sim"],         # NaCl, Max 10 [cite: 558]
    "pembrolizumabe": [1.0, 10.0, "Sim", "Sim"],       # [cite: 570]
    "pemetrexede": [1.0, 25.0, "Sim", "Sim"],          # [cite: 577]
    "pertuzumabe": [1.5, 3.0, "Não", "Sim"],           # NaCl [cite: 582]
    "polatuzumabe": [0.72, 22.0, "Não", "Sim"],        # NaCl [cite: 596, 597]
    
    # GRUPO R-Z
    "ramucirumabe": [2.0, 10.0, "Não", "Sim"],         # NaCl [cite: 603]
    "rituximabe": [1.0, 4.0, "Sim", "Sim"],            # [cite: 611]
    "sacituzumabe": [1.1, 3.4, "Não", "Sim"],          # NaCl [cite: 618]
    "tafasitamabe": [2.0, 8.0, "Sim", "Sim"],          # [cite: 624]
    "talquetamabe": [0, 0, "-", "-"],                  # SC [cite: 629]
    "teclistamabe": [0, 0, "-", "-"],                  # SC [cite: 643]
    "temozolomida": [2.5, 2.5, "Não", "Sim"],          # [cite: 648]
    "tensirolimo": [0.1, 1.0, "Sim", "Sim"],           # [cite: 653]
    "tiotepa": [0.5, 1.0, "Sim", "Sim"],               # [cite: 658]
    "topotecano": [0.02, 0.5, "Sim", "Sim"],           # [cite: 663]
    "trabectedina": [0.01, 0.05, "Sim", "Sim"],        # [cite: 668]
    "trastuzumabe": [0.4, 4.0, "Sim", "Sim"],          # [cite: 674]
    "trastuzumabe deruxtecan": [0.4, 2.0, "Sim", "Não"], # Glicose [cite: 680]
    "trastuzumabe entansina": [4.0, 20.0, "Não", "Sim"], # NaCl [cite: 685]
    "vinflunina": [3.0, 12.0, "Sim", "Sim"],           # [cite: 716]
    "vinorelbina": [1.5, 3.0, "Sim", "Sim"],           # [cite: 721]
    "zolbetuximabe": [0.2, 5.0, "Sim", "Sim"]          # [cite: 727]
}

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def run_audit():
    print("--- INICIANDO PENTE FINO (AUDITORIA E CORRECAO) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # Busca medicamentos no banco
    cursor.execute("SELECT id, name FROM medicamentos")
    db_items = cursor.fetchall()
    
    count_updates = 0
    
    for item in db_items:
        mid = item[0]
        name = item[1]
        norm_name = normalize(name)
        
        # Encontra correspondencia
        match_data = None
        
        # 1. Match Exato ou Contido
        for k, v in dados_auditados.items():
            k_norm = normalize(k)
            # Logica para evitar falsos positivos (ex: "taxel" pegando tudo)
            if k_norm == norm_name or (len(k_norm) > 4 and k_norm in norm_name):
                # Protecao contra Paclitaxel vs Nab-paclitaxel
                if "nab" in k_norm and "nab" not in norm_name: continue
                if "nab" in norm_name and "nab" not in k_norm: continue
                # Protecao Doxo vs Doxo Lipo
                if "lipo" in k_norm and "lipo" not in norm_name: continue
                if "lipo" in norm_name and "lipo" not in k_norm: continue
                
                match_data = v
                break
        
        if match_data:
            # Aplica Correcao Forcada
            c_min, c_max, sg, sf = match_data
            
            cursor.execute('''
                UPDATE medicamentos 
                SET concMin = ?, concMax = ?, sg5 = ?, sf09 = ?
                WHERE id = ?
            ''', (c_min, c_max, sg, sf, mid))
            
            print(f"[CORRIGIDO] {name}: Faixa {c_min}-{c_max} | SG:{sg} SF:{sf}")
            count_updates += 1
        else:
            print(f"[ALERTA] {name} nao encontrado na lista de auditoria.")

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"Auditoria concluida. {count_updates} medicamentos padronizados.")
    print("-" * 30)

if __name__ == '__main__':
    run_audit()
