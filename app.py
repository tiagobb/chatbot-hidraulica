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

- Hidráulica Industrial (circuitos, componentes, óleos, simbologia ISO 1219, servo-hidráulica, hidráulica móvel e estacionária)
- Elétrica Industrial (instalações, motores, quadros de comando, NR-10, NBR 5410, NR-12)
- Eletrônica Industrial (componentes, inversores de frequência VFD, soft-starters, instrumentação)
- Eletromecânica (servo-motores, freios eletromagnéticos, CNC)
- Mecânica Industrial (transmissões, rolamentos, vedações, pneumática)
- Informática Industrial (redes Ethernet/IP, Profibus, Modbus, Profinet, SCADA, HMI, CMMS)
- Automação Industrial (CLPs, Ladder/FBD/ST, PID, Industria 4.0, IIoT)

Quando houver CONHECIMENTO RELEVANTE DA BASE DE DADOS no contexto, use-o como referência principal para responder, citando a fonte quando pertinente.

Comportamento:
- Use linguagem técnica precisa e clara
- Cite normas técnicas relevantes (ISO, NBR, NR, etc.)
- Ofereça exemplos práticos e procedimentos passo a passo
- Quando receber uma imagem, analise-a detalhadamente
- Priorize segurança: sempre alerte sobre riscos
- Responda sempre em português do Brasil"""

WELCOME_MESSAGE = (
    "Olá! Sou seu **Técnico Especialista em Manutenção** com mais de 20 anos de experiência.\n\n"
    "Posso ajudar com **hidráulica, elétrica, automação, mecânica** e muito mais.\n\n"
    "Digite sua pergunta, use os botões de ação rápida, ou anexe uma foto do equipamento. 👇"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.stApp, .main { background-color: #0f172a !important; }
.block-container { padding: 1.2rem 1.5rem 5rem 1.5rem !important; max-width: 860px !important; margin: 0 auto !important; }

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #0f2d5e 0%, #1e40af 60%, #1e3a5f 100%);
    border-radius: 16px; padding: 22px 26px 18px; margin-bottom: 12px;
    border: 1px solid #2563eb44; box-shadow: 0 8px 32px rgba(37,99,235,.2);
}
.app-header h1 { color:#fff; font-size:1.5rem; font-weight:800; margin:0 0 4px 0; }
.app-header .subtitle { color:#93c5fd; font-size:.8rem; margin:0 0 14px 0; }
.expertise-tags { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
.etag { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15); color:#e2e8f0; font-size:.72rem; padding:3px 10px; border-radius:20px; }
.quick-btns { display:flex; gap:8px; flex-wrap:wrap; }

/* ── Toolbar row ── */
.toolbar { display:flex; gap:8px; align-items:center; margin-bottom:10px; flex-wrap:wrap; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] { background:transparent !important; border:none !important; padding:4px 0 !important; margin-bottom:2px !important; }
[data-testid="stChatMessage"] > div { background:transparent !important; }

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background:#1e293b !important; border-radius:4px 16px 16px 16px !important;
    padding:12px 16px !important; border:1px solid #334155 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background:linear-gradient(135deg,#0369a1,#0891b2) !important;
    border-radius:16px 4px 16px 16px !important; padding:11px 15px !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li { color:#e2e8f0 !important; font-size:.9rem !important; line-height:1.65 !important; margin:0 !important; }
[data-testid="stChatMessage"] strong { color:#f1f5f9 !important; }
[data-testid="stChatMessage"] code { background:#0f172a !important; color:#fbbf24 !important; padding:2px 6px !important; border-radius:4px !important; }

/* ── Input ── */
[data-testid="stBottom"] { background:#0f172a !important; border-top:1px solid #1e293b !important; }
[data-testid="stChatInput"] { background:#1e293b !important; border:1.5px solid #334155 !important; border-radius:12px !important; }
[data-testid="stChatInput"]:focus-within { border-color:#10b981 !important; box-shadow:0 0 0 3px rgba(16,185,129,.12) !important; }
[data-testid="stChatInput"] > div { background:#1e293b !important; }
[data-testid="stChatInput"] textarea { color:#e2e8f0 !important; background:#1e293b !important; caret-color:#10b981 !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#64748b !important; }

/* ── Buttons ── */
.stButton > button {
    background:#1e293b !important; color:#e2e8f0 !important;
    border:1px solid #334155 !important; border-radius:8px !important;
    font-weight:500 !important; transition:all .2s !important;
    font-size:.85rem !important;
}
.stButton > button:hover { background:#334155 !important; border-color:#3b82f6 !important; color:#fff !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background:#1e293b !important; border:1px solid #334155 !important; border-radius:10px !important; }
[data-testid="stExpander"] summary { color:#e2e8f0 !important; }
[data-testid="stExpander"] * { color:#e2e8f0 !important; }
[data-testid="stExpander"] p { color:#e2e8f0 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] { background:#0f172a !important; border:1.5px dashed #334155 !important; border-radius:10px !important; }
[data-testid="stFileUploader"] * { color:#94a3b8 !important; }
[data-testid="stFileUploader"] small { color:#64748b !important; }

/* ── Inputs/textareas ── */
.stTextInput > div > div > input { background:#0f172a !important; color:#e2e8f0 !important; border:1px solid #334155 !important; border-radius:8px !important; }
.stTextArea > div > div > textarea { background:#0f172a !important; color:#e2e8f0 !important; border:1px solid #334155 !important; border-radius:8px !important; }
.stSelectbox > div > div { background:#0f172a !important; color:#e2e8f0 !important; }

/* ── Source tags ── */
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf { background:#7f1d1d33; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d33; color:#f87171; border:1px solid #991b1b; }
.src-text { background:#14532d33; color:#86efac; border:1px solid #14532d; }

/* ── Alerts ── */
.stAlert { background:#1e293b !important; border-radius:8px !important; }
.stSuccess { border-left:3px solid #10b981 !important; }
.stError { border-left:3px solid #ef4444 !important; }
.stWarning { border-left:3px solid #f59e0b !important; }
.stInfo { border-left:3px solid #3b82f6 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:#0f172a; }
::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }
</style>
"""

