import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os

# ── Configurações ─────────────────────────────────────────────────────────────
SUPABASE_URL   = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Você é um especialista técnico sênior em manutenção industrial, com mais de 20 anos de experiência em Hidráulica, Elétrica, Eletrônica, Eletromecânica, Mecânica, Automação e Redes Industriais. Responda sempre em português do Brasil de forma precisa e profissional."""

WELCOME_MSG = "Olá! Sou seu assistente técnico experiente. Estou aqui para diagnosticar problemas e sugerir soluções rápidas para seu equipamento. Como posso ajudar?"

# ── CSS Avançado de Posicionamento Fixo (Evita quebras e tela branca) ──────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { 
    font-family: 'Inter', sans-serif !important; 
    box-sizing: border-box;
}

/* Ocultar cabeçalhos inúteis do Streamlit */
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Configuração do fundo principal */
.stApp, .main { 
    background-color: #12151C !important; 
}

/* Ajusta o espaçamento da página inteira */
.block-container { 
    padding: 20px !important; 
    max-width: 100% !important; 
}

/* 🏢 FORÇAR LAYOUT LADO A LADO VIA CSS CONVENIENTE */
/* Aplica comportamento de container nas colunas do Streamlit sem quebrar */
[data-testid="stColumns"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-start !important;
    gap: 20px !important;
}

/* Garante que a coluna esquerda (Menu) mantenha largura fixa rígida */
[data-testid="stColumns"] > div:nth-child(1) {
    min-width: 290px !important;
    max-width: 290px !important;
    flex: 0 0 290px !important;
    background: #1C2030 !important;
    border-radius: 12px !important;
    border: 1px solid #252B3B !important;
    padding: 20px 14px !important;
}

/* Garante que a coluna direita (Chat) ocupe todo o resto da tela */
[data-testid="stColumns"] > div:nth-child(2) {
    flex: 1 1 auto !important;
    width: 100% !important;
}

/* Títulos de Seção */
.sec-title {
    font-size: 11px !important; 
    font-weight: 700 !important; 
    letter-spacing: 1.5px;
    color: #64748B; 
    text-transform: uppercase;
    border-bottom: 1px solid #252B3B; 
    padding-bottom: 6px; 
    margin-bottom: 14px;
    margin-top: 10px;
}

/* Estilização limpa do File Uploader */
.upload-label {
    font-size: 13px !important; 
    font-weight: 600 !important; 
    color: #E2E8F0; 
    margin-bottom: 6px;
}
.upload-label span { font-weight: 400; color: #64748B; }

[data-testid="stFileUploader"] { background: transparent !important; border: none !important; }
[data-testid="stFileDropzone"] {
    background: #12151C !important; 
    border: 1.5px dashed #334155 !important;
    border-radius: 8px !important; 
    padding: 12px !important;
}
[data-testid="stFileDropzone"] button {
    background: #252B3B !important; 
    color: #FFFFFF !important;
    border: 1px solid #334155 !important; 
    font-size: 12px !important; 
    width: 100%;
}

/* Lista de Especialidades */
.exp-item {
    display: flex; 
    align-items: center; 
    gap: 10px;
    padding: 8px 12px; 
    border-radius: 6px; 
    margin-bottom: 6px;
    background: #12151C; 
    border: 1px solid #252B3B;
    font-size: 13px !important; 
    color: #E2E8F0;
}
.exp-item .ei { font-size: 16px !important; }

/* Status */
.status-pill {
    background: #12151C; 
    border: 1px solid #252B3B;
    border-radius: 8px; 
    padding: 12px; 
    margin-top: 15px;
}
.status-pill .s-label { font-size: 10px !important; color: #64748B; text-transform: uppercase; }
.status-pill .s-val { font-size: 13px !important; color: #2ECC71; font-weight: 600; }

/* Header do Chat */
.app-header {
    background: linear-gradient(135deg, #1C2030 0%, #12151C 100%);
    border-radius: 12px; 
    padding: 20px 24px; 
    margin-bottom: 20px;
    border: 1px solid #252B3B; 
    border-left: 6px solid #007ACC; 
    display: flex; 
    align-items: center; 
    gap: 16px;
}
.icon-box {
    background: #252B3B; border-radius: 8px;
    width: 50px; height: 50px; display: flex; align-items: center;
    justify-content: center; font-size: 24px !important; flex-shrink: 0;
}
.app-header h1 { color: #FFFFFF !important; font-size: 20px !important; font-weight: 700 !important; margin: 0 !important; }
.app-header .sub { color: #94A3B8 !important; font-size: 13px !important; margin: 4px 0 0 0 !important; }

/* Estilização dos Botões Nativos */
.stButton > button {
    background: #1C2030 !important; 
    color: #C8D0E0 !important;
    border: 1px solid #252B3B !important; 
    border-radius: 8px !important;
    font-size: 13px !important; 
    padding: 10px 12px !important;
}
.stButton > button:hover {
    border-color: #007ACC !important;
    color: #FFFFFF !important;
}

/* Balões das Mensagens */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 10px 0 !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1C2030 !important; border-radius: 4px 12px 12px 12px !important; padding: 14px 18px !important; border: 1px solid #252B3B !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #165339, #1E724E) !important; border-radius: 12px 4px 12px 12px !important; padding: 14px 18px !important;
}
[data-testid="stChatMessage"] p { color: #E2E8F0 !important; font-size: 14px !important; }

/* Input fixo inferior */
[data-testid="stBottom"] { background: #12151C !important; border-top: 1px solid #252B3B !important; padding: 15px 0 !important; }
[data-testid="stChatInput"] { background: #1C2030 !important; border: 1.5px solid #252B3B !important; border-radius: 10px !important; }
</style>
"""

