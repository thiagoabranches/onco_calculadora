import os

print("--- DIAGNÓSTICO DE ARQUIVOS ---")
print(f"Diretório de execução: {os.getcwd()}")
print("-" * 30)

arquivos = [f for f in os.listdir('.') if os.path.isfile(f)]
encontrados = False

for f in arquivos:
    # Destaca CSVs e Excels
    if f.endswith('.csv') or f.endswith('.xlsx') or f.endswith('.xls'):
        print(f"📄 [ALVO] {f}")
        encontrados = True
    else:
        print(f"   {f}")

print("-" * 30)
if not encontrados:
    print("❌ NENHUM arquivo CSV ou Excel encontrado nesta pasta!")
else:
    print("✅ Copie o nome exato do arquivo [ALVO] acima.")
