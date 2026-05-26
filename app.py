import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES INICIAIS (Obrigatório ser o primeiro comando Streamlit)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide")

# Variáveis de Ambiente e Constantes
SUPABASE_URL   = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Você é um especialista técnico sênior em manutenção industrial, com mais de 20 anos de experiência nas seguintes áreas:
- Hidráulica Industrial (circuitos, componentes, óleos, simbologia ISO 1219, servo-hidráulica)
- Elétrica Industrial (instalações, motores, quadros de comando, NR-10, NBR 5410, NR-12)
- Eletrônica Industrial (componentes, inversores de frequência VFD, soft-starters, instrumentação)
- Eletromecânica (servo-motores, freios eletromagnéticos, CNC)
- Mecânica Industrial (transmissões, rolamentos, vedações, pneumática)
- Automação Industrial (CLPs, Ladder/FBD/ST, PID, Industria 4.0, IIoT)
- Redes Industriais (Ethernet/IP, Profibus, Modbus, Profinet, SCADA, HMI)
Quando houver CONHECIMENTO RELEVANTE DA BASE DE DADOS no contexto, use-o como referência principal, citando a fonte.
Use linguagem técnica precisa, cite normas (ISO, NBR, NR), ofereça procedimentos passo a passo.
Ao receber imagem, analise detalhadamente. Priorize sempre a segurança.
Responda sempre em português do Brasil."""

WELCOME_MSG = "Olá! Sou seu assistente técnico experiente. Estou aqui para diagnosticar problemas e sugerir soluções rápidas para seu equipamento. Como posso ajudar?"

# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE VISUAL (CSS BLINDADO)
# ══════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp, .main { background: #12151C !important; }
.block-container { padding: .8rem .8rem 5rem .8rem !important; max-width: 100% !important; }

/* Flexbox nativo para colunas Streamlit lado a lado sem quebra */
[data-testid="stColumns"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-start !important;
    gap: 16px !important;
}

/* Coluna da Esquerda (Painel Lateral Fixo) */
[data-testid="stColumns"] > div:nth-child(1) {
    min-width: 290px !important;
    max-width: 290px !important;
    flex: 0 0 290px !important;
    background: #1C2030 !important;
    border-radius: 12px !important;
    border: 1px solid #252B3B !important;
    padding: 16px 12px !important;
}

/* Coluna da Direita (Área Fluida do Chat) */
[data-testid="stColumns"] > div:nth-child(2) {
    flex: 1 1 auto !important;
    width: 100% !important;
}

.sec-title {
    font-size: .62rem; font-weight: 700; letter-spacing: 2px;
    color: #5A6478; text-transform: uppercase;
    border-bottom: 1px solid #252B3B; padding-bottom: 8px; margin-bottom: 12px;
}
.upload-label { font-size: .75rem; font-weight: 600; color: #8A96AD; margin-bottom: 6px; }
.upload-label span { font-weight: 400; color: #5A6478; }

[data-testid="stFileUploader"] { background: transparent !important; border: none !important; }
[data-testid="stFileDropzone"] {
    background: #12151C !important; border: 1.5px dashed #2D3448 !important;
    border-radius: 8px !important; padding: 10px !important;
}
[data-testid="stFileDropzone"] * { color: #8A96AD !important; }
[data-testid="stFileDropzone"] button {
    background: #252B3B !important; color: #C8D0E0 !important;
    border: 1px solid #363D55 !important; border-radius: 6px !important;
    font-size: .78rem !important; padding: 5px 14px !important;
}

.exp-item {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 10px; border-radius: 7px; margin-bottom: 3px;
    background: #12151C; border: 1px solid #1E2435;
    font-size: .81rem; color: #C0C8D8;
}
.exp-item .ei { font-size: 1rem; min-width: 18px; }

.status-pill {
    background: #1