# ── Backend helpers ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def search_knowledge(q, sb):
    try: return sb.rpc("buscar_conhecimento", {"consulta": q, "max_resultados": 4}).execute().data or []
    except: return []

def count_docs(sb):
    try: return sb.table("knowledge_base").select("id",count="exact").execute().count or 0
    except: return 0

def stream_groq(msgs, key, model):
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    b = {"model": model, "messages": msgs, "stream": True, "temperature": 0.7, "max_tokens": 4096}
    with requests.post(GROQ_URL, headers=h, json=b, stream=True, timeout=120) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                d = line.decode("utf-8")
                if d.startswith("data: "):
                    s = d[6:].strip()
                    if s == "[DONE]": break
                    try:
                        c = json.loads(s)["choices"][0]["delta"].get("content","")
                        if c: yield c
                    except: pass

def do_chat(prompt, image_bytes, mime_type, sb, kb_count):
    rag = ""
    if sb and kb_count > 0:
        results = search_knowledge(prompt, sb)
        if results:
            rag = "\n\n---\n**CONHECIMENTO DA BASE:**\n" + "".join(f"\n📚 [{r['title']}]:\n{r['content']}\n" for r in results) + "---\n"
    
    api = [{"role": "system", "content": SYSTEM_PROMPT + rag}]
    for m in st.session_state.messages[:-1]:
        if m.get("role") in ["user", "assistant"]: 
            api.append({"role": m["role"], "content": m["content"]})
            
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        api.append({"role": "user", "content": [
            {"type": "text", "text": prompt + rag},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
        ]})
        model = VISION_MODEL
    else:
        api.append({"role": "user", "content": prompt})
        model = TEXT_MODEL
        
    with st.chat_message("assistant", avatar="🔧"):
        ph = st.empty()
        full = ""
        try:
            for chunk in stream_groq(api, GROQ_API_KEY, model):
                full += chunk
                ph.markdown(full + "▌")
            ph.markdown(full)
        except requests.HTTPError as e:
            ph.error(f"Erro {e.response.status_code}")
    return full

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada.")
    st.stop()

sb
