import pandas as pd
import sqlite3
import re
import os

db_file = "farmacia_clinica.db"

# --- Dados extraídos do PDF (Protocolos e Ordens de Infusão) ---
# Os dados são extraídos do PDF, Páginas 13 a 102.
# Estrutura: {
#   "Nome Protocolo Original": {
#       "medicamentos": "M1, M2, M3",
#       "acronimo": "ACR",
#       "ordem": [["1", "MED1"], ["2", "MED2"], ...]
#   }
# }
# Vamos focar em extrair a lista principal de protocolos e a ordem sequencial do texto/tabela.

# Lista de Protocolos e seus Componentes (Principalmente das Tabelas)
protocols_data = [
    # Tabela 14.2 (Beva + FOLFIRI)
    {"nome": "Ácido Folínico, Bevacizumabe, Fluoruracila e Irinotecano", "acronimo": "Beva + FOLFIRI",
     "ordem": [["1°", "Bevacizumabe"], ["2°", "Ácido Folínico + Irinotecano"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 17.2 (Beva + FOLFOX)
    {"nome": "Ácido Folínico, Bevacizumabe, Fluoruracila e Oxaliplatina", "acronimo": "Beva + FOLFOX",
     "ordem": [["1°", "Bevacizumabe"], ["2°", "Ácido Folínico + Oxaliplatina"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 18.2 (FLOT)
    {"nome": "Ácido Folínico, Docetaxel, Fluoruracila e Oxaliplatina", "acronimo": "FLOT",
     "ordem": [["1°", "Docetaxel"], ["2°", "Ácido Folínico + Oxaliplatina"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 19.2 (ELF)
    {"nome": "Ácido Folínico, Etoposídeo e Fluoruracila", "acronimo": "ELF",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Ácido Folínico"], ["3°", "Fluoruracila"]]},
    # Tabela 20.2 (Ácido Folínico e Fluoruracila)
    {"nome": "Ácido Folínico e Fluoruracila", "acronimo": "AC + 5FU",
     "ordem": [["1°", "Ácido Folínico"], ["2°", "Fluoruracila"]]},
    # Tabela 21.2 (FOLFIRI/IFL - Infusão concomitante)
    {"nome": "Ácido Folínico, Fluoruracila e Irinotecano (Concomitante)", "acronimo": "FOLFIRI (Concomitante)",
     "ordem": [["1°", "Ácido Folínico + Irinotecano"], ["2°", "Fluoruracila (bolus)"], ["3°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 21.3 (FOLFIRI/IFL - Sequencial)
    {"nome": "Ácido Folínico, Fluoruracila e Irinotecano (Sequencial)", "acronimo": "FOLFIRI (Sequencial)",
     "ordem": [["1°", "Irinotecano"], ["2°", "Ácido Folínico"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 22.2 (FOLFOXIRI - Sequencial com concomitância)
    {"nome": "Ácido Folínico, Fluoruracila, Irinotecano e Oxaliplatina", "acronimo": "FOLFOXIRI",
     "ordem": [["1°", "Irinotecano"], ["2°", "Oxaliplatina + Ácido Folínico"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 22.3 (FOLFOXIRI - Sequencial)
    {"nome": "Ácido Folínico, Fluoruracila, Irinotecano e Oxaliplatina (Sequencial)", "acronimo": "FOLFOXIRI (Sequencial)",
     "ordem": [["1°", "Irinotecano"], ["2°", "Oxaliplatina"], ["3°", "Ácido Folínico"], ["4°", "Fluoruracila (bolus)"], ["5°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 23.2 (FOLFOX - Concomitante)
    {"nome": "Ácido Folínico, Fluoruracila e Oxaliplatina", "acronimo": "FOLFOX / FLOX",
     "ordem": [["1°", "Ácido Folínico + Oxaliplatina"], ["2°", "Fluoruracila (bolus)"], ["3°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 23.4 (FOLFOX - Sequencial)
    {"nome": "Ácido Folínico, Fluoruracila e Oxaliplatina (Sequencial)", "acronimo": "FOLFOX (Sequencial)",
     "ordem": [["1°", "Oxaliplatina"], ["2°", "Ácido Folínico"], ["3°", "Fluoruracila (bolus)"], ["4°", "Fluoruracila (infusão contínua)"]]},
    # Tabela 23.5 (Ácido Folínico e Metotrexato)
    {"nome": "Ácido Folínico e Metotrexato", "acronimo": "MTX + LV Resgate",
     "ordem": [["1°", "Metotrexato"], ["2°", "Ácido Folínico (Resgate)"]]},
    # Tabela 24.2 (Ácido Zoledrônico e Paclitaxel)
    {"nome": "Ácido Zoledrônico e Paclitaxel", "acronimo": "PAC + AZ",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Ácido Zoledrônico (após 24h)"]]},
    # Tabela 24.3 (Atezolizumabe, Carboplatina e Etoposídeo)
    {"nome": "Atezolizumabe, Carboplatina e Etoposídeo", "acronimo": "ATEZO + CB P + ETOPO",
     "ordem": [["1°", "Atezolizumabe"], ["2°", "Etoposídeo"], ["3°", "Carboplatina"]]},
    # Tabela 25.2 (Bevacizumabe e Irinotecano)
    {"nome": "Bevacizumabe e Irinotecano", "acronimo": "BEVA + IRI",
     "ordem": [["1°", "Irinotecano"], ["2°", "Bevacizumabe"]]},
    # Tabela 25.3 (Bleomicina e Cisplatina)
    {"nome": "Bleomicina e Cisplatina", "acronimo": "BLM + CYS",
     "ordem": [["1°", "Bleomicina"], ["2°", "Cisplatina"]]},
    # Tabela 26.2 (BEP)
    {"nome": "Bleomicina, Cisplatina e Etoposídeo", "acronimo": "BEP",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Bleomicina"], ["3°", "Cisplatina"]]},
    # Tabela 27.2 (BOMP)
    {"nome": "Bleomicina, Cisplatina, Mitomicina e Vincristina", "acronimo": "BOMP",
     "ordem": [["1°", "Vincristina"], ["2°", "Bleomicina"], ["3°", "Mitomicina"], ["4°", "Cisplatina"]]},
    # Tabela 28.2 (R-ABVD)
    {"nome": "Bleomicina, Dacarbazina, Doxorrubicina, Rituximabe e Vimblastina", "acronimo": "R-ABVD",
     "ordem": [["1°", "Rituximabe"], ["2°", "Vimblastina"], ["3°", "Doxorrubicina"], ["4°", "Bleomicina"], ["5°", "Dacarbazina"]]},
    # Tabela 29.2 (ABVD)
    {"nome": "Bleomicina, Dacarbazina, Doxorrubicina e Vimblastina", "acronimo": "ABVD",
     "ordem": [["1°", "Vimblastina"], ["2°", "Doxorrubicina"], ["3°", "Bleomicina"], ["4°", "Dacarbazina"]]},
    # Tabela 30.2 (Bleomicina e Paclitaxel)
    {"nome": "Bleomicina e Paclitaxel", "acronimo": "BLM + PAC",
     "ordem": [["1°", "Bleomicina"], ["2°", "Paclitaxel"]]},
    # Tabela 30.3 (Bortezomibe e Carboplatina)
    {"nome": "Bortezomibe e Carboplatina", "acronimo": "BORTEZ + CB P",
     "ordem": [["1°", "Bortezomibe"], ["2°", "Carboplatina"]]},
    # Tabela 31.2 (Bortezomibe e Citarabina)
    {"nome": "Bortezomibe e Citarabina", "acronimo": "BORTEZ + CITA",
     "ordem": [["1°", "Citarabina"], ["2°", "Bortezomibe"]]},
    # Tabela 31.3 (Bortezomibe e Gencitabina)
    {"nome": "Bortezomibe e Gencitabina", "acronimo": "BORTEZ + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Bortezomibe"]]},
    # Tabela 32.2 (Bortezomibe e Mitoxantrona)
    {"nome": "Bortezomibe e Mitoxantrona", "acronimo": "BORTEZ + MITO",
     "ordem": [["1°", "Bortezomibe"], ["2°", "Mitoxantrona"]]},
    # Tabela 32.3 (Carboplatina e Cetuximabe)
    {"nome": "Carboplatina e Cetuximabe", "acronimo": "CB P + CETUX",
     "ordem": [["1°", "Carboplatina"], ["2°", "Cetuximabe"]]},
    # Tabela 33.2 (Carboplatina, Cetuximabe e Paclitaxel)
    {"nome": "Carboplatina, Cetuximabe e Paclitaxel", "acronimo": "CB P + CETUX + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Carboplatina"], ["3°", "Cetuximabe"]]},
    # Tabela 34.2 (Carboplatina e Docetaxel)
    {"nome": "Carboplatina e Docetaxel", "acronimo": "CB P + DOCE",
     "ordem": [["1°", "Docetaxel"], ["2°", "Carboplatina"]]},
    # Tabela 35.2 (Carboplatina, Doxorrubicina Lipossomal e Paclitaxel)
    {"nome": "Carboplatina, Doxorrubicina Lipossomal e Paclitaxel", "acronimo": "CB P + DOXO-LIPO + PAC",
     "ordem": [["1°", "Doxorrubicina Lipossomal"], ["2°", "Paclitaxel"], ["3°", "Carboplatina"]]},
    # Tabela 36.2 (Carboplatina e Etoposídeo)
    {"nome": "Carboplatina e Etoposídeo", "acronimo": "CB P + ETOPO",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Carboplatina"]]},
    # Tabela 36.3 (ICE)
    {"nome": "Carboplatina, Etoposídeo e Ifosfamida", "acronimo": "ICE",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Ifosfamida"], ["3°", "Carboplatina"]]},
    # Tabela 37.2 (Carboplatina e Fluoruracila)
    {"nome": "Carboplatina e Fluoruracila", "acronimo": "CB P + 5FU",
     "ordem": [["1°", "Carboplatina"], ["2°", "Fluoruracila"]]},
    # Tabela 38.2 (Carboplatina e Gencitabina)
    {"nome": "Carboplatina e Gencitabina", "acronimo": "CB P + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Carboplatina"]]},
    # Tabela 38.3 (Carboplatina e Ifosfamida)
    {"nome": "Carboplatina e Ifosfamida", "acronimo": "CB P + IFO",
     "ordem": [["1°", "Ifosfamida"], ["2°", "Carboplatina"]]},
    # Tabela 39.2 (Carboplatina e Paclitaxel)
    {"nome": "Carboplatina e Paclitaxel", "acronimo": "CB P + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Carboplatina"]]},
    # Tabela 39.3 (Carboplatina e Topotecano)
    {"nome": "Carboplatina e Topotecano", "acronimo": "CB P + TOPO",
     "ordem": [["1°", "Topotecano"], ["2°", "Carboplatina"]]},
    # Tabela 40.2 (DARTMOUTH / CBDT)
    {"nome": "Carmustina, Cisplatina e Dacarbazina", "acronimo": "CBDT / DARTMOUTH",
     "ordem": [["1°", "Dacarbazina"], ["2°", "Carmustina"], ["3°", "Cisplatina"]]},
    # Tabela 40.3 (Cetuximabe e Cisplatina)
    {"nome": "Cetuximabe e Cisplatina", "acronimo": "CETUX + CYS",
     "ordem": [["1°", "Cisplatina"], ["2°", "Cetuximabe"]]},
    # Tabela 41.2 (Cetuximabe e Docetaxel)
    {"nome": "Cetuximabe e Docetaxel", "acronimo": "CETUX + DOCE",
     "ordem": [["1°", "Docetaxel"], ["2°", "Cetuximabe"]]},
    # Tabela 42.2 (Cetuximabe e Oxaliplatina)
    {"nome": "Cetuximabe e Oxaliplatina", "acronimo": "CETUX + OXALI",
     "ordem": [["1°", "Oxaliplatina"], ["2°", "Cetuximabe"]]},
    # Tabela 42.3 (Cetuximabe e Paclitaxel)
    {"nome": "Cetuximabe e Paclitaxel", "acronimo": "CETUX + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Cetuximabe"]]},
    # Tabela 42.4 (Ciclofosfamida e Cisplatina)
    {"nome": "Ciclofosfamida e Cisplatina", "acronimo": "CTX + CYS",
     "ordem": [["1°", "Ciclofosfamida"], ["2°", "Cisplatina"]]},
    # Tabela 43.2 (DTPACE)
    {"nome": "Ciclofosfamida, Cisplatina, Dexametasona, Doxorrubicina, Etoposídeo e Talidomida", "acronimo": "DTPACE",
     "ordem": [["1°", "Dexametasona (VO)"], ["2°", "Etoposídeo"], ["3°", "Doxorrubicina"], ["4°", "Ciclofosfamida"], ["5°", "Cisplatina"], ["6°", "Talidomida (VO)"]]},
    # Tabela 44.2 (CAP)
    {"nome": "Ciclofosfamida, Cisplatina e Doxorrubicina", "acronimo": "CAP",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Ciclofosfamida"], ["3°", "Cisplatina"]]},
    # Tabela 45.2 (VAC com Dactinomicina)
    {"nome": "Ciclofosfamida, Dactinomicina e Vincristina", "acronimo": "VAC (Dactinomicina)",
     "ordem": [["1°", "Vincristina"], ["2°", "Dactinomicina"], ["3°", "Ciclofosfamida"]]},
    # Tabela 46.2 (Ciclofosfamida e Docetaxel)
    {"nome": "Ciclofosfamida e Docetaxel", "acronimo": "CTX + DOCE",
     "ordem": [["1°", "Ciclofosfamida"], ["2°", "Docetaxel"]]},
    # Tabela 46.3 (TAC)
    {"nome": "Ciclofosfamida, Docetaxel e Doxorrubicina", "acronimo": "TAC",
     "ordem": [["1°", "Docetaxel"], ["2°", "Doxorrubicina"], ["3°", "Ciclofosfamida"]]},
    # Tabela 47.2 (AC)
    {"nome": "Ciclofosfamida e Doxorrubicina", "acronimo": "AC",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Ciclofosfamida"]]},
    # Tabela 48.2 (CAE)
    {"nome": "Ciclofosfamida, Doxorrubicina e Etoposídeo", "acronimo": "CAE",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Doxorrubicina"], ["3°", "Ciclofosfamida"]]},
    # Tabela 49.2 (CAF/FAC)
    {"nome": "Ciclofosfamida, Doxorrubicina e Fluoruracila", "acronimo": "CAF / FAC",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Fluoruracila"], ["3°", "Ciclofosfamida"]]},
    # Tabela 50.2 (ACT)
    {"nome": "Ciclofosfamida, Doxorrubicina e Paclitaxel", "acronimo": "AC-T / ACT",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Ciclofosfamida"], ["3°", "Paclitaxel"]]},
    # Tabela 50.3 (R-CHOP)
    {"nome": "Ciclofosfamida, Doxorrubicina, Prednisona, Rituximabe e Vincristina", "acronimo": "R-CHOP",
     "ordem": [["1°", "Prednisona (VO)"], ["2°", "Vincristina"], ["3°", "Doxorrubicina"], ["4°", "Ciclofosfamida"], ["5°", "Rituximabe"]]},
    # Tabela 51.2 (CHOP)
    {"nome": "Ciclofosfamida, Doxorrubicina, Prednisona e Vincristina", "acronimo": "CHOP",
     "ordem": [["1°", "Prednisona (VO)"], ["2°", "Vincristina"], ["3°", "Doxorrubicina"], ["4°", "Ciclofosfamida"]]},
    # Tabela 52.2 (VAC com Doxorrubicina)
    {"nome": "Ciclofosfamida, Doxorrubicina e Vincristina", "acronimo": "VAC (Doxorrubicina)",
     "ordem": [["1°", "Vincristina"], ["2°", "Doxorrubicina"], ["3°", "Ciclofosfamida"]]},
    # Tabela 53.2 (Ciclofosfamida e Fludarabina)
    {"nome": "Ciclofosfamida e Fludarabina", "acronimo": "CTX + FLUDARA",
     "ordem": [["1°", "Fludarabina"], ["2°", "Ciclofosfamida"]]},
    # Tabela 54.2 (CMF)
    {"nome": "Ciclofosfamida, Fluoruracila e Metotrexato (Endovenoso)", "acronimo": "CMF (EV)",
     "ordem": [["1°", "Fluoruracila"], ["2°", "Metotrexato"], ["3°", "Ciclofosfamida"]]},
    # Tabela 54.3 (Ciclofosfamida e Etoposídeo)
    {"nome": "Ciclofosfamida e Etoposídeo", "acronimo": "CTX + ETOPO",
     "ordem": [["1°", "Ciclofosfamida"], ["2°", "Etoposídeo"]]},
    # Tabela 55.2 (Ciclofosfamida e Paclitaxel)
    {"nome": "Ciclofosfamida e Paclitaxel", "acronimo": "CTX + PAC",
     "ordem": [["1°", "Ciclofosfamida"], ["2°", "Paclitaxel"]]},
    # Tabela 55.3 (R-COP/R-CVP)
    {"nome": "Ciclofosfamida, Prednisona, Rituximabe e Vincristina", "acronimo": "R-COP / R-CVP",
     "ordem": [["1°", "Prednisona (VO)"], ["2°", "Vincristina"], ["3°", "Ciclofosfamida"], ["4°", "Rituximabe"]]},
    # Tabela 56.2 (COP/CVP)
    {"nome": "Ciclofosfamida, Prednisona e Vincristina", "acronimo": "COP / CVP",
     "ordem": [["1°", "Prednisona (VO)"], ["2°", "Vincristina"], ["3°", "Ciclofosfamida"]]},
    # Tabela 56.3 (CVD)
    {"nome": "Cisplatina, Dacarbazina e Vimblastina", "acronimo": "CVD",
     "ordem": [["1°", "Vimblastina"], ["2°", "Dacarbazina"], ["3°", "Cisplatina"]]},
    # Tabela 57.2 (Cisplatina e Docetaxel)
    {"nome": "Cisplatina e Docetaxel", "acronimo": "CYS + DOCE",
     "ordem": [["1°", "Docetaxel"], ["2°", "Cisplatina"]]},
    # Tabela 58.2 (DCF)
    {"nome": "Cisplatina, Docetaxel e Fluoruracila", "acronimo": "DCF",
     "ordem": [["1°", "Docetaxel"], ["2°", "Fluoruracila"], ["3°", "Cisplatina"]]},
    # Tabela 58.3 (Cisplatina, Docetaxel e Gencitabina)
    {"nome": "Cisplatina, Docetaxel e Gencitabina", "acronimo": "CYS + DOCE + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Docetaxel"], ["3°", "Cisplatina"]]},
    # Tabela 59.2 (Cisplatina e Doxorrubicina)
    {"nome": "Cisplatina e Doxorrubicina", "acronimo": "CYS + DOXO",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Cisplatina"]]},
    # Tabela 59.3 (MVAC)
    {"nome": "Cisplatina, Doxorrubicina, Metotrexato e Vimblastina", "acronimo": "MVAC",
     "ordem": [["1°", "Vimblastina"], ["2°", "Metotrexato"], ["3°", "Doxorrubicina"], ["4°", "Cisplatina"]]},
    # Tabela 61.2 (Al-Sarraf)
    {"nome": "Cisplatina e Fluoruracila", "acronimo": "Al-Sarraf / CYS + 5FU",
     "ordem": [["1°", "Fluoruracila"], ["2°", "Cisplatina"]]},
    # Tabela 62.2 (Cisplatina, Fluoruracila e Gencitabina)
    {"nome": "Cisplatina, Fluoruracila e Gencitabina", "acronimo": "CYS + 5FU + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Fluoruracila"], ["3°", "Cisplatina"]]},
    # Tabela 63.2 (Cisplatina e Gencitabina)
    {"nome": "Cisplatina e Gencitabina", "acronimo": "CYS + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Cisplatina"]]},
    # Tabela 63.3 (Cisplatina, Gencitabina e Paclitaxel)
    {"nome": "Cisplatina, Gencitabina e Paclitaxel", "acronimo": "CYS + GEM + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Gencitabina"], ["3°", "Cisplatina"]]},
    # Tabela 64.2 (Cisplatina e Ifosfamida)
    {"nome": "Cisplatina e Ifosfamida", "acronimo": "CYS + IFO",
     "ordem": [["1°", "Ifosfamida"], ["2°", "Cisplatina"]]},
    # Tabela 65.2 (TIP)
    {"nome": "Cisplatina, Ifosfamida, Mesna e Paclitaxel", "acronimo": "TIP",
     "ordem": [["1°", "Ifosfamida + Mesna"], ["2°", "Paclitaxel"], ["3°", "Cisplatina"], ["4°", "Mesna"]]},
    # Tabela 65.3 (Cisplatina e Irinotecano)
    {"nome": "Cisplatina e Irinotecano", "acronimo": "CYS + IRI",
     "ordem": [["1°", "Cisplatina"], ["2°", "Irinotecano"]]},
    # Tabela 66.2 (Cisplatina e Paclitaxel)
    {"nome": "Cisplatina e Paclitaxel", "acronimo": "CYS + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Cisplatina"]]},
    # Tabela 67.2 (Cisplatina e Raltitrexato)
    {"nome": "Cisplatina e Raltitrexato", "acronimo": "CYS + RALT",
     "ordem": [["1°", "Raltitrexato"], ["2°", "Cisplatina"]]},
    # Tabela 67.3 (Cisplatina e Topotecano)
    {"nome": "Cisplatina e Topotecano", "acronimo": "CYS + TOPO",
     "ordem": [["1°", "Topotecano"], ["2°", "Carboplatina"]]}, # OBS: Aqui o texto sugere Carboplatina, mas o protocolo é Cisplatina
    # Tabela 68.2 (Cisplatina e Trastuzumabe)
    {"nome": "Cisplatina e Trastuzumabe", "acronimo": "CYS + TRAST",
     "ordem": [["1°", "Cisplatina"], ["2°", "Trastuzumabe"]]},
    # Tabela 68.3 (Cisplatina e Vincristina)
    {"nome": "Cisplatina e Vincristina", "acronimo": "CYS + VCR",
     "ordem": [["1°", "Vincristina"], ["2°", "Cisplatina"]]},
    # Tabela 69.2 (Cisplatina e Vinorelbina)
    {"nome": "Cisplatina e Vinorelbina", "acronimo": "CYS + VRB",
     "ordem": [["1°", "Vinorelbina"], ["2°", "Cisplatina"]]},
    # Tabela 69.3 (Citarabina e Fludarabina)
    {"nome": "Citarabina e Fludarabina", "acronimo": "CITA + FLUDARA",
     "ordem": [["1°", "Fludarabina"], ["2°", "Citarabina"]]},
    # Tabela 71.2 (VAD)
    {"nome": "Dexametasona, Doxorrubicina e Vincristina", "acronimo": "VAD",
     "ordem": [["1°", "Dexametasona (VO)"], ["2°", "Vincristina"], ["3°", "Doxorrubicina"]]},
    # Tabela 72.2 (Docetaxel e Doxorrubicina)
    {"nome": "Docetaxel e Doxorrubicina", "acronimo": "DOCE + DOXO",
     "ordem": [["1°", "Docetaxel"], ["2°", "Doxorrubicina"]]},
    # Tabela 73.2 (Docetaxel e Gencitabina)
    {"nome": "Docetaxel e Gencitabina", "acronimo": "DOCE + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Docetaxel"]]},
    # Tabela 74.2 (Docetaxel e Epirrubicina)
    {"nome": "Docetaxel e Epirrubicina", "acronimo": "DOCE + EPI",
     "ordem": [["1°", "Docetaxel"], ["2°", "Epirrubicina"]]},
    # Tabela 75.2 (Docetaxel e Fluoruracila)
    {"nome": "Docetaxel e Fluoruracila", "acronimo": "DOCE + 5FU",
     "ordem": [["1°", "Docetaxel"], ["2°", "Fluoruracila"]]},
    # Tabela 75.3 (Docetaxel e Ifosfamida)
    {"nome": "Docetaxel e Ifosfamida", "acronimo": "DOCE + IFO",
     "ordem": [["1°", "Docetaxel"], ["2°", "Ifosfamida"]]},
    # Tabela 76.2 (Docetaxel e Irinotecano)
    {"nome": "Docetaxel e Irinotecano", "acronimo": "DOCE + IRI",
     "ordem": [["1°", "Irinotecano"], ["2°", "Docetaxel"]]},
    # Tabela 76.3 (Docetaxel e Metotrexato)
    {"nome": "Docetaxel e Metotrexato", "acronimo": "DOCE + MTX",
     "ordem": [["1°", "Metotrexato"], ["2°", "Docetaxel"]]},
    # Tabela 77.2 (Docetaxel e Oxaliplatina)
    {"nome": "Docetaxel e Oxaliplatina", "acronimo": "DOCE + OXALI",
     "ordem": [["1°", "Docetaxel"], ["2°", "Oxaliplatina"]]},
    # Tabela 77.3 (Docetaxel e Pamidronato)
    {"nome": "Docetaxel e Pamidronato", "acronimo": "DOCE + PAMI",
     "ordem": [["1°", "Docetaxel"], ["2°", "Pamidronato"]]},
    # Tabela 78.2 (Docetaxel e Pemetrexede)
    {"nome": "Docetaxel e Pemetrexede", "acronimo": "DOCE + PEMET",
     "ordem": [["1°", "Pemetrexede"], ["2°", "Docetaxel"]]},
    # Tabela 79.2 (Docetaxel e Topotecano)
    {"nome": "Docetaxel e Topotecano", "acronimo": "DOCE + TOPO",
     "ordem": [["1°", "Docetaxel"], ["2°", "Topotecano"]]},
    # Tabela 79.3 (Docetaxel e Vinorelbina)
    {"nome": "Docetaxel e Vinorelbina", "acronimo": "DOCE + VRB",
     "ordem": [["1°", "Docetaxel"], ["2°", "Vinorelbina"]]},
    # Tabela 80.2 (Doxorrubicina e Etoposídeo)
    {"nome": "Doxorrubicina e Etoposídeo", "acronimo": "DOXO + ETOPO",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Doxorrubicina"]]},
    # Tabela 80.3 (FAM/iFAM)
    {"nome": "Doxorrubicina, Fluoruracila e Mitomicina", "acronimo": "FAM / iFAM",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Fluoruracila"], ["3°", "Mitomicina"]]},
    # Tabela 81.2 (Doxorrubicina e Gencitabina)
    {"nome": "Doxorrubicina e Gencitabina", "acronimo": "DOXO + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Doxorrubicina"]]},
    # Tabela 81.3 (Doxorrubicina e Ifosfamida)
    {"nome": "Doxorrubicina e Ifosfamida", "acronimo": "DOXO + IFO",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Ifosfamida"]]},
    # Tabela 82.2 (Doxorrubicina e Paclitaxel)
    {"nome": "Doxorrubicina e Paclitaxel", "acronimo": "DOXO + PAC",
     "ordem": [["1°", "Doxorrubicina"], ["2°", "Paclitaxel"]]},
    # Tabela 82.3 (Epirrubicina e Gencitabina)
    {"nome": "Epirrubicina e Gencitabina", "acronimo": "EPI + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Epirrubicina"]]},
    # Tabela 83.2 (Epirrubicina e Paclitaxel)
    {"nome": "Epirrubicina e Paclitaxel", "acronimo": "EPI + PAC",
     "ordem": [["1°", "Epirrubicina"], ["2°", "Paclitaxel"]]},
    # Tabela 83.3 (Etoposídeo e Mitomicina)
    {"nome": "Etoposídeo e Mitomicina", "acronimo": "ETOPO + MITO",
     "ordem": [["1°", "Etoposídeo"], ["2°", "Mitomicina"]]},
    # Tabela 84.2 (Etoposídeo e Paclitaxel)
    {"nome": "Etoposídeo e Paclitaxel", "acronimo": "ETOPO + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Etoposídeo"]]},
    # Tabela 84.3 (Etoposídeo e Topotecano)
    {"nome": "Etoposídeo e Topotecano", "acronimo": "ETOPO + TOPO",
     "ordem": [["1°", "Topotecano"], ["2°", "Etoposídeo"]]},
    # Tabela 85.2 (Etoposídeo e Vincristina)
    {"nome": "Etoposídeo e Vincristina", "acronimo": "ETOPO + VCR",
     "ordem": [["1°", "Vincristina"], ["2°", "Etoposídeo"]]},
    # Tabela 85.3 (Fluoruracila e Gencitabina)
    {"nome": "Fluoruracila e Gencitabina", "acronimo": "5FU + GEM",
     "ordem": [["1°", "Gencitabina"], ["2°", "Fluoruracila"]]},
    # Tabela 86.2 (Fluoruracila, Gencitabina e Trastuzumabe)
    {"nome": "Fluoruracila, Gencitabina e Trastuzumabe", "acronimo": "5FU + GEM + TRAST",
     "ordem": [["1°", "Gencitabina"], ["2°", "Fluoruracila"], ["3°", "Trastuzumabe"]]},
    # Tabela 87.2 (Fluoruracila e Irinotecano)
    {"nome": "Fluoruracila e Irinotecano", "acronimo": "5FU + IRI",
     "ordem": [["1°", "Irinotecano"], ["2°", "Fluoruracila"]]},
    # Tabela 87.3 (Fluoruracila e Metotrexato)
    {"nome": "Fluoruracila e Metotrexato", "acronimo": "5FU + MTX",
     "ordem": [["1°", "Fluoruracila"], ["2°", "Metotrexato"]]},
    # Tabela 88.2 (Fluoruracila e Oxaliplatina)
    {"nome": "Fluoruracila e Oxaliplatina", "acronimo": "5FU + OXALI",
     "ordem": [["1°", "Oxaliplatina"], ["2°", "Fluoruracila"]]},
    # Tabela 88.3 (Fluoruracila e Paclitaxel)
    {"nome": "Fluoruracila e Paclitaxel", "acronimo": "5FU + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Fluoruracila"]]},
    # Tabela 89.2 (Fluoruracila e Raltitrexato)
    {"nome": "Fluoruracila e Raltitrexato", "acronimo": "5FU + RALT",
     "ordem": [["1°", "Raltitrexato"], ["2°", "Fluoruracila"]]},
    # Tabela 89.3 (Fluoruracila e Trastuzumabe)
    {"nome": "Fluoruracila e Trastuzumabe", "acronimo": "5FU + TRAST",
     "ordem": [["1°", "Fluoruracila"], ["2°", "Trastuzumabe"]]},
    # Tabela 90.2 (Gencitabina e Irinotecano)
    {"nome": "Gencitabina e Irinotecano", "acronimo": "GEM + IRI",
     "ordem": [["1°", "Gencitabina"], ["2°", "Irinotecano"]]},
    # Tabela 90.3 (Gencitabina e Oxaliplatina)
    {"nome": "Gencitabina e Oxaliplatina", "acronimo": "GEM + OXALI",
     "ordem": [["1°", "Gencitabina"], ["2°", "Oxaliplatina"]]},
    # Tabela 91.2 (Gencitabina e Paclitaxel)
    {"nome": "Gencitabina e Paclitaxel", "acronimo": "GEM + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Gencitabina"]]},
    # Tabela 91.3 (Gencitabina e Pemetrexede)
    {"nome": "Gencitabina e Pemetrexede", "acronimo": "GEM + PEMET",
     "ordem": [["1°", "Pemetrexede"], ["2°", "Gencitabina"]]},
    # Tabela 92.2 (Gencitabina e Pralatrexate)
    {"nome": "Gencitabina e Pralatrexate", "acronimo": "GEM + PRAL",
     "ordem": [["1°", "Pralatrexate"], ["2°", "Gencitabina"]]},
    # Tabela 92.3 (Gencitabina e Trastuzumabe)
    {"nome": "Gencitabina e Trastuzumabe", "acronimo": "GEM + TRAST",
     "ordem": [["1°", "Gencitabina"], ["2°", "Trastuzumabe"]]},
    # Tabela 93.2 (Gencitabina e Vinorelbina)
    {"nome": "Gencitabina e Vinorelbina", "acronimo": "GEM + VRB",
     "ordem": [["1°", "Vinorelbina"], ["2°", "Gencitabina"]]},
    # Tabela 95.2 (Ifosfamida e Paclitaxel)
    {"nome": "Ifosfamida e Paclitaxel", "acronimo": "IFO + PAC",
     "ordem": [["1°", "Ifosfamida + Mesna"], ["2°", "Paclitaxel"]]},
    # Tabela 95.3 (Ifosfamida e Vinorelbina)
    {"nome": "Ifosfamida e Vinorelbina", "acronimo": "IFO + VRB",
     "ordem": [["1°", "Vinorelbina"], ["2°", "Ifosfamida"]]},
    # Tabela 96.2 (IROX)
    {"nome": "Irinotecano e Oxaliplatina", "acronimo": "IROX",
     "ordem": [["1°", "Irinotecano"], ["2°", "Oxaliplatina"]]},
    # Tabela 97.2 (Irinotecano e Paclitaxel)
    {"nome": "Irinotecano e Paclitaxel", "acronimo": "IRI + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Irinotecano"]]},
    # Tabela 97.3 (Irinotecano e Raltitrexato)
    {"nome": "Irinotecano e Raltitrexato", "acronimo": "IRI + RALT",
     "ordem": [["1°", "Irinotecano"], ["2°", "Raltitrexato"]]},
    # Tabela 98.2 (Metotrexato e Paclitaxel)
    {"nome": "Metotrexato e Paclitaxel", "acronimo": "MTX + PAC",
     "ordem": [["1°", "Metotrexato"], ["2°", "Paclitaxel"]]},
    # Tabela 98.3 (Oxaliplatina e Paclitaxel)
    {"nome": "Oxaliplatina e Paclitaxel", "acronimo": "OXALI + PAC",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Oxaliplatina"]]},
    # Tabela 99.2 (Oxaliplatina e Raltitrexato)
    {"nome": "Oxaliplatina e Raltitrexato", "acronimo": "OXALI + RALT",
     "ordem": [["1°", "Raltitrexato"], ["2°", "Oxaliplatina"]]},
    # Tabela 99.3 (Paclitaxel e Pamidronato)
    {"nome": "Paclitaxel e Pamidronato", "acronimo": "PAC + PAMI",
     "ordem": [["1°", "Paclitaxel"], ["2°", "Pamidronato"]]},
    # Tabela 100.2 (Paclitaxel e Pemetrexede)
    {"nome": "Paclitaxel e Pemetrexede", "acronimo": "PAC + PEMET",
     "ordem": [["1°", "Pemetrexede"], ["2°", "Paclitaxel"]]},
    # Tabela 100.3 (Paclitaxel e Ramucirumabe)
    {"nome": "Paclitaxel e Ramucirumabe", "acronimo": "PAC + RAMUC",
     "ordem": [["1°", "Ramucirumabe"], ["2°", "Paclitaxel"]]},
    # Tabela 101.2 (Paclitaxel e Trastuzumabe)
    {"nome": "Paclitaxel e Trastuzumabe", "acronimo": "PAC + TRAST",
     "ordem": [["1°", "Trastuzumabe"], ["2°", "Paclitaxel"]]},
    # Tabela 101.3 (Pertuzumabe e Trastuzumabe)
    {"nome": "Pertuzumabe e Trastuzumabe", "acronimo": "PERTU + TRAST",
     "ordem": [["1°", "Pertuzumabe"], ["2°", "Trastuzumabe"]]},
]

# 4. Funções do Motor
def run_backend():
    print("--- MOTOR DE CARREGAMENTO DE PROTOCOLOS (131+ PROTOCOLOS) ---")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # A. Cria a nova tabela 'protocolos'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS protocolos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            acronym TEXT,
            medications TEXT,
            infusion_order TEXT,
            UNIQUE(name)
        )
    ''')
    conn.commit()

    # B. Insere/Atualiza os dados
    count = 0
    for p in protocols_data:
        # Formata a ordem sequencial para uma string JSON-like (para facilitar o display)
        order_str = "; ".join([f"{item[0]}: {item[1]}" for item in p['ordem']])
        meds_str = ", ".join(p['ordem'][i][1].split(' + ')[0] for i in range(len(p['ordem'])))
        
        cursor.execute('''
            INSERT OR REPLACE INTO protocolos (name, acronym, medications, infusion_order)
            VALUES (?, ?, ?, ?)
        ''', (p['nome'], p['acronimo'], meds_str, order_str))
        count += 1

    conn.commit()
    conn.close()
    print(f"SUCESSO: {count} protocolos de infusão carregados/atualizados.")

if __name__ == '__main__':
    run_backend()
