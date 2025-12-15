import os

print("--- CONTEÚDO DA PASTA ---")
print(f"Diretório: {os.getcwd()}")
print("-" * 30)

arquivos = os.listdir('.')
count = 0

for f in arquivos:
    # Filtra apenas arquivos que nos interessam (Excel e CSV)
    if f.lower().endswith(('.xlsx', '.xls', '.csv')):
        print(f"[{count}] {f}")
        count += 1

if count == 0:
    print("[AVISO] Nenhum Excel ou CSV encontrado.")
else:
    print("-" * 30)
    print("Copie a lista acima e cole no chat.")