# ── Supabase ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Processamento de texto ─────────────────────────────────────────────────────
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

# ── Base de conhecimento ───────────────────────────────────────────────────────
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

# ── Groq ───────────────────────────────────────────────────────────────────────
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
                        content = json.loads(s)["choices"][0]["delta"].get("content","")
                        if content: yield content
                    except: pass

# ── App ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada.")
    st.stop()

sb = get_supabase() if SUPABASE_URL and SUPABASE_KEY else None
kb_count = count_docs(sb) if sb else 0

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = ""
if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
  <h1>🔧 Técnico Especialista em Manutenção</h1>
  <p class="subtitle">🏆 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
  <div class="expertise-tags">
    <span class="etag">💧 Hidráulica</span>
    <span class="etag">⚡ Elétrica</span>
    <span class="etag">🔌 Eletrônica/VFD</span>
    <span class="etag">⚙️ Eletromecânica</span>
    <span class="etag">🔩 Mecânica</span>
    <span class="etag">🤖 Automação/CLP</span>
    <span class="etag">🌐 Redes Industriais</span>
    <span class="etag">📚 {kb_count} fragmentos</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Botões de ação rápida ──────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔧 Diagnosticar Falha", use_container_width=True):
        st.session_state.quick_prompt = "Preciso diagnosticar uma falha no equipamento. Me faça as perguntas necessárias para identificar o problema."
        st.rerun()
with col2:
    if st.button("🔍 Identificar Componente", use_container_width=True):
        st.session_state.quick_prompt = "Preciso identificar um componente hidráulico ou elétrico. Como posso descrevê-lo para você identificar?"
        st.rerun()
with col3:
    if st.button("📋 Consultar Esquema", use_container_width=True):
        st.session_state.quick_prompt = "Preciso de ajuda para interpretar ou montar um esquema hidráulico ou elétrico."
        st.rerun()

# ── Toolbar: foto / admin / nova conversa ─────────────────────────────────────
t1, t2, t3 = st.columns([2, 2, 2])
with t1:
    if st.button("📷 Anexar Foto", use_container_width=True):
        st.session_state.show_upload = not st.session_state.show_upload
        st.rerun()
