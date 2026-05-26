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

WELCOME_MESSAGE = "Olá! Sou seu **Técnico Especialista em Manutenção** com mais de 20 anos de experiência.\n\nSelecione a área na barra lateral ou use os atalhos rápidos abaixo para começar."

# Ações rápidas por área
AREA_ACTIONS = {
    "💧 Hidráulica Industrial": [
        ("🔊 Ruído / Cavitação",        "Estou com ruído excessivo na bomba hidráulica. Como identificar se é cavitação e quais são as causas?"),
        ("🌡️ Óleo Superaquecido",       "O óleo do sistema hidráulico está superaquecendo acima de 60°C. Quais as principais causas e soluções?"),
        ("📊 Simbologia de Válvulas",    "Pode me ajudar a interpretar a simbologia ISO 1219 de válvulas hidráulicas?"),
    ],
    "⚡ Elétrica Industrial": [
        ("⚡ Disjuntor Atuando",         "O disjuntor está atuando com frequência. Como identificar a causa — sobrecarga, curto ou falha?"),
        ("🔥 Motor Aquecendo",           "O motor elétrico está aquecendo além do normal. Quais causas e como medir a temperatura adequadamente?"),
        ("📋 Verificar NR-10 / NR-12",   "Quais são os principais requisitos da NR-10 para trabalho seguro em instalações elétricas?"),
    ],
    "🔌 Eletrônica / VFD": [
        ("🔴 Falha no Inversor",         "O inversor de frequência está apresentando falha. Como interpretar os códigos de erro mais comuns?"),
        ("📈 Configurar Rampa VFD",      "Como configurar corretamente a rampa de aceleração e desaceleração em um inversor de frequência?"),
        ("🔧 Soft-Starter com Problema", "O soft-starter não está acionando o motor. Quais os pontos de verificação?"),
    ],
    "⚙️ Eletromecânica / CNC": [
        ("🎯 Alarme no CNC",             "O CNC está gerando alarme durante o ciclo de trabalho. Como fazer o diagnóstico inicial?"),
        ("🔩 Servo-Motor com Vibração",  "O servo-motor está vibrando excessivamente. Quais as causas e como ajustar os parâmetros PID?"),
        ("🛑 Freio Eletromagnético",     "O freio eletromagnético não está liberando corretamente. Como verificar a bobina e o entreferro?"),
    ],
    "🔩 Mecânica Industrial": [
        ("🔊 Rolamento com Ruído",       "O rolamento está com ruído anormal. Como identificar o tipo de falha e o momento de troca?"),
        ("💨 Vazamento de Vedação",      "Estou com vazamento em vedações. Como selecionar o tipo correto de retentor ou gaxeta?"),
        ("⚙️ Correia / Transmissão",     "Como fazer o alinhamento correto de polias e verificar a tensão adequada da correia?"),
    ],
    "🤖 Automação / CLP": [
        ("🔴 CLP em Falha",              "O CLP entrou em modo de falha (FAULT). Como fazer o diagnóstico e recovery do sistema?"),
        ("📝 Lógica Ladder",             "Preciso entender uma lógica Ladder com temporizadores e contadores. Pode explicar?"),
        ("🌐 Comunicação Modbus",        "Como configurar a comunicação Modbus RTU entre o CLP e um inversor de frequência?"),
    ],
    "🌐 Redes Industriais": [
        ("📡 Falha na Rede Profibus",    "A rede Profibus está com falha de comunicação em um escravo. Como diagnosticar?"),
        ("🔗 Configurar Ethernet/IP",    "Como configurar um dispositivo Ethernet/IP no CLP e verificar a conexão?"),
        ("📊 Instalar SCADA/HMI",        "Quais os passos para configurar a comunicação entre um SCADA e o CLP via OPC?"),
    ],
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp, .main { background-color: #1A1D24 !important; }
.block-container { padding: 1rem 1rem 5rem 1rem !important; max-width: 100% !important; }

/* ── PAINEL ESQUERDO ── */
[data-testid="stColumn"]:first-child {
    background-color: #232732 !important;
    border-radius: 12px !important;
    border: 1px solid #2F3545 !important;
    padding: 0 4px !important;
}
.panel-title {
    font-size: .62rem; font-weight: 700; color: #8A99AD;
    text-transform: uppercase; letter-spacing: 1.8px;
    padding: 10px 0 8px; border-bottom: 1px solid #2F3545; margin-bottom: 10px;
}
.area-item {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 10px; border-radius: 7px; margin-bottom: 3px;
    background: #1A1D2444; font-size: .82rem; color: #CBD5E1;
    cursor: pointer;
}
.status-box {
    background: #1A1D24; border: 1px solid #2F3545;
    border-radius: 8px; padding: 10px 12px; margin-top: 14px;
}

/* ── HEADER / WELCOME CARD ── */
.welcome-card {
    background: linear-gradient(135deg, #1E2230 0%, #232732 100%);
    border-left: 5px solid #007ACC;
    border-radius: 10px; padding: 20px 24px; margin-bottom: 14px;
    box-shadow: 0 4px 16px rgba(0,122,204,.1);
}
.welcome-card h1 { color: #FFFFFF; font-size: 1.4rem; font-weight: 800; margin: 0 0 4px 0; }
.welcome-card .sub { color: #8A99AD; font-size: .8rem; margin: 0; }
.area-badge {
    display: inline-block; background: #007ACC22; border: 1px solid #007ACC55;
    color: #60AEFF; font-size: .75rem; font-weight: 600;
    padding: 3px 12px; border-radius: 20px; margin-top: 10px;
}

/* ── BOTÕES ── */
.stButton > button {
    background-color: #2D323F !important; color: #E0E6F0 !important;
    border: 1px solid #3A4255 !important; border-radius: 20px !important;
    font-weight: 500 !important; font-size: .83rem !important;
    transition: all .2s !important; padding: 8px 14px !important;
}
.stButton > button:hover {
    border-color: #007ACC !important; color: #60AEFF !important;
    background-color: #282E3D !important;
}

/* ── CHAT ── */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 4px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #232732 !important; border-radius: 4px 14px 14px 14px !important;
    padding: 12px 16px !important; border: 1px solid #2F3545 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #005A99, #007ACC) !important;
    border-radius: 14px 4px 14px 14px !important; padding: 11px 15px !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #E2E8F0 !important; font-size: .9rem !important; line-height: 1.65 !important; margin: 0 !important;
}
[data-testid="stChatMessage"] strong { color: #FFFFFF !important; }
[data-testid="stChatMessage"] code { background: #1A1D24 !important; color: #FFC857 !important; padding: 2px 5px !important; border-radius: 4px !important; }

/* ── INPUT ── */
[data-testid="stBottom"] { background: #1A1D24 !important; border-top: 1px solid #2F3545 !important; }
[data-testid="stChatInput"] { background: #232732 !important; border: 1.5px solid #3A4255 !important; border-radius: 12px !important; }
[data-testid="stChatInput"]:focus-within { border-color: #007ACC !important; box-shadow: 0 0 0 3px rgba(0,122,204,.12) !important; }
[data-testid="stChatInput"] > div { background: #232732 !important; }
[data-testid="stChatInput"] textarea { color: #E2E8F0 !important; background: #232732 !important; caret-color: #007ACC !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #64748b !important; }

/* ── FORM INPUTS ── */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #1A1D24 !important; color: #E2E8F0 !important;
    border: 1px solid #3A4255 !important; border-radius: 8px !important;
}
[data-testid="stFileUploader"] { background: #1A1D24 !important; border: 1.5px dashed #3A4255 !important; border-radius: 8px !important; }
[data-testid="stFileUploader"] > div { background: #1A1D24 !important; }
[data-testid="stFileUploader"] section { background: #1A1D24 !important; border: none !important; }
[data-testid="stFileUploader"] * { color: #8A99AD !important; background: transparent !important; }
[data-testid="stFileDropzoneInstructions"] { background: #1A1D24 !important; }
[data-testid="stFileDropzone"] { background: #1A1D24 !important; border: 1.5px dashed #3A4255 !important; border-radius: 8px !important; }
[data-testid="stExpander"] { background: #232732 !important; border: 1px solid #2F3545 !important; border-radius: 10px !important; }
[data-testid="stExpander"] * { color: #E2E8F0 !important; }
[data-testid="stExpander"] summary p { color: #E2E8F0 !important; }

/* ── RADIO (área de seleção) — esconde círculos, vira lista ── */
[data-testid="stRadio"] > div { gap: 2px !important; }
[data-testid="stRadio"] label {
    color: #CBD5E1 !important; font-size: .82rem !important;
    background: #1A1D2466 !important; border: 1px solid #2F3545 !important;
    border-radius: 7px !important; padding: 6px 10px !important;
    cursor: pointer !important; width: 100% !important;
    transition: all .15s !important;
}
[data-testid="stRadio"] label:hover { background: #2D323F !important; border-color: #007ACC !important; color: #60AEFF !important; }
[data-testid="stRadio"] label[data-selected="true"],
[data-testid="stRadio"] input:checked + div { background: #007ACC22 !important; border-color: #007ACC !important; color: #60AEFF !important; }
/* Esconde o círculo do radio */
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { margin: 0 !important; }
[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }

/* ── SOURCE TAGS ── */
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf     { background:#7f1d1d33; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d33; color:#f87171; border:1px solid #991b1b; }
.src-text    { background:#14532d33; color:#86efac; border:1px solid #14532d; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #1A1D24; }
::-webkit-scrollbar-thumb { background: #3A4255; border-radius: 3px; }
</style>
"""

# ── Supabase & helpers ─────────────────────────────────────────────────────────
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

def extract_pdf(file_bytes):
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages).strip()
    except Exception as e:
        return f"Erro ao processar PDF: {e}"

def get_youtube_transcript(url):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        vid = url.split("youtu.be/")[1].split("?")[0] if "youtu.be/" in url else url.split("v=")[1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["pt","pt-BR","en"])
        return " ".join(t["text"] for t in transcript), None
    except Exception as e:
        return None, str(e)

def search_knowledge(query, sb):
    try:
        r = sb.rpc("buscar_conhecimento", {"consulta": query, "max_resultados": 4}).execute()
        return r.data or []
    except: return []

def upload_doc(title, content, source_type, source_ref, sb):
    chunks = chunk_text(content)
    for i, chunk in enumerate(chunks):
        sb.table("knowledge_base").insert({
            "title": title, "content": chunk,
            "source_type": source_type, "source_ref": source_ref, "chunk_index": i
        }).execute()
    return len(chunks)

def get_all_docs(sb):
    try:
        r = sb.table("knowledge_base").select("id,title,source_type,chunk_index,created_at").order("created_at", desc=True).execute()
        return r.data or []
    except: return []

def delete_doc(title, sb):
    try:
        sb.table("knowledge_base").delete().eq("title", title).execute()
        return True
    except: return False

def count_docs(sb):
    try:
        r = sb.table("knowledge_base").select("id", count="exact").execute()
        return r.count or 0
    except: return 0

def stream_groq(api_messages, api_key, model):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": api_messages, "stream": True, "temperature": 0.7, "max_tokens": 4096}
    with requests.post(GROQ_URL, headers=headers, json=body, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                d = line.decode("utf-8")
                if d.startswith("data: "):
                    s = d[6:].strip()
                    if s == "[DONE]": break
                    try:
                        c = json.loads(s)["choices"][0]["delta"].get("content","")
                        if c: yield c
                    except: pass

def do_rag(query, sb, kb_count):
    if not sb or kb_count == 0: return ""
    results = search_knowledge(query, sb)
    if not results: return ""
    ctx = "\n\n---\n**CONHECIMENTO DA BASE:**\n"
    for r in results:
        ctx += f"\n📚 [{r['title']}]:\n{r['content']}\n"
    return ctx + "---\n"

def send_message(prompt, image_bytes, mime_type, sb, kb_count):
    rag = do_rag(prompt, sb, kb_count)
    api_msgs = [{"role":"system","content": SYSTEM_PROMPT + rag}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user","assistant"):
            api_msgs.append({"role":m["role"],"content":m["content"]})
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        api_msgs.append({"role":"user","content":[
            {"type":"text","text": prompt + rag},
            {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
        ]})
        model = VISION_MODEL
    else:
        api_msgs.append({"role":"user","content": prompt})
        model = TEXT_MODEL

    with st.chat_message("assistant", avatar="🔧"):
        if rag: st.caption("📚 Consultando base de conhecimento...")
        ph = st.empty(); full = ""
        try:
            for chunk in stream_groq(api_msgs, GROQ_API_KEY, model):
                full += chunk; ph.markdown(full + "▌")
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

if "messages"     not in st.session_state: st.session_state.messages     = [{"role":"assistant","content": WELCOME_MESSAGE}]
if "quick_prompt" not in st.session_state: st.session_state.quick_prompt = ""

areas_list = list(AREA_ACTIONS.keys())

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: coluna esquerda + coluna direita
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 3], gap="medium")

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL ESQUERDO
# ─────────────────────────────────────────────────────────────────────────────
with col_left:
    # Foto
    st.markdown('<div class="panel-title">📎 Anexar Foto (opcional)</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg","jpeg","png","webp"], key="foto_up", label_visibility="collapsed")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Será enviada com a próxima mensagem")

    st.markdown("<br>", unsafe_allow_html=True)

    # Área de análise (radio dinâmico)
    st.markdown('<div class="panel-title">⚙️ Área de Análise</div>', unsafe_allow_html=True)
    area_selecionada = st.radio(
        "area", areas_list,
        label_visibility="collapsed",
        key="area_radio"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin
    st.markdown('<div class="panel-title">🔐 Painel Admin</div>', unsafe_allow_html=True)
    if not st.session_state.get("admin_logged"):
        pwd = st.text_input("Senha", type="password", placeholder="Senha admin", label_visibility="collapsed", key="pwd")
        if st.button("Entrar", use_container_width=True, key="btn_login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True; st.rerun()
            else:
                st.error("Senha incorreta")
    else:
        st.success("✅ Admin")
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            st.session_state.admin_logged = False; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Nova Conversa", use_container_width=True, key="btn_nova"):
        st.session_state.messages = [{"role":"assistant","content": WELCOME_MESSAGE}]
        st.session_state.quick_prompt = ""
        st.rerun()

    # Status
    st.markdown(f"""
    <div class="status-box">
        <div style="font-size:.62rem;color:#8A99AD;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Sistema Operacional</div>
        <div style="font-size:.82rem;color:#2ECC71;font-weight:600;">● Conectado · {kb_count} fragmentos</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COLUNA DIREITA
# ─────────────────────────────────────────────────────────────────────────────
with col_right:

    # Welcome card
    st.markdown(f"""
    <div class="welcome-card">
        <h1>🔧 Técnico Especialista em Manutenção</h1>
        <p class="sub">🏆 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
        <span class="area-badge">Foco atual: {area_selecionada[2:]}</span>
    </div>
    """, unsafe_allow_html=True)

    # Atalhos rápidos dinâmicos por área
    actions = AREA_ACTIONS.get(area_selecionada, [])
    b1, b2, b3 = st.columns(3)
    for col_btn, (label, prompt_text) in zip([b1, b2, b3], actions):
        with col_btn:
            if st.button(label, use_container_width=True, key=f"btn_{label}"):
                st.session_state.quick_prompt = prompt_text
                st.rerun()

    # Admin panel expandido
    if st.session_state.get("admin_logged") and sb:
        with st.expander("📚 BASE DE CONHECIMENTO — Adicionar / Gerenciar", expanded=False):
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
                            else: st.success(f"✅ {upload_doc(pt, text, 'pdf', pf.name, sb)} fragmentos!"); st.rerun()
            with tab2:
                tt = st.text_input("Título", placeholder="Ex: Procedimento Troca de Óleo", key="txt_t")
                tc = st.text_area("Conteúdo", placeholder="Cole o texto técnico aqui...", height=150, key="txt_c")
                if st.button("💾 Salvar Texto", key="btn_txt"):
                    if not tt: st.warning("Digite um título.")
                    elif not tc: st.warning("Digite o conteúdo.")
                    else:
                        with st.spinner("Salvando..."): st.success(f"✅ {upload_doc(tt, tc, 'text', 'manual', sb)} fragmentos!"); st.rerun()
            with tab3:
                yt = st.text_input("Título", placeholder="Ex: Aula Hidráulica Industrial", key="yt_t")
                yu = st.text_input("URL YouTube", placeholder="https://youtube.com/watch?v=...", key="yt_u")
                if st.button("📥 Extrair e Salvar", key="btn_yt"):
                    if not yt: st.warning("Digite um título.")
                    elif not yu: st.warning("Digite a URL.")
                    else:
                        with st.spinner("Extraindo..."):
                            text, err = get_youtube_transcript(yu)
                            if err: st.error(f"Erro: {err}")
                            else: st.success(f"✅ {upload_doc(yt, text, 'youtube', yu, sb)} fragmentos!"); st.rerun()
            with tab4:
                docs = get_all_docs(sb)
                if not docs: st.info("Base vazia.")
                else:
                    for title in list({d["title"] for d in docs}):
                        chunks = [d for d in docs if d["title"] == title]
                        src = chunks[0]["source_type"]
                        color = {"pdf":"src-pdf","youtube":"src-youtube","text":"src-text"}.get(src,"src-text")
                        c1, c2 = st.columns([5,1])
                        with c1: st.markdown(f'<span class="source-tag {color}">{src.upper()}</span> **{title}** <small style="color:#8A99AD">({len(chunks)} frag.)</small>', unsafe_allow_html=True)
                        with c2:
                            if st.button("🗑️", key=f"del_{title}"): delete_doc(title, sb); st.rerun()
                        st.divider()

    # Mensagens
    for msg in st.session_state.messages:
        avatar = "🔧" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image_bytes"):
                st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=300)

    # Atalho rápido
    if st.session_state.quick_prompt:
        qp = st.session_state.quick_prompt
        st.session_state.quick_prompt = ""
        with st.chat_message("user", avatar="👤"):
            st.markdown(qp)
        st.session_state.messages.append({"role":"user","content": qp})
        full = send_message(qp, None, None, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content": full})

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Descreva o problema técnico ou faça sua pergunta..."):
    uploaded_file = st.session_state.get("foto_up")
    image_bytes, mime_type, suffix = None, None, ""
    if uploaded_file:
        image_bytes = uploaded_file.read()
        mime_type   = uploaded_file.type
        suffix      = f"\n\n📷 *[{uploaded_file.name}]*"

    display = prompt + suffix
    user_msg = {"role":"user","content": display}
    if image_bytes: user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with col_right:
        with st.chat_message("user", avatar="👤"):
            st.markdown(display)
            if image_bytes: st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=300)

        full = send_message(prompt, image_bytes, mime_type, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content": full})
