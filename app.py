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
- Hidráulica Industrial (circuitos, components, óleos, simbologia ISO 1219, servo-hidráulica)
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

# ── CSS Ajustado (Fontes Grandes e Espaçamento Correto) ────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { 
    font-family: 'Inter', sans-serif !important; 
}

/* Ocultar elementos nativos do Streamlit */
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Configuração do fundo e container principal */
.stApp, .main { 
    background-color: #12151C !important; 
}
.block-container { 
    padding: 20px 30px 80px 30px !important; 
    max-width: 98% !important; 
}

/* ═══════════════════════════════
   PAINEL ESQUERDO (COLUNA)
═══════════════════════════════ */
.left-col {
    background: #1C2030;
    border-radius: 12px;
    border: 1px solid #252B3B;
    padding: 24px 20px;
    min-height: 80vh;
}
.sec-title {
    font-size: 13px !important; 
    font-weight: 700 !important; 
    letter-spacing: 1.5px;
    color: #64748B; 
    text-transform: uppercase;
    border-bottom: 1px solid #252B3B; 
    padding-bottom: 8px; 
    margin-bottom: 16px;
    margin-top: 15px;
}
.upload-label {
    font-size: 14px !important; 
    font-weight: 600 !important; 
    color: #E2E8F0; 
    margin-bottom: 8px;
}
.upload-label span { 
    font-weight: 400; 
    color: #64748B; 
}

/* Caixa Dropzone */
[data-testid="stFileUploader"] { background: transparent !important; border: none !important; }
[data-testid="stFileDropzone"] {
    background: #12151C !important; 
    border: 1.5px dashed #334155 !important;
    border-radius: 8px !important; 
    padding: 20px !important;
}
[data-testid="stFileDropzone"] * { color: #94A3B8 !important; font-size: 13px !important; }
[data-testid="stFileDropzone"] button {
    background: #252B3B !important; 
    color: #FFFFFF !important;
    border: 1px solid #334155 !important; 
    border-radius: 6px !important;
    font-size: 13px !important; 
    padding: 8px 16px !important;
    width: 100%;
}

/* Lista de Especialidades */
.exp-item {
    display: flex; 
    align-items: center; 
    gap: 12px;
    padding: 12px 16px; 
    border-radius: 8px; 
    margin-bottom: 8px;
    background: #12151C; 
    border: 1px solid #252B3B;
    font-size: 14px !important; 
    color: #E2E8F0;
    font-weight: 500;
}
.exp-item .ei { 
    font-size: 18px !important; 
    min-width: 24px; 
}

/* Status do Sistema */
.status-pill {
    background: #12151C; 
    border: 1px solid #252B3B;
    border-radius: 8px; 
    padding: 14px; 
    margin-top: 24px;
}
.status-pill .s-label { 
    font-size: 11px !important; 
    color: #64748B; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
    margin-bottom: 4px; 
}
.status-pill .s-val { 
    font-size: 14px !important; 
    color: #2ECC71; 
    font-weight: 600; 
}

/* ═══════════════════════════════
   HEADER PRINCIPAL DO CHAT
═══════════════════════════════ */
.app-header {
    background: linear-gradient(135deg, #1C2030 0%, #12151C 100%);
    border-radius: 12px; 
    padding: 24px 28px; 
    margin-bottom: 24px;
    border: 1px solid #252B3B; 
    border-left: 6px solid #007ACC; 
    box-shadow: 0 4px 15px rgba(0,0,0,.3);
    display: flex; 
    align-items: center; 
    gap: 20px;
}
.icon-box {
    background: #252B3B; 
    border-radius: 10px;
    width: 60px; 
    height: 60px; 
    display: flex; 
    align-items: center;
    justify-content: center; 
    font-size: 28px !important; 
    flex-shrink: 0;
    border: 1px solid #334155;
}
.app-header h1 { 
    color: #FFFFFF !important; 
    font-size: 24px !important; 
    font-weight: 700 !important; 
    margin: 0 0 4px 0 !important; 
}
.app-header .sub { 
    color: #94A3B8 !important; 
    font-size: 14px !important; 
    margin: 0 !important; 
}

/* ═══════════════════════════════
   BOTÕES DE AÇÃO RÁPIDA
═══════════════════════════════ */
.stButton > button {
    background: #1C2030 !important; 
    color: #F1F5F9 !important;
    border: 1px solid #252B3B !important; 
    border-radius: 8px !important;
    font-size: 14px !important; 
    font-weight: 600 !important;
    padding: 14px 18px !important; 
    transition: all .2s ease !important;
}
.stButton > button:hover {
    background: #252B3B !important; 
    border-color: #007ACC !important;
    color: #FFFFFF !important; 
}

/* ═══════════════════════════════
   MENSAGENS DO CHAT
═══════════════════════════════ */
[data-testid="stChatMessage"] { 
    background: transparent !important; 
    border: none !important; 
    padding: 14px 0 !important; 
}
[data-testid="stChatMessage"] > div { 
    background: transparent !important; 
}

/* Balão do Assistente */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1C2030 !important; 
    border-radius: 4px 12px 12px 12px !important;
    padding: 16px 20px !important; 
    border: 1px solid #252B3B !important;
}

/* Balão do Usuário */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #165339, #1E724E) !important;
    border-radius: 12px 4px 12px 12px !important; 
    padding: 16px 20px !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #E2E8F0 !important; 
    font-size: 15px !important; 
    line-height: 1.6 !important; 
}

/* Campo de Texto Inferior */
[data-testid="stBottom"] { 
    background: #12151C !important; 
    border-top: 1px solid #252B3B !important; 
    padding: 20px 0 !important;
}
[data-testid="stChatInput"] { 
    background: #1C2030 !important; 
    border: 1.5px solid #252B3B !important; 
    border-radius: 10px !important; 
}
[data-testid="stChatInput"] textarea { 
    color: #FFFFFF !important; 
    background: #1C2030 !important; 
    font-size: 15px !important;
}
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
    api = [{"role":"system","content": SYSTEM_PROMPT + rag}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user","assistant