with t2:
    if not st.session_state.get("admin_logged"):
        if st.button("🔐 Painel Admin", use_container_width=True):
            st.session_state.show_admin_login = not st.session_state.get("show_admin_login", False)
            st.rerun()
    else:
        if st.button("🔓 Sair do Admin", use_container_width=True):
            st.session_state.admin_logged = False
            st.rerun()
with t3:
    if st.button("🗑️ Nova Conversa", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.session_state.quick_prompt = ""
        st.session_state.show_upload = False
        st.rerun()

# ── Área de upload de foto ─────────────────────────────────────────────────────
uploaded_file = None
if st.session_state.show_upload:
    with st.container():
        st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;margin-bottom:10px;">', unsafe_allow_html=True)
        st.markdown("**📷 Anexar imagem ao próximo envio**")
        uploaded_file = st.file_uploader("Selecione ou tire uma foto", type=["jpg","jpeg","png","webp"], label_visibility="collapsed")
        if uploaded_file:
            st.image(uploaded_file, width=280)
            st.success("✅ Imagem pronta — será enviada com sua próxima mensagem")
        st.markdown('</div>', unsafe_allow_html=True)

# ── Login admin ───────────────────────────────────────────────────────────────
if st.session_state.get("show_admin_login") and not st.session_state.get("admin_logged"):
    with st.container():
        st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;margin-bottom:10px;">', unsafe_allow_html=True)
        pwd = st.text_input("🔐 Senha do Admin", type="password", placeholder="Digite a senha", key="admin_pwd")
        if st.button("Entrar", key="btn_login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.session_state.show_admin_login = False
                st.rerun()
            else:
                st.error("Senha incorreta")
        st.markdown('</div>', unsafe_allow_html=True)

# ── Painel Admin ───────────────────────────────────────────────────────────────
if st.session_state.get("admin_logged") and sb:
    st.success("✅ Admin conectado")
    with st.expander("📚 BASE DE CONHECIMENTO — Adicionar / Gerenciar", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload PDF", "✍️ Texto", "🎥 YouTube", "🗂️ Gerenciar"])

        with tab1:
            st.markdown("**Envie manuais e documentos em PDF**")
            pdf_title = st.text_input("Título", placeholder="Ex: Manual Bomba Rexroth A10V", key="pdf_title")
            pdf_file  = st.file_uploader("Selecione o PDF", type=["pdf"], key="pdf_upload")
            if st.button("📤 Processar e Salvar PDF", key="btn_pdf"):
                if not pdf_title: st.warning("Digite um título.")
                elif not pdf_file: st.warning("Selecione um PDF.")
                else:
                    with st.spinner("Processando..."):
                        text = extract_pdf(pdf_file.read())
                        if text.startswith("Erro"): st.error(text)
                        else:
                            n = upload_doc(pdf_title, text, "pdf", pdf_file.name, sb)
                            st.success(f"✅ PDF salvo em {n} fragmentos!")
                            st.rerun()

        with tab2:
            st.markdown("**Cole procedimentos, normas ou textos técnicos**")
            txt_title   = st.text_input("Título", placeholder="Ex: Procedimento Troca de Óleo", key="txt_title")
            txt_content = st.text_area("Conteúdo", placeholder="Cole o texto técnico aqui...", height=180, key="txt_content")
            if st.button("💾 Salvar Texto", key="btn_txt"):
                if not txt_title: st.warning("Digite um título.")
                elif not txt_content: st.warning("Digite o conteúdo.")
                else:
                    with st.spinner("Salvando..."):
                        n = upload_doc(txt_title, txt_content, "text", "manual", sb)
                        st.success(f"✅ Salvo em {n} fragmentos!")
                        st.rerun()

        with tab3:
            st.markdown("**Extraia transcrição de vídeos do YouTube**")
            yt_title = st.text_input("Título", placeholder="Ex: Aula Hidráulica Industrial", key="yt_title")
            yt_url   = st.text_input("URL do YouTube", placeholder="https://www.youtube.com/watch?v=...", key="yt_url")
            st.caption("⚠️ O vídeo precisa ter legendas em português ou inglês.")
            if st.button("📥 Extrair e Salvar", key="btn_yt"):
                if not yt_title: st.warning("Digite um título.")
                elif not yt_url: st.warning("Digite a URL.")
                else:
                    with st.spinner("Extraindo transcrição..."):
                        text, error = get_youtube_transcript(yt_url)
                        if error: st.error(f"Erro: {error}")
                        else:
                            n = upload_doc(yt_title, text, "youtube", yt_url, sb)
                            st.success(f"✅ Salvo em {n} fragmentos!")
                            st.rerun()

        with tab4:
            docs = get_all_docs(sb)
            if not docs:
                st.info("Base vazia. Adicione documentos nas outras abas.")
            else:
                titles = list({d["title"] for d in docs})
                for title in titles:
                    chunks = [d for d in docs if d["title"] == title]
                    src    = chunks[0]["source_type"]
                    color  = {"pdf":"src-pdf","youtube":"src-youtube","text":"src-text"}.get(src,"src-text")
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f'<span class="source-tag {color}">{src.upper()}</span> **{title}** <small style="color:#64748b">({len(chunks)} fragmentos)</small>', unsafe_allow_html=True)
                    with c2:
                        if st.button("🗑️", key=f"del_{title}"):
                            delete_doc(title, sb)
                            st.rerun()
                    st.divider()

# ── Chat ───────────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image_bytes"):
            st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=320)

# Processa ação rápida
if st.session_state.quick_prompt:
    qp = st.session_state.quick_prompt
    st.session_state.quick_prompt = ""
    with st.chat_message("user"):
        st.markdown(qp)
    st.session_state.messages.append({"role": "user", "content": qp})

    rag_context = ""
    if sb and kb_count > 0:
        results = search_knowledge(qp, sb)
        if results:
            rag_context = "\n\n---\n**CONHECIMENTO DA BASE:**\n"
            for r in results:
                rag_context += f"\n📚 [{r['title']}]:\n{r['content']}\n"
            rag_context += "---\n"

    api_msgs = [{"role":"system","content": SYSTEM_PROMPT + rag_context}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user","assistant"):
            api_msgs.append({"role": m["role"], "content": m["content"]})
    api_msgs.append({"role":"user","content": qp})

    with st.chat_message("assistant"):
        ph = st.empty()
        full = ""
        try:
            for chunk in stream_groq(api_msgs, GROQ_API_KEY, TEXT_MODEL):
                full += chunk
                ph.markdown(full + "▌")
            ph.markdown(full)
        except Exception as e:
            ph.error(str(e)[:200])
            full = ""
    if full:
        st.session_state.messages.append({"role":"assistant","content": full})

# Input do usuário
if prompt := st.chat_input("Digite sua pergunta ou descreva o problema..."):
    image_bytes, mime_type, display_suffix = None, None, ""
    if uploaded_file:
        image_bytes = uploaded_file.read()
        mime_type   = uploaded_file.type
        display_suffix = f"\n\n📷 *[{uploaded_file.name}]*"

    display_text = prompt + display_suffix
    user_msg = {"role":"user","content": display_text}
    if image_bytes: user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(display_text)
        if image_bytes:
            st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=320)

    # RAG
    rag_context = ""
    if sb and kb_count > 0:
        results = search_knowledge(prompt, sb)
        if results:
            rag_context = "\n\n---\n**CONHECIMENTO DA BASE:**\n"
            for r in results:
                rag_context += f"\n📚 [{r['title']}]:\n{r['content']}\n"
            rag_context += "---\n"

    api_msgs = [{"role":"system","content": SYSTEM_PROMPT + rag_context}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user","assistant"):
            api_msgs.append({"role": m["role"], "content": m["content"]})

    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        api_msgs.append({"role":"user","content":[
            {"type":"text","text": prompt + rag_context},
            {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
        ]})
        model = VISION_MODEL
    else:
        api_msgs.append({"role":"user","content": prompt})
        model = TEXT_MODEL

    with st.chat_message("assistant"):
        if rag_context: st.caption("📚 Consultando base de conhecimento...")
        ph = st.empty()
        full = ""
        try:
            for chunk in stream_groq(api_msgs, GROQ_API_KEY, model):
                full += chunk
                ph.markdown(full + "▌")
            ph.markdown(full)
        except requests.HTTPError as e:
            ph.error(f"Erro {e.response.status_code}: {e.response.text[:200]}")
            full = ""

    if full:
        st.session_state.messages.append({"role":"assistant","content": full})
