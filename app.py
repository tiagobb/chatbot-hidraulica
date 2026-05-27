import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os
import re
import hashlib

# ── Configurações ─────────────────────────────────────────────────────────────
SUPABASE_URL   = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

# Foto do avatar do técnico (troque o número 0-99 para escolher outro rosto)
TECH_AVATAR = "https://randomuser.me/api/portraits/men/75.jpg"
USER_AVATAR = "👤"

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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Fonte Inter SOMENTE em elementos de texto — NUNCA em ícones (Material Symbols) */
* { box-sizing: border-box; }
html, body, .stApp, button, input, textarea, select,
p, h1, h2, h3, h4, h5, h6, li, a, label,
.stMarkdown, [data-testid="stMarkdownContainer"] {
    font-family: 'Inter', sans-serif !important;
}
/* Restaura a fonte dos ícones para não virarem texto cru */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons,
span[class*="material"] {
    font-family: 'Material Symbols Rounded','Material Icons' !important;
}

#MainMenu, footer, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
.stApp, .main { background: #12151C !important; }
.block-container { padding: 1.5rem 2rem 7rem 2rem !important; max-width: 1180px !important; }

/* ═══════════════════════════════
   BARRA LATERAL — SEMPRE ABERTA (travada, não fecha)
═══════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2B303C 0%, #20242F 100%) !important;
    border-right: 1px solid #2D3448 !important;
    width: 320px !important;
    min-width: 320px !important;
    max-width: 320px !important;
    transform: none !important;
    visibility: visible !important;
    margin-left: 0 !important;
}
/* Mesmo quando o Streamlit tenta colapsar, forçamos aberta */
section[data-testid="stSidebar"][aria-expanded="false"] {
    transform: none !important;
    margin-left: 0 !important;
    width: 320px !important;
    min-width: 320px !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 1.4rem 1.1rem !important; }
/* Esconde o botão X de fechar — a barra fica sempre visível, igual à imagem */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

.sec-title {
    font-size: .72rem; font-weight: 700; letter-spacing: 2px;
    color: #8A96AD; text-transform: uppercase;
    margin: 20px 0 12px 0;
}
.upload-label { font-size: .98rem; font-weight: 700; color: #E6ECF7; margin-bottom: 6px; }
.upload-label span { font-weight: 400; color: #8A96AD; font-size: .82rem; }

/* File uploader */
[data-testid="stFileUploader"] { background: transparent !important; }
[data-testid="stFileUploaderDropzone"], [data-testid="stFileDropzone"] {
    background: #1A1E28 !important; border: 1.5px dashed #3A435C !important;
    border-radius: 10px !important; padding: 14px !important; min-height: auto !important;
}
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileDropzone"] * { color: #9AA6BD !important; }
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileDropzone"] button {
    background: #2E3547 !important; color: #DCE3F0 !important;
    border: 1px solid #434C66 !important; border-radius: 8px !important;
    font-size: .9rem !important; font-weight: 600 !important; padding: 8px 18px !important;
}

/* Lista de expertise */
.exp-item {
    display: flex; align-items: center; gap: 12px;
    padding: 11px 13px; border-radius: 9px; margin-bottom: 6px;
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06);
    font-size: .96rem; color: #D4DBEA;
}
.exp-item .ei { font-size: 1.18rem; min-width: 22px; text-align: center; }

/* Status */
.status-pill {
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06);
    border-radius: 10px; padding: 13px 15px; margin-top: 16px;
}
.status-pill .s-label { font-size: .68rem; color: #8A96AD; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
.status-pill .s-val   { font-size: .92rem; color: #2ECC71; font-weight: 600; }

/* ═══════════════════════════════
   HEADER PRINCIPAL
═══════════════════════════════ */
.app-header {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 60%, #1A2035 100%);
    border-radius: 18px; padding: 28px 32px; margin-bottom: 20px;
    border: 1px solid #2A3555; box-shadow: 0 8px 30px rgba(0,0,0,.35);
}
.hdr-top { display: flex; align-items: center; gap: 22px; }
.icon-box {
    background: radial-gradient(circle at 35% 28%, #5A6884, #252B3B 72%);
    border-radius: 50%;
    width: 82px; height: 82px; display: flex; align-items: center;
    justify-content: center; font-size: 2.6rem; flex-shrink: 0;
    border: 1px solid #4A5268;
    box-shadow: inset 0 2px 8px rgba(255,255,255,.12), 0 5px 16px rgba(0,0,0,.35);
}
.app-header h1 { color: #FFFFFF !important; font-size: 1.95rem; font-weight: 800; margin: 0 0 6px 0 !important; line-height: 1.15; }
.app-header .sub { color: #8A9BC0; font-size: 1.02rem; margin: 0; }
.app-header .welcome {
    color: #C8D2E6; font-size: 1.1rem; line-height: 1.6;
    margin: 20px 0 0 0; padding-top: 20px; border-top: 1px solid #2A3555;
}

/* ═══════════════════════════════
   BOTÕES
═══════════════════════════════ */
.stButton > button {
    background: #1C2030 !important; color: #D4DBEA !important;
    border: 1px solid #2D3448 !important; border-radius: 12px !important;
    font-size: 1rem !important; font-weight: 500 !important;
    padding: 16px 14px !important; transition: all .2s !important;
}
.stButton > button:hover {
    background: #252B3B !important; border-color: #4A7AC8 !important;
    color: #FFFFFF !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(74,122,200,.18) !important;
}

/* ═══════════════════════════════
   CHAT
═══════════════════════════════ */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 5px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; }
/* Avatar redondo (foto) */
[data-testid="stChatMessage"] img { border-radius: 50% !important; object-fit: cover !important; }
/* Estilo PADRÃO = bolha do assistente (vale para qualquer tipo de avatar) */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    background: #1C2030 !important; border-radius: 4px 16px 16px 16px !important;
    padding: 14px 18px !important; border: 1px solid #252B3B !important;
}
/* Sobrescreve para a bolha do USUÁRIO (avatar emoji 👤) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #235E72, #2C8094) !important;
    border-radius: 16px 4px 16px 16px !important; padding: 13px 17px !important;
    border: none !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #D8E0F0 !important; font-size: .98rem !important; line-height: 1.65 !important; margin: 0 !important;
}
[data-testid="stChatMessage"] strong { color: #FFFFFF !important; }
[data-testid="stChatMessage"] code { background: #12151C !important; color: #FFC857 !important; padding: 2px 5px !important; border-radius: 4px !important; }

/* ═══════════════════════════════
   INPUT
═══════════════════════════════ */
[data-testid="stBottom"] { background: #12151C !important; border-top: 1px solid #1E2435 !important; }
/* Campo claro com TEXTO ESCURO (legível), borda verde arredondada — igual à imagem */
[data-testid="stChatInput"] { background: #F4F6FA !important; border: 2px solid #3DA177 !important; border-radius: 28px !important; }
[data-testid="stChatInput"]:focus-within { border-color: #2ECC71 !important; box-shadow: 0 0 0 3px rgba(46,204,113,.14) !important; }
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] { background: #F4F6FA !important; }
[data-testid="stChatInput"] textarea {
    color: #1A1E28 !important; -webkit-text-fill-color: #1A1E28 !important;
    background: #F4F6FA !important; caret-color: #1A6B4A !important; font-size: 1rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #6A7589 !important; -webkit-text-fill-color: #6A7589 !important; }
/* Botão de enviar VERDE (igual à imagem) */
[data-testid="stChatInputSubmitButton"] {
    background: linear-gradient(135deg, #1A6B4A, #1E8A5E) !important;
    border-radius: 50% !important; color: #FFFFFF !important;
}
[data-testid="stChatInputSubmitButton"]:hover { background: #23A06E !important; }
[data-testid="stChatInput"] button svg { color: #FFFFFF !important; fill: #FFFFFF !important; }
/* Ícones de anexar/áudio também esverdeados */
[data-testid="stChatInput"] [data-testid="stChatInputFileUploadButton"] svg,
[data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] svg { color: #FFFFFF !important; }
[data-testid="stChatInput"] [data-testid="stChatInputFileUploadButton"] svg { color: #2ECC71 !important; fill: #2ECC71 !important; }

/* ═══════════════════════════════
   FORM / ADMIN
═══════════════════════════════ */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #12151C !important; color: #D8E0F0 !important;
    border: 1px solid #2D3448 !important; border-radius: 8px !important;
}
[data-testid="stExpander"] { background: #12151C !important; border: 1px solid #252B3B !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary p { color: #C8D0E0 !important; }
.stAlert { background: #12151C !important; border-radius: 8px !important; }
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf     { background:#7f1d1d33; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d33; color:#f87171; border:1px solid #991b1b; }
.src-text    { background:#14532d33; color:#86efac; border:1px solid #14532d; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #12151C; }
::-webkit-scrollbar-thumb { background: #2D3448; border-radius: 2px; }
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

def find_youtube_url(text):
    if not text: return None
    m = re.search(r'https?://[^\s]*(?:youtube\.com/watch\?[^\s]*v=|youtu\.be/)[^\s]+', text)
    return m.group(0) if m else None

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

def transcribe_audio(audio_bytes, key):
    try:
        h = {"Authorization": f"Bearer {key}"}
        files = {"file": ("fala.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3-turbo", "language": "pt"}
        r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                          headers=h, files=files, data=data, timeout=60)
        r.raise_for_status()
        return r.json().get("text", "").strip(), None
    except Exception as e:
        return None, str(e)

def do_chat(prompt, image_bytes, mime_type, sb, kb_count):
    rag = ""
    if sb and kb_count > 0:
        results = search_knowledge(prompt, sb)
        if results:
            rag = "\n\n---\n**CONHECIMENTO DA BASE:**\n" + "".join(f"\n📚 [{r['title']}]:\n{r['content']}\n" for r in results) + "---\n"
    # YouTube: se houver link na pergunta, lê a transcrição e usa como contexto
    yt_context, yt_note = "", ""
    yt_url = find_youtube_url(prompt)
    if yt_url:
        transcript, err = get_youtube_transcript(yt_url)
        if transcript:
            yt_context = ("\n\n---\n**TRANSCRIÇÃO DO VÍDEO DO YOUTUBE (conteúdo falado — "
                          "analise tecnicamente e responda com base nisto):**\n" + transcript[:15000] + "\n---\n")
            yt_note = "🎥 Li a transcrição do vídeo do YouTube e estou analisando..."
        else:
            yt_note = f"⚠️ Não consegui ler a transcrição do vídeo (pode não ter legendas disponíveis). Detalhe: {err}"
    api = [{"role":"system","content": SYSTEM_PROMPT + rag}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user","assistant"): api.append({"role":m["role"],"content":m["content"]})
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        api.append({"role":"user","content":[
            {"type":"text","text":prompt+rag+yt_context},
            {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
        ]})
        model = VISION_MODEL
    else:
        api.append({"role":"user","content":prompt+yt_context})
        model = TEXT_MODEL
    with st.chat_message("assistant", avatar=TECH_AVATAR):
        if rag: st.caption("📚 Consultando base de conhecimento...")
        if yt_note: st.caption(yt_note)
        ph = st.empty(); full = ""
        try:
            for chunk in stream_groq(api, GROQ_API_KEY, model):
                full += chunk; ph.markdown(full+"▌")
            ph.markdown(full)
        except requests.HTTPError as e:
            ph.error(f"Erro {e.response.status_code}: {e.response.text[:200]}"); full = ""
    return full

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada."); st.stop()

sb       = get_supabase() if SUPABASE_URL and SUPABASE_KEY else None
kb_count = count_docs(sb) if sb else 0

if "messages"     not in st.session_state: st.session_state.messages     = []
if "quick_prompt" not in st.session_state: st.session_state.quick_prompt = ""

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT — barra lateral nativa (abre / fecha com o botão X e o ☰)
# ══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────
# BARRA LATERAL
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec-title">RECURSOS ADICIONAIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-label">ANEXAR FOTO <span>(opcional)</span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg","jpeg","png","webp"],
                                     label_visibility="collapsed", key="foto_up")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Será enviada com a próxima mensagem")

    st.markdown('<div class="upload-label" style="margin-top:14px;">PERGUNTAR POR VOZ <span>(grave e solte)</span></div>', unsafe_allow_html=True)
    audio = st.audio_input("voz", label_visibility="collapsed", key="voice_in")
    if audio is not None:
        ab = audio.getvalue()
        sig = hashlib.md5(ab).hexdigest()
        if st.session_state.get("last_voice_sig") != sig:
            st.session_state.last_voice_sig = sig
            with st.spinner("🎤 Transcrevendo sua fala..."):
                vtext, verr = transcribe_audio(ab, GROQ_API_KEY)
            if vtext:
                st.session_state.quick_prompt = vtext
                st.rerun()
            else:
                st.error(f"Não entendi o áudio: {verr}")

    st.markdown('<div class="sec-title" style="margin-top:18px;">ÁREAS DE EXPERTISE</div>', unsafe_allow_html=True)
    for icon, label in [
        ("🔧","Hidráulica Industrial"),
        ("⚡","Elétrica Industrial"),
        ("🔌","Eletrônica / VFD"),
        ("⚙️","Eletromecânica / CNC"),
        ("🔩","Mecânica Industrial"),
        ("🤖","Automação / CLP"),
        ("🌐","Redes Industriais"),
    ]:
        st.markdown(f'<div class="exp-item"><span class="ei">{icon}</span>{label}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)

    # Admin
    if not st.session_state.get("admin_logged"):
        with st.expander("🔐 Admin", expanded=False):
            pwd = st.text_input("Senha", type="password", label_visibility="collapsed",
                                placeholder="Senha admin", key="pwd")
            if st.button("Entrar", use_container_width=True, key="btn_login"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True; st.rerun()
                else: st.error("Senha incorreta")
    else:
        st.success("✅ Admin conectado")
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            st.session_state.admin_logged = False; st.rerun()

    if st.button("🗑️ Nova Conversa", use_container_width=True, key="btn_nova"):
        st.session_state.messages = []
        st.session_state.quick_prompt = ""; st.rerun()

    st.markdown(f"""
    <div class="status-pill">
        <div class="s-label">Sistema Operacional</div>
        <div class="s-val">● Online · {kb_count} fragmentos</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# ÁREA PRINCIPAL
# ─────────────────────────────────────────────────
with st.container():
    st.markdown(f"""
    <div class="app-header">
      <div class="hdr-top">
        <div class="icon-box">⚙️</div>
        <div>
          <h1>🛠️ Técnico Especialista em Manutenção Industrial</h1>
          <p class="sub">👨‍🔧 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
        </div>
      </div>
      <p class="welcome">{WELCOME_MSG}</p>
    </div>
    """, unsafe_allow_html=True)

    # Botões de ação rápida
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔧 Diagnosticar Falha", use_container_width=True, key="q1"):
            st.session_state.quick_prompt = "Preciso diagnosticar uma falha no equipamento. Me faça as perguntas necessárias para identificar o problema."; st.rerun()
    with b2:
        if st.button("🔍 Identificar Componente", use_container_width=True, key="q2"):
            st.session_state.quick_prompt = "Preciso identificar um componente hidráulico ou elétrico. Como posso descrevê-lo para você identificar?"; st.rerun()
    with b3:
        if st.button("📋 Consultar Esquema", use_container_width=True, key="q3"):
            st.session_state.quick_prompt = "Preciso de ajuda para interpretar ou montar um esquema hidráulico ou elétrico."; st.rerun()

    # Admin panel
    if st.session_state.get("admin_logged") and sb:
        with st.expander("📚 BASE DE CONHECIMENTO", expanded=False):
            tab1, tab2, tab3, tab4 = st.tabs(["📄 PDF","✍️ Texto","🎥 YouTube","🗂️ Gerenciar"])
            with tab1:
                pt = st.text_input("Título", placeholder="Ex: Manual Bomba Rexroth A10V", key="pdf_t")
                pf = st.file_uploader("PDF", type=["pdf"], key="pdf_f")
                if st.button("📤 Salvar PDF", key="btn_pdf"):
                    if not pt: st.warning("Digite um título.")
                    elif not pf: st.warning("Selecione um PDF.")
                    else:
                        with st.spinner("Processando..."):
                            text = extract_pdf(pf.read())
                            if text.startswith("Erro"): st.error(text)
                            else: st.success(f"✅ {upload_doc(pt,text,'pdf',pf.name,sb)} fragmentos!"); st.rerun()
            with tab2:
                tt = st.text_input("Título", placeholder="Ex: Procedimento Troca de Óleo", key="txt_t")
                tc = st.text_area("Conteúdo", placeholder="Cole o texto técnico aqui...", height=140, key="txt_c")
                if st.button("💾 Salvar Texto", key="btn_txt"):
                    if not tt: st.warning("Título obrigatório.")
                    elif not tc: st.warning("Conteúdo obrigatório.")
                    else:
                        with st.spinner("Salvando..."): st.success(f"✅ {upload_doc(tt,tc,'text','manual',sb)} fragmentos!"); st.rerun()
            with tab3:
                yt = st.text_input("Título", placeholder="Ex: Aula Hidráulica Industrial", key="yt_t")
                yu = st.text_input("URL YouTube", placeholder="https://youtube.com/watch?v=...", key="yt_u")
                if st.button("📥 Extrair e Salvar", key="btn_yt"):
                    if not yt: st.warning("Título obrigatório.")
                    elif not yu: st.warning("URL obrigatória.")
                    else:
                        with st.spinner("Extraindo..."):
                            text, err = get_youtube_transcript(yu)
                            if err: st.error(f"Erro: {err}")
                            else: st.success(f"✅ {upload_doc(yt,text,'youtube',yu,sb)} fragmentos!"); st.rerun()
            with tab4:
                docs = get_all_docs(sb)
                if not docs: st.info("Base vazia.")
                else:
                    for title in list({d["title"] for d in docs}):
                        chunks = [d for d in docs if d["title"]==title]
                        src = chunks[0]["source_type"]
                        color = {"pdf":"src-pdf","youtube":"src-youtube","text":"src-text"}.get(src,"src-text")
                        c1,c2 = st.columns([5,1])
                        with c1: st.markdown(f'<span class="source-tag {color}">{src.upper()}</span> **{title}** <small style="color:#5A6478">({len(chunks)} frag.)</small>', unsafe_allow_html=True)
                        with c2:
                            if st.button("🗑️", key=f"del_{title}"): delete_doc(title,sb); st.rerun()
                        st.divider()

    # Mensagens do chat
    for msg in st.session_state.messages:
        avatar = TECH_AVATAR if msg["role"] == "assistant" else USER_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image_bytes"):
                st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=300)

    # Ação rápida
    if st.session_state.quick_prompt:
        qp = st.session_state.quick_prompt
        st.session_state.quick_prompt = ""
        with st.chat_message("user", avatar=USER_AVATAR): st.markdown(qp)
        st.session_state.messages.append({"role":"user","content":qp})
        full = do_chat(qp, None, None, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content":full})

# ── Chat input (com anexo de imagem no próprio campo, igual à imagem) ──────────
chat = st.chat_input("Digite sua pergunta, anexe uma foto ou cole um link do YouTube...",
                     accept_file=True, file_type=["jpg", "jpeg", "png", "webp"])
if chat:
    prompt = (chat.text or "").strip()
    files  = chat.files or []
    uf = files[0] if files else st.session_state.get("foto_up")
    img_b, mime, sfx = None, None, ""
    if uf:
        img_b = uf.read(); mime = uf.type; sfx = f"\n\n📷 *[{uf.name}]*"
    if not prompt and img_b:
        prompt = "Analise esta imagem do equipamento/componente e me diga o que você identifica."

    if prompt or img_b:
        display = prompt + sfx
        umsg = {"role": "user", "content": display}
        if img_b: umsg["image_bytes"] = img_b
        st.session_state.messages.append(umsg)

        with st.container():
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(display)
                if img_b: st.image(PIL.Image.open(io.BytesIO(img_b)), width=300)
            full = do_chat(prompt, img_b, mime, sb, kb_count)
            if full: st.session_state.messages.append({"role": "assistant", "content": full})
