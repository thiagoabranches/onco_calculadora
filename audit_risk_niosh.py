import sqlite3
import re

db_file = "farmacia_clinica.db"

# CLASSIFICAÇÃO BASEADA NO NIOSH (LISTA DE ANTINEOPLÁSICOS PERIGOSOS)
# Group 1: Antineoplastic drugs (Cytotoxic/Hazardous)
niosh_group_1 = [
    # Alquilantes & Platinas
    "bendamustina", "bussulfano", "carboplatina", "carmustina", "clorambucila", 
    "cisplatina", "ciclofosfamida", "dacarbazina", "ifosfamida", "melfalano", 
    "oxaliplatina", "temozolomida", "tiotepa", "trabectedina", "lurbinectedin", 
    "procarbazina", "estreptozocina",
    
    # Antimetabólitos
    "azacitidina", "capecitabina", "cladribina", "clofarabina", "citarabina", 
    "decitabina", "floxuridina", "fludarabina", "fluorouracil", "gencitabina", 
    "mercaptopurina", "metotrexato", "nelarabina", "pemetrexede", "thioguanina",
    
    # Antibióticos Antitumorais
    "bleomicina", "dactinomicina", "daunorrubicina", "doxorrubicina", 
    "epirrubicina", "idarubicina", "mitomicina", "mitoxantrona", "valrubicina",
    
    # Inibidores Mitóticos (Taxanos, Vincas, etc)
    "cabazitaxel", "docetaxel", "paclitaxel", "nab-paclitaxel", 
    "vinblastina", "vincristina", "vinorelbina", "vinflunina", 
    "eribulina", "ixabepilona",
    
    # Inibidores de Topoisomerase
    "etoposideo", "irinotecano", "topotecano", "teniposideo",
    
    # Outros Perigosos
    "bortezomibe", "carfilzomib", "ixazomib", "lenalidomida", "pomalidomida", 
    "talidomida", "trixido de arsenio", "tretinoina",
    
    # ADCs (Antibody-Drug Conjugates) - CARREGAM QUIMIO
    "brentuximabe vedotina", "traztuzumabe entansina", "kadcyla", "adcetris",
    "gentuzumabe ozogamicina", "inotuzumabe ozogamicina", "polatuzumabe vedotina",
    "enfortumabe vedotina", "sacituzumabe govitecano", "trastuzumabe deruxtecan"
]

# Group: Monoclonals & Biologics (Geralmente NÃO classificados como perigosos/citotóxicos pelo NIOSH para manuseio)
# Eles exigem assepsia, mas não são mutagênicos/teratogênicos como a quimio.
safe_biologics = [
    "rituximabe", "trastuzumabe", "bevacizumabe", "cetuximabe", "panitumumabe",
    "pertuzumabe", "alemtuzumabe", "atezolizumabe", "avelumabe", "cemiplimabe",
    "daratumumab", "durvalumabe", "elotuzumabe", "ipilimumabe", "nivolumabe",
    "obinutuzumabe", "ofatumumabe", "pembrolizumabe", "ramucirumabe", 
    "tocilizumabe", "blinatumomabe", "aflibercepte", "interferona", "interleucina"
]

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def run():
    print("--- AUDITORIA DE RISCO OCUPACIONAL (FONTE: NIOSH 2024) ---")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. Adicionar coluna de Fonte
    try: cursor.execute("ALTER TABLE medicamentos ADD COLUMN risk_source TEXT DEFAULT '-'")
    except: pass
    
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    updates_cyto = 0
    updates_safe = 0
    
    for r in rows:
        mid = r[0]
        name = r[1]
        norm_name = normalize(name)
        
        is_cyto = 0 # Default Seguro
        source = "-"
        
        # Verifica se é Grupo 1 (Perigoso)
        match_cyto = False
        for drug in niosh_group_1:
            if normalize(drug) in norm_name:
                match_cyto = True
                break
        
        # Verifica se é Biológico Seguro (exceção explícita)
        # Ex: "Trastuzumabe" (Seguro) vs "Trastuzumabe Entansina" (Perigoso)
        match_safe = False
        for drug in safe_biologics:
            # Só marca seguro se NÃO for um ADC (Entansina/Vedotina/Deruxtecan)
            if normalize(drug) in norm_name and not match_cyto:
                match_safe = True
                break
        
        # Lógica Final
        if match_cyto:
            is_cyto = 1
            source = "NIOSH 2024 (Grupo 1)"
            updates_cyto += 1
            print(f" [☣️ PERIGO] {name}")
        elif match_safe:
            is_cyto = 0
            source = "NIOSH 2024 (Biológico)"
            updates_safe += 1
            # print(f" [🛡️ SEGURO] {name}")
        else:
            # Se não está em nenhuma lista, mantém o padrão (Seguro) mas marca revisão
            is_cyto = 0 
            source = "Não Listado"

        cursor.execute("UPDATE medicamentos SET is_cytotoxic = ?, risk_source = ? WHERE id = ?", (is_cyto, source, mid))

    conn.commit()
    conn.close()
    print("-" * 30)
    print(f"RESUMO DA AUDITORIA:")
    print(f" - {updates_cyto} confirmados como Citotóxicos (Vermelho)")
    print(f" - {updates_safe} classificados como Biológicos/Seguros (Branco)")
    print("-" * 30)

if __name__ == '__main__':
    run()
