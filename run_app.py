import streamlit as st
import subprocess
import time
import requests
from streamlit_html_component import html_component
import os

# 1. Configurações Iniciais
FLASK_PORT = 8000
FLASK_SERVER_URL = f"http://localhost:{FLASK_PORT}"

st.set_page_config(layout="wide")

# 2. Iniciar o Servidor Flask em Background
@st.cache_resource(ttl=3600)
def start_flask_server():
    st.info("Iniciando servidor Flask em segundo plano...")
    
    # Comando robusto para Streamlit Cloud
    command = ["gunicorn", "-w", "4", "-b", f"0.0.0.0:{FLASK_PORT}", "app:app"]
    
    try:
        process = subprocess.Popen(command, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        st.warning("Gunicorn não encontrado. Tentando iniciar com 'python app.py'.")
        command_fallback = ["python", "app.py"]
        process = subprocess.Popen(command_fallback, env=os.environ.copy())
    
    time.sleep(5) 
    
    # Verifica se o servidor Flask está online
    try:
        requests.get(FLASK_SERVER_URL, timeout=10)
        st.success(f"Servidor Flask iniciado com sucesso na porta {FLASK_PORT}.")
    except requests.exceptions.ConnectionError:
        st.error("Erro: Servidor Flask não iniciou ou a porta está inacessível.")
        
    return process

# 3. Execução Principal
flask_process = start_flask_server()

# 4. Tenta buscar o conteúdo HTML gerado pelo Flask e exibir
try:
    # Tenta obter o HTML do Flask
    response = requests.get(FLASK_SERVER_URL, timeout=30)
    
    if response.status_code == 200:
        # Exibe o conteúdo HTML gerado pelo Flask
        html_component(response.text, height=1000, width="100%", scrolling=True)
        st.info("Interface servida pelo Flask incorporada ao Streamlit.")
    else:
        st.error(f"Erro ao carregar a página: Código de status {response.status_code}. O Flask pode ter falhado.")

except requests.exceptions.RequestException as e:
    st.error(f"Erro crítico de conexão: O Flask não respondeu. {e}")

