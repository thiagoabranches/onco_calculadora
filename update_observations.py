import sqlite3
import re

# DADOS DE SEGURANÇA EXTRAÍDOS DO RELATÓRIO TÉCNICO
# Fonte: "Pesquisa de Medicamentos no Mercado Brasileiro.pdf"
obs_data = {
    "aflibercepte": "Diluição em NaCl 0,9% ou Glicose 5%. Concentrações fora do intervalo não foram validadas.",
    "alfapeginterferona": "Administração via subcutânea (SC) direta. Não diluir em bolsa.",
    "amivantamabe": "Alta incidência de reações infusionais na primeira dose. Diluir em G5% ou NaCl 0,9%.",
    "atezolizumabe": "Diluição em NaCl 0,9%.",
    "avelumabe": "Vital utilizar filtro de 0,2 micra na linha de infusão.",
    "azacitidina": "Reconstituição crítica com água estéril. Suspensão hidrolisa rapidamente (usar em 45 min).",
    "bacilo de calmette": "Instilação intravesical direta. Não injetar IV.",
    "belinostat": "Reconstituir com 9 mL de água. Diluição em 250 mL de NaCl 0,9%.",
    "bendamustina": "Reconstituir com água. Diluição em 500 mL de NaCl 0,9%.",
    "bevacizumabe": "Apenas NaCl 0,9% (incompatível com Glicose). Diluições abaixo de 1,4 mg/mL podem causar desestabilização.",
    "blinatumomabe": "Exige estabilizador (polissorbato 80). Dose ínfima (ng/mL). Bolsa dura 24-96h.",
    "bortezomibe": "ATENÇÃO: Diferença crítica de concentração IV (1 mg/mL) vs SC (2,5 mg/mL).",
    "bussulfano": "Solubilidade limitada; concentrações > 0,6 mg/mL podem precipitar.",
    "cabazitaxel": "Pré-mistura obrigatória (diluente + concentrado) resulta em 10 mg/mL antes da bolsa.",
    "carfilzomib": "Administração direta ou bolsa pequena (50-100 mL Glicose 5%).",
    "carmustina": "Reconstituir com solvente alcoólico. Concentrações altas aumentam dor na infusão.",
    "cetuximabe": "Não agitar. Geralmente administrado não diluído ou em NaCl 0,9%.",
    "cisplatina": "Requer íons Cloreto para estabilidade. NUNCA diluir apenas em Glicose.",
    "cidofovir": "Nefrotóxico. Hidratação vigorosa obrigatória com probenecida.",
    "dactinomicina": "Vesicante. Injetar na via do soro em fluxo livre.",
    "daratumumab": "IV em bolsa grande. SC (Faspro) é co-formulado com hialuronidase e não se dilui.",
    "docetaxel": "Risco aumentado de precipitação acima de 0,74 mg/mL.",
    "doxorrubicina": "VESICANTE EXTREMO (Risco de Necrose).",
    "doxorrubicina lipossomal": "IRRITANTE. Apenas Glicose 5% (NaCl desestabiliza o lipossoma).",
    "elranatamabe": "Uso SC direto, não diluída.",
    "etoposideo": "Instável em altas concentrações (precipita > 0,4 mg/mL). Monitorar cristalização.",
    "foscarnet": "Vesicante irritante. Infusão central pura ou periférica diluída.",
    "fotemustine": "Fotossensível. Proteger da luz.",
    "gencitabina": "Solubilidade máx 40 mg/mL. NaCl 0,9% sem conservantes.",
    "gentuzumabe": "Proteger da luz UV. Filtro pode ser necessário.",
    "ifosfamida": "Neurotóxico. Geralmente associado a Mesna.",
    "ipilimumabe": "Requer filtro de linha.",
    "melfalano": "Instabilidade hidrolítica rápida: infundir em até 60 min após preparo.",
    "mitoxantrona": "Cor azul intensa na urina/esclera. Vesicante.",
    "nab-paclitaxel": "NÃO usar filtro. NÃO diluir em bolsa (infundir suspensão reconstituída).",
    "naxitamabe": "Diluir em NaCl 0,9%. Albumina humana pode ser adicionada para estabilização.",
    "oxaliplatina": "APENAS Glicose 5%. NaCl causa degradação. Instável abaixo de 0,2 mg/mL.",
    "paclitaxel": "Obrigatório uso de equipo sem PVC e filtro 0,22 micra.",
    "panitumumabe": "Sempre diluir em NaCl 0,9%.",
    "pemetrexede": "Suplementação de B12/Ácido Fólico obrigatória.",
    "pertuzumabe": "Não agitar. Diluir em NaCl 0,9%.",
    "rituximabe": "Risco de reação infusional grave na primeira dose.",
    "sacituzumabe": "Proteger da luz. Não agitar.",
    "talquetamabe": "Uso SC direto.",
    "teclistamabe": "Uso SC escalonado.",
    "tensirolimo": "Mistura 1:1 com diluente específico antes da bolsa. Proteger da luz.",
    "topotecano": "Diluir em NaCl ou Glicose.",
    "trabectedina": "Infusão longa (24h) ou curta. Proteger da luz.",
    "trastuzumabe": "Não agitar. Incompatível com Glicose (exceto algumas formulações, checar bula).",
    "trastuzumabe deruxtecan": "Apenas Glicose 5%.",
    "trastuzumabe entansina": "Não usar Glicose. Não agitar. Filtro 0.22 micra.",
    "trioxido de arsenio": "Monitorar QT. Risco de síndrome de diferenciação.",
    "vimblastina": "FATAL SE ADMINISTRADO VIA INTRATECAL. Apenas IV.",
    "vincristina": "FATAL SE ADMINISTRADO VIA INTRATECAL. Dose máx 2mg (Capeamento).",
    "vinorelbina": "Vesicante. Infusão rápida seguida de lavagem venosa."
}

def normalize(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def run():
    print("--- INJETANDO OBSERVAÇÕES DE SEGURANÇA ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    # 1. Criar coluna
    try:
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN observations TEXT DEFAULT ''")
    except: pass # Já existe

    # 2. Atualizar
    cursor.execute("SELECT id, name FROM medicamentos")
    rows = cursor.fetchall()
    
    count = 0
    for r in rows:
        mid = r[0]
        name = r[1]
        key = normalize(name)
        
        obs_text = ""
        # Busca flexível
        for k_ref, txt in obs_data.items():
            k_norm = normalize(k_ref)
            if k_norm == key or (len(k_norm)>4 and k_norm in key):
                # Proteções de nomes similares
                if "nab" in k_norm and "nab" not in key: continue
                if "lipo" in k_norm and "lipo" not in key: continue
                
                obs_text = txt
                break
        
        if obs_text:
            cursor.execute("UPDATE medicamentos SET observations = ? WHERE id = ?", (obs_text, mid))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"--- SUCESSO: {count} observações de segurança adicionadas. ---")

if __name__ == '__main__':
    run()
