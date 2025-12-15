import os
import glob

print("--- DIAGNÓSTICO DE ARQUIVOS NA PASTA ---")
print(f"Diretório atual: {os.getcwd()}")
print("-" * 30)

# Busca todos os arquivos Excel e CSV
files = glob.glob("*.xlsx") + glob.glob("*.csv")
count = 0

if files:
    print("Arquivos encontrados (Excel e CSV):")
    print("-" * 30)
    for f in sorted(files):
        print(f"[{count}] {f}")
        count += 1
    print("-" * 30)
    print("Por favor, localize o arquivo que contém os dados dos 131 Protocolos (provavelmente NÃO é o PAMC).")
else:
    print("[AVISO] Nenhum arquivo Excel ou CSV encontrado na pasta.")
