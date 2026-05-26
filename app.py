import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES INICIAIS DA PÁGINA (Deve ser o primeiro comando Streamlit)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide")

# Varíaveis de Ambiente e Constantes
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
# CSS CUSTOMIZADO (Lado a Lado Estável)
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

/* Configuração de Flexbox para as colunas do Streamlit */
[data-testid="stColumns"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-start !important;
    gap: 16px !important;
}

/* Coluna Esquerda Fira */
[data-testid="stColumns"] > div:nth-child(1) {
    min-width: 290px !important;
    max-width: 290px !important;
    flex: 0 0 290px !important;
    background: #1C2030 !important;
    border-radius: 12px !important;
    border: 1px solid #252B3B !important;
    padding: 16px 12px !important;
}

/* Coluna Direita Fluida */
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
    background: #12151C; border: 1px solid #1E2435;
    border-radius: 8px; padding: 10px 14px; margin-top: 16px;
}
.status-pill .s-label { font-size: .6rem; color: #5A6478; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 3px; }
.status-pill .s-val   { font-size: .82rem; color: #2ECC71; font-weight: 600; }

.app-header {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 60%, #1A2035 100%);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 14px;
    border: 1px solid #2A3555; box-shadow: 0 6px 24px rgba(0,0,0,.3);
    display: flex; align-items: center; gap: 18px;
}
.icon-box {
    background: #252B3B; border-radius: 10px;
    width: 54px; height: 54px; display: flex; align-items: center;
    justify-content: center; font-size: 1.8rem; flex-shrink: 0;
    border: 1px solid #363D55;
}
.app-header h1 { color: #FFFFFF !important; font-size: 1.35rem; font-weight: 800; margin: 0 0 4px 0 !important; }
.app-header .sub { color: #7A8BAD !important; font-size: .78rem; margin: 0 !important; }

.stButton > button {
    background: #1C2030 !important; color: #C8D0E0 !important;
    border: 1px solid #2D3448 !important; border-radius: 10px !important;
    font-size: .83rem !important; font-weight: 500 !important;
    padding: 10px 12px !important; transition: all .2s !important;
}
.stButton > button:hover {
    background: #252B3B !important; border-color: #4A7AC8 !important;
    color: #FFFFFF !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(74,122,200,.15) !important;
}

[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 3px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; }

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1C2030 !important; border-radius: 4px 14px 14px 14px !important;
    padding: 12px 16px !important; border: 1px solid #252B3B !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #1A6B4A, #1E8A5E) !important;
    border-radius: 14px 4px 14px 14px !important; padding: 11px 15px !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #
