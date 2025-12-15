import sqlite3

# DADOS COMPLEMENTARES (Baseados na interpretação clínica do relatório)
updates = {
    # SC ou Direto (Faixa 0 ou Fixa)
    "alfapeginterferona 2a": [0, 0], # SC [cite: 36]
    "elranatamabe": [0, 0],          # SC [cite: 345]
    "epcoritamabe": [0, 0],          # SC [cite: 358]
    "talquetamabe": [0, 0],          # SC [cite: 629]
    "teclistamabe": [0, 0],          # SC [cite: 643]
    "pertuzumabe + trastuzumabe": [0, 0], # SC (Phesgo) [cite: 589]
    
    # Diluições Específicas (Calculadas)
    "bacilo de calmette guerin": [0.8, 1.6], # 40-80mg em 50mL [cite: 90]
    "isatuximabe": [1.0, 4.0],       # Est. baseada em dose/250mL 
    "pertuzumabe": [1.6, 3.0],       # 420mg em 250mL (aprox 1.68) 
    "nab-paclitaxel": [5.0, 5.0],    # Suspensão pronta, não diluir [cite: 511]
    "trastuzumabe deruxtecan": [0.4, 2.0], # Em 100mL 
    "panitumumabe": [1.0, 10.0],     # Max 10mg/mL 
    "tensirolimo": [0.1, 1.0],       # Diluir em bolsa após pré-mix [cite: 653]
    "trabectedina": [0.01, 0.05],    # Diluir em 500mL [cite: 668]
    "temozolomida": [2.5, 2.5],      # IV Raro: 2.5 mg/mL [cite: 648]
    "lurbinectedin": [0.02, 0.5],    # Diluir em bolsa [cite: 478]
    "topotecano": [0.02, 0.5],       # [cite: 663]
    
    # Correções de Faixas Amplas
    "bevacizumabe": [1.4, 16.5],     # Reforçando [cite: 130]
    "oxaliplatina": [0.2, 2.0],      # Reforçando [cite: 545]
    "paclitaxel": [0.3, 1.2]         # Reforçando [cite: 552]
}

def run():
    print("--- PREENCHENDO LACUNAS DO MÓDULO 2 ---")
    conn = sqlite3.connect('farmacia_clinica.db')
    cursor = conn.cursor()
    
    count = 0
    for nome_chave, faixas in updates.items():
        # Busca parcial pelo nome
        cursor.execute("SELECT id, name FROM medicamentos WHERE name LIKE ?", ('%'+nome_chave+'%',))
        rows = cursor.fetchall()
        
        for r in rows:
            # Só atualiza se estiver vazio ou zerado (para não sobrescrever o que já estava bom)
            # OU se for uma correção forçada (lista acima)
            mid = r[0]
            
            cursor.execute("UPDATE medicamentos SET concMin = ?, concMax = ? WHERE id = ?", (faixas[0], faixas[1], mid))
            print(f"[FIX] {r[1]}: {faixas[0]} - {faixas[1]}")
            count += 1

    conn.commit()
    conn.close()
    print(f"--- SUCESSO: {count} faixas complementares aplicadas. ---")

if __name__ == '__main__':
    run()
