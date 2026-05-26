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

# ── CSS Corrigido para Escalonamento e Proporções de Tela Reais ────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Reset Geral e Fontes Legíveis */
* { 
    font-family: 'Inter', sans-serif !important; 
    box-sizing: border-box; 
}

/* Ocultar Elementos Nativos Invasivos do Streamlit */
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Configuração do Background Grafite Premium */
.stApp, .main { 
    background-color: #161920 !important; 
}
.block-container { 
    padding: 1.5rem 2rem 6rem 2rem !important; 
    max-width: 95% !important; 
}

/* ═══════════════════════════════
   PAINEL ESQUERDO (COLUNA TÉCNICA)
═══════════════════════════════ */
.left-col {
    background: #1F232E;
    border-radius: 12px;
    border: 1px solid #2D3446;
    padding: 24px 18px;
    min-height: 82vh;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.sec-title {
    font-size: 0.75rem; 
    font-weight: 700; 
    letter-spacing: 1.5px;
    color: #7E8B9B; 
    text-transform: uppercase;
    border-bottom: 1px solid #2D3446; 
    padding-bottom: 10px; 
    margin-bottom: 16px;
    margin-top: 12px;
}
.upload-label {
    font-size: 0.85rem; 
    font-weight: 600; 
    color: #E2E8F0; 
    margin-bottom: 10px;
}
.upload-label span { 
    font-weight: 400; 
    color: #7E8B9B; 
}

/* Customização do Box de Arrastar Arquivos */
[data-testid="stFileUploader"] { background: transparent !important; border: none !important; }
[data-testid="stFileDropzone"] {
    background: #161920 !important; 
    border: 1.5px dashed #3A4356 !important;
    border-radius: 8px !important; 
    padding: 16px !important;
}
[data-testid="stFileDropzone"] * { color: #A0AEC0 !important; }
[data-testid="stFileDropzone"] button {
    background: #2D3446 !important; 
    color: #FFFFFF !important;
    border: 1px solid #3A4356 !important; 
    border-radius: 6px !important;
    font-size: 0.85rem !important; 
    padding: 8px 16px !important;
    width: 100%;
}

/* Estilização da Lista de Especialidades */
.exp-item {
    display: flex; 
    align-items: center; 
    gap: 12px;
    padding: 10px 14px; 
    border-radius: 8px; 
    margin-bottom: 6px;
    background: #161920; 
    border: 1px solid #2D3446;
    font-size: 0.9rem; 
    color: #C2CEDA;
}
.exp-item .ei { 
    font-size: 1.1rem; 
    min-width: 22px; 
}

/* Indicador de Status Base */
.status-pill {
    background: #161920; 
    border: 1px solid #2D3446;
    border-radius: 8px; 
    padding: 14px; 
    margin-top: 24px;
}
.status-pill .s-label { 
    font-size: 0.65rem; 
    color: #7E8B9B; 
    text-transform: uppercase; 
    letter-spacing: 1.5px; 
    margin-bottom: 6px; 
}
.status-pill .s-val { 
    font-size: 0.9rem; 
    color: #2ECC71; 
    font-weight: 600; 
}

/* ═══════════════════════════════
   HEADER PRINCIPAL DO DIAGNÓSTICO
═══════════════════════════════ */
.app-header {
    background: linear-gradient(135deg, #1F232E 0%, #161920 100%);
    border-radius: 12px; 
    padding: 26px 30px; 
    margin-bottom: 22px;
    border: 1px solid #2D3446; 
    border-left: 6px solid #007ACC; /* Destaque azul de óleo industrial */
    box-shadow: 0 4px 15px rgba(0,0,0,.25);
    display: flex; 
    align-items: center; 
    gap: 22px;
}
.icon-box {
    background: #2D3446; 
    border-radius: 10px;
    width: 64px; 
    height: 64px; 
    display: flex; 
    align-items: center;
    justify-content: center; 
    font-size: 2rem; 
    flex-shrink: 0;
    border: 1px solid #3A4356;
}
.app-header h1 { 
    color: #FFFFFF !important; 
    font-size: 1.75rem !important; 
    font-weight: 700 !important; 
    margin: 0 0 6px 0 !important; 
    letter-spacing: 0.5px; 
}
.app-header .sub { 
    color: #90A0B2 !important; 
    font-size: 0.95rem !important; 
    margin: 0 !important; 
}

/* ═══════════════════════════════
   BOTÕES DE INTERAÇÃO RÁPIDA
═══════════════════════════════ */
.stButton > button {
    background: #1F232E !important; 
    color: #E2E8F0 !important;
    border: 1px solid #2D3446 !important; 
    border-radius: 8px !important;
    font-size: 0.95rem !important; 
    font-weight: 600 !important;
    padding: 14px 16px !important; 
    transition: all .2s ease !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.stButton > button:hover {
    background: #252A38 !important; 
    border-color: #007ACC !important;
    color: #FFFFFF !important; 
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 122, 204, 0.25) !important;
}

/* ═══════════════════════════════
   MENSAGENS E HISTÓRICO DO CHAT
═══════════════════════════════ */
[data-testid="stChatMessage"] { 
    background: transparent !important; 
    border: none !important; 
    padding: 12px 0 !important; 
}
[data-testid="stChatMessage"] > div { 
    background: transparent !important; 
}

/* Caixa de Resposta da Inteligência / Técnico */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1F232E !important; 
    border-radius: 4px 12px 12px 12px !important;
    padding: 16px 20px !important; 
    border: 1px solid #2D3446 !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

/* Caixa de Envio do Usuário */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #165339, #1E724E) !important;
    border-radius: 12px 4px 12px 12px !important; 
    padding: 14px 18px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #E2E8F0 !important; 
    font-size: 1rem !important; 
    line-height: 1.6 !important; 
    margin: 0 !important;
}
[data-testid="stChatMessage"] strong { color: #FFFFFF !important; font-weight: 600; }
[data-testid="stChatMessage"] code { background: #161920 !important; color: #FFCC00 !important; padding: 2px 6px !important; border-radius: 4px !important; }

/* ═══════════════════════════════
   CAIXA DE DIGITAÇÃO PRINCIPAL
═══════════════════════════════ */
[data-testid="stBottom"] { 
    background: #161920 !important; 
    border-top: 1px solid #2D3446 !important; 
    padding: 15px 0 !important;
}
[data-testid="stChatInput"] { 
    background: #1F232E !important; 
    border: 1.5px solid #2D3446 !important; 
    border-radius: 10px !important; 
    padding: 4px !important;
}
[data-testid="stChatInput"]:focus-within { 
    border-color: #007ACC !important; 
    box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.2) !important; 
}
[data-testid="stChatInput"] > div { background: #1F232E !important; }
[data-testid="stChatInput"] textarea { 
    color: #FFFFFF !important; 
    background: #1F232E !important; 
    font-size: 1rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #7E8B9B !important; }
</style>
"""

# ── Backend helpers ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def chunk_text(text, size=800, overlap=150):
    text = text.strip()
    if not text: return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk: chunks.append(chunk)
        if end >= len(text): break
        start = end - overlap
    return chunks

def extract_pdf(fb):
    try:
        import pypdf
        r = pypdf.PdfReader(io.BytesIO(fb))
        return "\n\n".join(p.extract_text() or "" for p in r.pages).strip()
    except Exception as e: return f"Erro: {e}"

def get_youtube_transcript(url):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        vid = url.split("youtu.be/")[1].split("?")[0] if "youtu.be/" in url else url.split("v=")[1].split("&")[0]
        t = YouTubeTranscriptApi.get_transcript(vid, languages=["pt","pt-BR","en"])
        return " ".join(x["text"] for x in t), None
    except Exception as e: return None, str(e)

def search_knowledge(q, sb):
    try: return sb.rpc("buscar_conhecimento", {"consulta": q, "max_resultados": 4}).execute().data or []
    except: return []

def upload_doc(title, content, stype, sref, sb):
    chunks = chunk_text(content)
    for i, c in enumerate(chunks):
        sb.table("knowledge_base").insert({"title":title,"content":c,"source_type":stype,"source_ref":sref,"chunk_index":i}).execute()
    return len(chunks)

def get_all_docs(sb):
    try: return sb.table("knowledge_base").select("id,title,source_type,chunk_index,created_at").order("created_at",desc=True).execute().data or []
    except: return []

def delete_doc(title, sb):
    try: sb.table("knowledge_base").delete().eq("title",title).execute(); return True
    except: return False

def count_docs(sb):
    try: return sb.table("knowledge_base").select("id",count="exact").execute().count or 0
    except: return 0

def stream_groq(msgs, key, model):
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    b = {"model": model, "messages": msgs, "stream": True, "temperature": 0.7, "max_tokens": 4096}
    with requests.post(GROQ_URL, headers=h, json=b, stream=True, timeout=120) as r:
        r.raise_for_status()
        for line in r
