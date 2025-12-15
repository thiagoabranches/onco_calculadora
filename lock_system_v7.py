import shutil
import os
import datetime

def lock_system():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_v7_completo_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    print(f"--- BLINDAGEM DO SISTEMA (V7) ---")
    print(f"Criando snapshot em: {backup_dir}")
    
    # 1. Backup do Banco de Dados (Ouro)
    if os.path.exists('farmacia_clinica.db'):
        shutil.copy2('farmacia_clinica.db', f"{backup_dir}/farmacia_clinica.db")
        print(" [OK] Banco de Dados salvo.")
    else:
        print(" [ERRO] Banco de dados não encontrado!")

    # 2. Backup do Front-end (HTML)
    if os.path.exists('templates/index.html'):
        shutil.copy2('templates/index.html', f"{backup_dir}/index.html")
        print(" [OK] Interface HTML salva.")
    else:
        print(" [ERRO] Template HTML não encontrado!")
        
    # 3. Criar arquivo de manifesto
    with open(f"{backup_dir}/manifesto.txt", "w") as f:
        f.write("Estado V7 Completo: Módulos 1 a 7 implementados.\n")
        f.write("Inclui: Marcas, Faixas, Obs, Parametros, Fisico-Quimico (NIOSH), Estabilidade, Clinica.\n")
        
    print("-" * 30)
    print("SISTEMA BLINDADO. Pode iniciar alterações de layout com segurança.")

if __name__ == '__main__':
    lock_system()
