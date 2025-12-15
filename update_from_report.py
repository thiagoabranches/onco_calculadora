import sqlite3
import re

# --- 1. DADOS EXTRAÍDOS DO RELATÓRIO TÉCNICO ---
# Estrutura: Nome: {marcas, apresentação, faixa, categoria, diluentes}
dados_novos = {
    "aflibercepte": {"marcas": "Zaltrap®", "apres": "Frasco 100 mg/4 mL | 200 mg/8 mL", "faixa": "0.6 - 8.0", "cat": "Antiangiogênicos", "sg5": "Sim", "sf09": "Sim"},
    "alfapeginterferona 2a": {"marcas": "Pegasys®", "apres": "Seringa 180 mcg/0,5 mL", "faixa": "SC Direto", "cat": "Imunoterápicos", "sg5": "-", "sf09": "-"},
    "amivantamabe": {"marcas": "Rybrevant®", "apres": "Frasco 350 mg/7 mL", "faixa": "0.5 - 20.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "atezolizumabe": {"marcas": "Tecentriq®", "apres": "Frasco 1200 mg | 840 mg", "faixa": "3.2 - 16.8", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "avelumabe": {"marcas": "Bavencio®", "apres": "Frasco 200 mg/10 mL", "faixa": "0.5 - 5.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "azacitidina": {"marcas": "Vidaza® | Genéricos", "apres": "Frasco 100 mg (Pó)", "faixa": "1.0 - 4.0", "cat": "Antimetabólitos", "sg5": "Não", "sf09": "Sim"},
    "bacilo de calmette guerin": {"marcas": "Imuno BCG® | Onco BCG®", "apres": "Frasco 40 mg | 80 mg", "faixa": "Intravesical", "cat": "Imunoterápicos", "sg5": "-", "sf09": "Sim"},
    "belinostat": {"marcas": "Beleodaq®", "apres": "Frasco 500 mg", "faixa": "1.0 - 2.0", "cat": "Inibidores", "sg5": "Não", "sf09": "Sim"},
    "bendamustina": {"marcas": "Ribomustin® | Genéricos", "apres": "Frasco 25 mg | 100 mg", "faixa": "0.2 - 0.6", "cat": "Agentes Alquilantes", "sg5": "Não", "sf09": "Sim"},
    "betadinutuximabe": {"marcas": "Qarziba®", "apres": "Frasco 20 mg/4,5 mL", "faixa": "Variável", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "bevacizumabe": {"marcas": "Avastin® | Mvasi® | Zirabev® | Oyaved®", "apres": "Frasco 100 mg | 400 mg", "faixa": "1.4 - 16.5", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "bleomicina": {"marcas": "Bonar® | Tecnomet®", "apres": "Frasco 15 UI", "faixa": "3.0 - 15.0", "cat": "Antibióticos", "sg5": "Não", "sf09": "Sim"},
    "blinatumomabe": {"marcas": "Blincyto®", "apres": "Frasco 38.5 mcg", "faixa": "Microdose", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "bortezomibe": {"marcas": "Velcade® | Mielocade®", "apres": "Frasco 3.5 mg", "faixa": "1.0 (IV) | 2.5 (SC)", "cat": "Inibidores", "sg5": "Não", "sf09": "Sim"},
    "brentuximabe vedotina": {"marcas": "Adcetris®", "apres": "Frasco 50 mg", "faixa": "0.4 - 1.8", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "bussulfano": {"marcas": "Busilvex®", "apres": "Frasco 60 mg/10 mL", "faixa": "0.5", "cat": "Agentes Alquilantes", "sg5": "Sim", "sf09": "Sim"},
    "cabazitaxel": {"marcas": "Jevtana® | Caab® | Proazitax®", "apres": "Frasco 60 mg/1.5 mL", "faixa": "0.10 - 0.26", "cat": "Taxanos", "sg5": "Sim", "sf09": "Sim"},
    "carboplatina": {"marcas": "Fauldcarbo® | B-Platin® | Genéricos", "apres": "Frasco 50 | 150 | 450 mg", "faixa": "0.5 - 2.0", "cat": "Platinas", "sg5": "Sim", "sf09": "Sim"},
    "carfilzomib": {"marcas": "Kyprolis®", "apres": "Frasco 10 | 30 | 60 mg", "faixa": "2.0", "cat": "Inibidores", "sg5": "Sim", "sf09": "Não"},
    "carmustina": {"marcas": "Becenun®", "apres": "Frasco 100 mg", "faixa": "0.2", "cat": "Agentes Alquilantes", "sg5": "Sim", "sf09": "Não"},
    "cemiplimabe": {"marcas": "Libtayo®", "apres": "Frasco 350 mg/7 mL", "faixa": "1.0 - 20.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "cetuximabe": {"marcas": "Erbitux®", "apres": "Frasco 100 mg | 500 mg", "faixa": "5.0 (Puro)", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "ciclofosfamida": {"marcas": "Genuxal® | Genéricos", "apres": "Frasco 200 mg | 1 g | 2 g", "faixa": "2.0 - 20.0", "cat": "Agentes Alquilantes", "sg5": "Sim", "sf09": "Sim"},
    "cidofovir": {"marcas": "Vistide®", "apres": "Frasco 375 mg/5 mL", "faixa": "3.0 - 4.0", "cat": "Antivirais", "sg5": "Não", "sf09": "Sim"},
    "cisplatina": {"marcas": "Platistine® | Faulcispla®", "apres": "Frasco 10 mg | 50 mg | 100 mg", "faixa": "0.5 - 1.0", "cat": "Platinas", "sg5": "Não", "sf09": "Sim"},
    "citarabina": {"marcas": "Aracytin® | Fauldcita®", "apres": "Frasco 100 mg | 500 mg", "faixa": "0.1 - 100.0", "cat": "Antimetabólitos", "sg5": "Sim", "sf09": "Sim"},
    "cladribina": {"marcas": "Leustatin®", "apres": "Frasco 10 mg/10 mL", "faixa": "0.015 - 0.1", "cat": "Antimetabólitos", "sg5": "Não", "sf09": "Sim"},
    "dacarbazina": {"marcas": "Dacarb® | Fauldacar®", "apres": "Frasco 100 mg | 200 mg", "faixa": "1.5 - 4.0", "cat": "Agentes Alquilantes", "sg5": "Sim", "sf09": "Sim"},
    "dactinomicina": {"marcas": "Cosmegen® | Dacilon®", "apres": "Frasco 500 mcg", "faixa": "Direto", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "daratumumab": {"marcas": "Darzalex® | Dalinvi®", "apres": "Frasco 100 mg | 400 mg", "faixa": "0.4 - 3.6", "cat": "Anticorpos Monoclonais", "sg5": "Não", "sf09": "Sim"},
    "daunorrubicina": {"marcas": "Daunoblastina®", "apres": "Frasco 20 mg", "faixa": "2.0", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "decitabina": {"marcas": "Dacogen®", "apres": "Frasco 50 mg", "faixa": "0.1 - 1.0", "cat": "Antimetabólitos", "sg5": "Sim", "sf09": "Sim"},
    "docetaxel": {"marcas": "Taxotere® | Docelibbs®", "apres": "Frasco 20 mg | 80 mg", "faixa": "0.3 - 0.74", "cat": "Taxanos", "sg5": "Sim", "sf09": "Sim"},
    "dostarlimabe": {"marcas": "Jemperli®", "apres": "Frasco 500 mg/10 mL", "faixa": "2.0 - 10.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "doxorrubicina": {"marcas": "Adriblastina® | Fauldoxo® | Rubidox®", "apres": "Frasco 10 mg | 50 mg", "faixa": "Variável", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "doxorrubicina lipossomal": {"marcas": "Caelyx® | Doxopeg®", "apres": "Frasco 20 mg/10 mL", "faixa": "0.4 - 1.2", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Não"},
    "durvalumabe": {"marcas": "Imfinzi®", "apres": "Frasco 120 mg | 500 mg", "faixa": "1.0 - 15.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "elotuzumabe": {"marcas": "Empliciti®", "apres": "Frasco 300 mg | 400 mg", "faixa": "25.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "enfortumabe vedotina": {"marcas": "Padcev®", "apres": "Frasco 20 mg | 30 mg", "faixa": "0.3 - 4.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "epirrubicina": {"marcas": "Farmorubicina® | Brecila®", "apres": "Frasco 10 mg | 50 mg", "faixa": "2.0", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "eribulina": {"marcas": "Halaven®", "apres": "Frasco 0.88 mg", "faixa": "0.02 - 0.44", "cat": "Inibidores", "sg5": "Não", "sf09": "Sim"},
    "etoposideo": {"marcas": "Vepesid® | Eposido®", "apres": "Frasco 100 mg/5 mL", "faixa": "0.2 - 0.4", "cat": "Inibidores", "sg5": "Sim", "sf09": "Sim"},
    "fluorouracil": {"marcas": "Fauldfluor® | Flusan®", "apres": "Frasco 250 mg | 2.5 g | 5 g", "faixa": "25.0", "cat": "Antimetabólitos", "sg5": "Sim", "sf09": "Sim"},
    "gencitabina": {"marcas": "Gemzar® | Genéricos", "apres": "Frasco 200 mg | 1 g | 2 g", "faixa": "0.1 - 38.0", "cat": "Antimetabólitos", "sg5": "Não", "sf09": "Sim"},
    "ifosfamida": {"marcas": "Holoxane®", "apres": "Frasco 1 g | 2 g", "faixa": "0.6 - 20.0", "cat": "Agentes Alquilantes", "sg5": "Sim", "sf09": "Sim"},
    "irinotecano": {"marcas": "Camptosar®", "apres": "Frasco 40 mg | 100 mg", "faixa": "0.12 - 2.8", "cat": "Inibidores", "sg5": "Sim", "sf09": "Sim"},
    "mitomicina": {"marcas": "Mitocin®", "apres": "Frasco 5 mg | 20 mg", "faixa": "0.5 - 1.0", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "mitoxantrona": {"marcas": "Evomixan®", "apres": "Frasco 20 mg", "faixa": "Variável", "cat": "Antibióticos", "sg5": "Sim", "sf09": "Sim"},
    "nivolumabe": {"marcas": "Opdivo®", "apres": "Frasco 40 mg | 100 mg | 240 mg", "faixa": "1.0 - 10.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "oxaliplatina": {"marcas": "Eloxatin®", "apres": "Frasco 50 mg | 100 mg", "faixa": "0.2 - 2.0", "cat": "Platinas", "sg5": "Sim", "sf09": "Não"},
    "paclitaxel": {"marcas": "Taxol®", "apres": "Frasco 30 mg | 100 mg", "faixa": "0.3 - 1.2", "cat": "Taxanos", "sg5": "Sim", "sf09": "Sim"},
    "pembrolizumabe": {"marcas": "Keytruda®", "apres": "Frasco 100 mg", "faixa": "1.0 - 10.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "pemetrexede": {"marcas": "Alimta®", "apres": "Frasco 100 mg | 500 mg", "faixa": "25.0", "cat": "Antimetabólitos", "sg5": "Sim", "sf09": "Sim"},
    "rituximabe": {"marcas": "MabThera® | Truxima® | Riximyo®", "apres": "Frasco 100 mg | 500 mg", "faixa": "1.0 - 4.0", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "trastuzumabe": {"marcas": "Herceptin® | Kanjinti® | Zedora®", "apres": "Frasco 150 mg | 440 mg", "faixa": "Variável", "cat": "Anticorpos Monoclonais", "sg5": "Sim", "sf09": "Sim"},
    "vinorelbina": {"marcas": "Navelbine®", "apres": "Frasco 10 mg | 50 mg", "faixa": "1.5 - 3.0", "cat": "Agentes da Vinca", "sg5": "Sim", "sf09": "Sim"}
}

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def run():
    print("--- INICIANDO ATUALIZAÇÃO (DADOS TÉCNICOS) ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # 1. CORREÇÃO DE CATEGORIAS (ANTIBIÓTICOS PLURAL)
    print("1. Padronizando Categorias...")
    cursor.execute("UPDATE medicamentos SET category = 'Antibióticos' WHERE category LIKE 'Antibiotico%' OR category LIKE 'Antibiótico%'")
    cursor.execute("UPDATE medicamentos SET category = 'Antimetabólitos' WHERE category LIKE 'Antimetabolito%' OR category LIKE 'Antimetabólito%'")
    cursor.execute("UPDATE medicamentos SET category = 'Platinas' WHERE name LIKE '%platina%'")
    cursor.execute("UPDATE medicamentos SET category = 'Taxanos' WHERE name LIKE '%taxel%'")
    
    # 2. ATUALIZAÇÃO DE DADOS (MARCAS E FAIXAS)
    print("2. Atualizando Marcas e Faixas...")
    
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        mid = row[0]
        name = row[1]
        key = normalize(name)
        
        # Procura correspondência
        match = None
        for k_ref in dados_novos:
            if normalize(k_ref) in key or key in normalize(k_ref):
                match = dados_novos[k_ref]
                break
        
        if match:
            # Extrai min/max da string de faixa
            c_min, c_max = 0, 0
            try:
                faixa_nums = re.findall(r"[\d\.]+", match['faixa'].replace(',', '.'))
                if len(faixa_nums) >= 2:
                    c_min, c_max = float(faixa_nums[0]), float(faixa_nums[1])
                elif len(faixa_nums) == 1:
                    c_max = float(faixa_nums[0])
            except: pass

            # Atualiza tudo de uma vez
            cursor.execute('''
                UPDATE medicamentos 
                SET brand_name = ?, 
                    concentration = ?, 
                    concMin = ?, 
                    concMax = ?, 
                    category = ?, 
                    sg5 = ?, 
                    sf09 = ?
                WHERE id = ?
            ''', (
                match['marcas'], 
                match['apres'], 
                c_min, 
                c_max, 
                match['cat'], 
                match['sg5'], 
                match['sf09'], 
                mid
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"--- SUCESSO: {count} medicamentos atualizados com dados oficiais. ---")

if __name__ == '__main__':
    run()
