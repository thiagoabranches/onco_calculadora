import os

print("--- LISTA DE ARQUIVOS ---")
cwd = os.getcwd()
print(f"Pasta: {cwd}")
print("-" * 30)

arquivos = [f for f in os.listdir('.') if os.path.isfile(f)]
csv_encontrado = False

for f in arquivos:
    # Verifica extensoes
    if f.lower().endswith(('.csv', '.xlsx', '.xls')):
        print(f"[ALVO] {f}")
        csv_encontrado = True
    else:
        print(f"       {f}")

print("-" * 30)
if not csv_encontrado:
    print("AVISO: Nenhum arquivo de dados (.csv ou .xlsx) encontrado nesta pasta.")
    print("ACAO: Voce precisa salvar o arquivo da planilha DENTRO desta pasta antes de continuar.")
else:
    print("OK: Arquivo de dados encontrado. Copie o nome exato dele.")
