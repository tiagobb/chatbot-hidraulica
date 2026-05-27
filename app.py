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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

:root{
    --bg:#07121b;
    --panel:#101b24;
    --panel-2:#172430;
    --line:#344657;
    --text:#eef6ff;
    --muted:#b7c4cf;
    --accent:#54b98c;
    --blue:#c8ebff;
}

.stApp, .main {
    background:
      radial-gradient(circle at 97% 94%, rgba(220,238,255,.32) 0 18px, transparent 20px),
      linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px),
      radial-gradient(circle at 70% 10%, rgba(50,117,151,.22), transparent 28%),
      #07121b !important;
    background-size: auto, 52px 52px, 52px 52px, auto, auto !important;
}
.block-container { padding: .75rem 1rem 5.2rem .85rem !important; max-width: 1220px !important; }

/* barra lateral visual parecida com o Gemini */
.left-col {
    background: linear-gradient(180deg, rgba(125,135,142,.42), rgba(72,80,88,.28));
    border-right: 1px solid rgba(255,255,255,.18);
    padding: 14px 10px 18px 10px;
    min-height: calc(100vh - 1.5rem);
    box-shadow: inset -10px 0 28px rgba(0,0,0,.25);
    position: relative;
}
.left-col:before{
    content:'×';
    position:absolute; top:9px; right:14px;
    color:#d7dde4; font-size:22px; font-weight:300;
}
.sec-title {
    font-size: .78rem; font-weight: 800; letter-spacing: .2px;
    color: #f0f3f6; text-transform: uppercase;
    margin: 42px 4px 8px 4px;
    text-shadow: 0 1px 2px rgba(0,0,0,.55);
}
.upload-label {
    display:none;
}
[data-testid="stFileUploader"] {
    background: #eaf1f8 !important;
    border: 1px solid #b6c5d4 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.22) !important;
}
[data-testid="stFileUploader"]:before{
    content:'ANEXAR FOTO (opcional)';
    display:block; color:#1b2430; font-size:.78rem; font-weight:800; margin-bottom:6px;
}
[data-testid="stFileDropzone"] {
    background: #dfe9f3 !important; border: 1px solid #b5c3d1 !important;
    border-radius: 8px !important; padding: 7px !important;
}
[data-testid="stFileDropzone"] * { color: #16202b !important; }
[data-testid="stFileDropzone"] button {
    width:100% !important;
    background: #eef5fc !important; color: #111923 !important;
    border: 1px solid #b7c6d5 !important; border-radius: 7px !important;
    font-size: .86rem !important; padding: 6px 10px !important;
    box-shadow: inset 0 -2px 4px rgba(0,0,0,.06) !important;
}
[data-testid="stFileUploader"] small { color:#475563 !important; }

.exp-item {
    display: flex; align-items: center; gap: 7px;
    padding: 7px 7px; border-radius: 7px; margin: 5px 0;
    background: rgba(0,0,0,.32); border: 1px solid rgba(255,255,255,.06);
    font-size: .86rem; color: #ffffff; font-weight: 700;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
}
.exp-item .ei { font-size: .92rem; min-width: 18px; }
.status-pill {
    background: rgba(5,17,28,.78); border: 1px solid rgba(255,255,255,.18);
    border-radius: 8px; padding: 11px 12px; margin-top: 18px;
    color:#fff; box-shadow: 0 5px 15px rgba(0,0,0,.22);
}
.status-pill .s-label { font-size: .78rem; color: #ffffff; font-weight:700; margin-bottom: 5px; }
.status-pill .s-val   { font-size: .84rem; color: #54d287; font-weight: 700; }

/* área principal */
.main-shell{ max-width: 840px; margin: 34px auto 0 auto; position:relative; }
.hamburger{ position:fixed; right:20px; top:76px; color:#e6edf5; font-size:20px; z-index:5; }
.app-card {
    background: rgba(20,31,40,.90);
    border: 1px solid rgba(190,214,232,.45);
    border-radius: 8px;
    box-shadow: 0 12px 35px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.08);
    overflow: hidden;
}
.app-header {
    padding: 18px 22px 14px 22px;
    border-bottom: 1px solid rgba(255,255,255,.16);
    display: flex; align-items: center; gap: 16px;
    background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,0));
}
.icon-box {
    width: 58px; height: 58px; display: flex; align-items:center; justify-content:center;
    font-size: 3rem; flex-shrink: 0; filter: drop-shadow(0 4px 4px rgba(0,0,0,.45));
}
.app-header h1 { color:#fff; font-size: 1.62rem; line-height:1.08; font-weight: 900; margin:0 0 5px 0; text-shadow:0 2px 2px rgba(0,0,0,.6); }
.app-header .sub { color:#cfdae3; font-size:.86rem; margin:0; }
.intro-text { padding: 15px 22px 10px 22px; color:#ffffff; font-weight:700; font-size:.94rem; line-height:1.55; }
.quick-row { padding: 0 22px 16px 22px; }
.quick-row .stButton > button, .stButton > button {
    background: rgba(15,27,38,.92) !important; color:#fff !important;
    border: 1px solid #6a8194 !important; border-radius: 8px !important;
    font-size: .88rem !important; font-weight: 800 !important;
    padding: 13px 10px !important; transition: all .18s ease !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 3px 10px rgba(0,0,0,.2) !important;
}
.stButton > button:hover { border-color:#bfefff !important; transform:translateY(-1px); background:#172b3b !important; }

/* chat */
.chat-area { max-width: 840px; margin: 16px auto 0 auto; border-bottom:1px solid rgba(255,255,255,.15); padding-bottom:10px; }
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 5px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; }
[data-testid="chatAvatarIcon-assistant"], [data-testid="chatAvatarIcon-user"] { background: transparent !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    box-shadow: 0 4px 16px rgba(0,0,0,.18);
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #303b46, #25313b) !important;
    border-radius: 4px 15px 15px 15px !important;
    padding: 12px 16px !important; border: 1px solid rgba(255,255,255,.06) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: #bfe7ff !important; color:#0c1a24 !important;
    border-radius: 14px 4px 14px 14px !important; padding: 12px 15px !important;
    border: 1px solid #d9f1ff !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size:.9rem !important; line-height:1.55 !important; margin:0 !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p { color:#fff !important; font-weight:700 !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color:#07131c !important; font-weight:500 !important; }
[data-testid="stChatMessage"] strong { color:#fff !important; }
[data-testid="stChatMessage"] code { background:#07121b !important; color:#ffd166 !important; padding:2px 5px !important; border-radius:4px !important; }

/* input inferior */
[data-testid="stBottom"] { background: transparent !important; border-top: none !important; }
[data-testid="stChatInput"] {
    max-width: 840px !important; margin: 0 auto 12px auto !important;
    background: #ffffff !important; border: 2px solid #45bf7d !important; border-radius: 24px !important;
    box-shadow: 0 8px 28px rgba(0,0,0,.28) !important;
}
[data-testid="stChatInput"] > div { background:#ffffff !important; border-radius:24px !important; }
[data-testid="stChatInput"] textarea { color:#101820 !important; background:#ffffff !important; caret-color:#1a8d55 !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#6b7280 !important; }
[data-testid="stChatInput"] button { background:#41b87a !important; color:#fff !important; border-radius:999px !important; }

.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #101b24 !important; color: #eef6ff !important; border: 1px solid #344657 !important; border-radius: 8px !important;
}
[data-testid="stExpander"] { background: rgba(16,27,36,.8) !important; border: 1px solid rgba(255,255,255,.14) !important; border-radius: 10px !important; }
[data-testid="stExpander"] * { color: #eef6ff !important; }
.stAlert { background: rgba(16,27,36,.85) !important; border-radius: 8px !important; }
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf { background:#7f1d1d33; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d33; color:#f87171; border:1px solid #991b1b; }
.src-text { background:#14532d33; color:#86efac; border:1px solid #14532d; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #07121b; }
::-webkit-scrollbar-thumb { background: #7e93a8; border-radius: 999px; }
@media (max-width: 760px){
    .block-container{padding:.4rem .5rem 5rem .5rem !important;}
    .left-col{min-height:auto; margin-bottom:12px;}
    .main-shell{margin-top:0;}
    .app-header h1{font-size:1.2rem;}
    .icon-box{width:44px;height:44px;font-size:2.2rem;}
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
        if m["role"] in ("user","assistant"): api.append({"role":m["role"],"content":m["content"]})
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        api.append({"role":"user","content":[
            {"type":"text","text":prompt+rag},
            {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
        ]})
        model = VISION_MODEL
    else:
        api.append({"role":"user","content":prompt})
        model = TEXT_MODEL
    with st.chat_message("assistant", avatar="🔧"):
        if rag: st.caption("📚 Consultando base de conhecimento...")
        ph = st.empty(); full = ""
        try:
            for chunk in stream_groq(api, GROQ_API_KEY, model):
                full += chunk; ph.markdown(full+"▌")
            ph.markdown(full)
        except requests.HTTPError as e:
            ph.error(f"Erro {e.response.status_code}: {e.response.text[:200]}"); full = ""
    return full

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada."); st.stop()

sb       = get_supabase() if SUPABASE_URL and SUPABASE_KEY else None
kb_count = count_docs(sb) if sb else 0

if "messages"     not in st.session_state: st.session_state.messages     = [{"role":"assistant","content":WELCOME_MSG}]
if "quick_prompt" not in st.session_state: st.session_state.quick_prompt = ""

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
col_L, col_R = st.columns([1, 3.2], gap="medium")

# ─────────────────────────────────────────────────
# PAINEL ESQUERDO
# ─────────────────────────────────────────────────
with col_L:
    st.markdown('<div class="left-col">', unsafe_allow_html=True)

    # Foto
    st.markdown('<div class="sec-title">RECURSOS ADICIONAIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-label">ANEXAR FOTO <span>(opcional)</span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg","jpeg","png","webp"],
                                     label_visibility="collapsed", key="foto_up")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Será enviada com a próxima mensagem")

    st.markdown("<br>", unsafe_allow_html=True)

    # Expertise — lista estática
    st.markdown('<div class="sec-title">ÁREAS DE EXPERTISE</div>', unsafe_allow_html=True)
    for icon, label in [
        ("🔧","Hidráulica Industrial"),
        ("⚡","Elétrica Industrial"),
        ("⚡","Eletrônica / VFD"),
        ("🔧","Eletrônica / VFD"),
        ("⚙️","Eletromecânica / CNC"),
        ("🔩","Mecânica Industrial"),
    ]:
        st.markdown(f'<div class="exp-item"><span class="ei">{icon}</span>{label}</div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin (oculto por padrão)
    if not st.session_state.get("admin_logged"):
        with st.expander("🔐 Admin", expanded=False):
            pwd = st.text_input("Senha", type="password", label_visibility="collapsed",
                                placeholder="Senha admin", key="pwd")
            if st.button("Entrar", use_container_width=True, key="btn_login"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True; st.rerun()
                else: st.error("Senha incorreta")
    else:
        st.success("✅ Admin")
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            st.session_state.admin_logged = False; st.rerun()

    if st.button("🗑️ Nova Conversa", use_container_width=True, key="btn_nova"):
        st.session_state.messages = [{"role":"assistant","content":WELCOME_MSG}]
        st.session_state.quick_prompt = ""; st.rerun()

    # Status
    st.markdown(f"""
    <div class="status-pill">
        <div class="s-label">Sistema Operacional</div>
        <div class="s-val">● Online · {kb_count} fragmentos</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# COLUNA DIREITA
# ─────────────────────────────────────────────────
with col_R:

    # Header / cartão principal da tela
    st.markdown("""
    <div class="hamburger">☰</div>
    <div class="main-shell">
      <div class="app-card">
        <div class="app-header">
          <div class="icon-box">⚙️</div>
          <div>
            <h1>🛠️ Técnico Especialista em Manutenção Industrial</h1>
            <p class="sub">👨‍🔧 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
          </div>
        </div>
        <div class="intro-text">Olá! Sou seu assistente técnico experiente. Estou aqui para diagnosticar problemas e sugerir soluções rápidas para seu equipamento. Como posso ajudar?</div>
        <div class="quick-row">
    """, unsafe_allow_html=True)

    # Botões de ação rápida (3 fixos)
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

    st.markdown("""
        </div>
      </div>
    </div>
    <div class="chat-area">
    """, unsafe_allow_html=True)

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

    # Chat messages
    for msg in st.session_state.messages:
        avatar = "🔧" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image_bytes"):
                st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=300)

    # Ação rápida
    if st.session_state.quick_prompt:
        qp = st.session_state.quick_prompt
        st.session_state.quick_prompt = ""
        with st.chat_message("user", avatar="👤"): st.markdown(qp)
        st.session_state.messages.append({"role":"user","content":qp})
        full = do_chat(qp, None, None, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content":full})

    st.markdown("</div>", unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Digite sua pergunta ou anexe uma foto..."):
    uf = st.session_state.get("foto_up")
    img_b, mime, sfx = None, None, ""
    if uf:
        img_b = uf.read(); mime = uf.type; sfx = f"\n\n📷 *[{uf.name}]*"

    display = prompt + sfx
    umsg = {"role":"user","content":display}
    if img_b: umsg["image_bytes"] = img_b
    st.session_state.messages.append(umsg)

    with col_R:
        with st.chat_message("user", avatar="👤"):
            st.markdown(display)
            if img_b: st.image(PIL.Image.open(io.BytesIO(img_b)), width=300)
        full = do_chat(prompt, img_b, mime, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content":full})
