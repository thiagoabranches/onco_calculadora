import streamlit as st
import subprocess
import time
import requests
import os
import signal
import sys
import atexit

# 1. Configurações Iniciais
FLASK_PORT = 8000
FLASK_SERVER_URL = f"http://0.0.0.0:{FLASK_PORT}"

st.set_page_config(layout="wide")
st.title("OncoCalc Pro - Módulo Streamlit/Flask")

# Variável global para armazenar o processo Flask
flask_process = None

# Função de limpeza para encerrar o Flask ao sair do Streamlit
def kill_flask_process():
    global flask_process
    if flask_process:
        st.info("Encerrando servidor Flask...")
        flask_process.terminate()
        flask_process.wait()
        st.success("Servidor Flask encerrado.")

# Garante que o processo seja encerrado ao fechar a sessão
atexit.register(kill_flask_process)



# 2. Iniciar o Servidor Flask em Background (Agora, usa o comando ideal para Cloud)
def start_flask_server():
    global flask_process
    
    if flask_process is None:
        st.info("Iniciando servidor Flask em segundo plano...")
        
        # Chamada CORRIGIDA para Streamlit Cloud: Executa Gunicorn como um módulo Python
        command = [sys.executable, "-m", "gunicorn", "-w", "4", "-b", f"0.0.0.0:{FLASK_PORT}", "app:app"]
        
        try:
            flask_process = subprocess.Popen(command, 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                           preexec_fn=os.setsid) # Inicia em um novo grupo de processo
            time.sleep(5) 
            st.success(f"Servidor Flask iniciado na porta {FLASK_PORT}.")
            
            # Checagem de saúde (Health Check)
            requests.get(FLASK_SERVER_HEALTH_URL, timeout=10)

        except (FileNotFoundError, requests.exceptions.RequestException) as e:
            st.error(f"Falha Crítica ao iniciar o servidor Flask/Gunicorn: {e}")
            st.code(" ".join(command))
            return False
            
    return True



# Tenta iniciar o servidor
if start_flask_server():
    # 3. Incorporar o Conteúdo Flask via Iframe Nativo
    # Definindo o tamanho do iframe. Note que a altura deve ser grande para caber a interface.
    st.components.v1.iframe(FLASK_SERVER_URL, height=800, scrolling=True)

