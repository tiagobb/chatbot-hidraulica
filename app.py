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
[data-testid="stToolbar"]  { display: none !important; }
[data-testid="stSidebar"]  { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp, .main { background: #0f172a !important; }
.block-container { padding: 1rem 1rem 5rem 1rem !important; max-width: 100% !important; }

/* ── PAINEL ESQUERDO ── */
.left-panel {
    background: #1e293b;
    border-radius: 14px;
    border: 1px solid #2d3f55;
    padding: 16px 14px;
    min-height: 80vh;
    position: sticky;
    top: 1rem;
}
.panel-section-title {
    font-size: .65rem; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 1.5px;
    padding-bottom: 8px; border-bottom: 1px solid #334155;
    margin-bottom: 10px;
}
.exp-item {
    display: flex; align-items: center; gap: 7px;
    padding: 6px 8px; border-radius: 6px; margin-bottom: 3px;
    background: #0f172a55; border: 1px solid #1e293b44;
    font-size: .8rem; color: #cbd5e1;
}
.status-box {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 8px; padding: 10px 12px; margin-top: 12px;
}

/* ── HEADER ── */
.app-header {
    background: linear-gradient(135deg, #0f2d5e 0%, #1e40af 60%, #1e3a5f 100%);
    border-radius: 14px; padding: 18px 22px 14px;
    margin-bottom: 12px; border: 1px solid #2563eb44;
    box-shadow: 0 6px 24px rgba(37,99,235,.2);
    display: flex; align-items: center; gap: 14px;
}
.app-header-icon { font-size: 2.2rem; line-height: 1; }
.app-header h1 { color: #fff; font-size: 1.3rem; font-weight: 800; margin: 0 0 3px 0; }
.app-header .sub { color: #93c5fd; font-size: .76rem; margin: 0; }

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 3px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1e293b !important; border-radius: 4px 14px 14px 14px !important;
    padding: 11px 15px !important; border: 1px solid #334155 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #0369a1, #0891b2) !important;
    border-radius: 14px 4px 14px 14px !important; padding: 10px 14px !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #e2e8f0 !important; font-size: .88rem !important; line-height: 1.65 !important; margin: 0 !important;
}
[data-testid="stChatMessage"] strong { color: #f1f5f9 !important; }
[data-testid="stChatMessage"] code { background: #0f172a !important; color: #fbbf24 !important; padding: 2px 5px !important; border-radius: 4px !important; }

/* ── INPUT ── */
[data-testid="stBottom"] { background: #0f172a !important; border-top: 1px solid #1e293b !important; padding: 8px 16px !important; }
[data-testid="stChatInput"] { background: #1e293b !important; border: 1.5px solid #334155 !important; border-radius: 12px !important; }
[data-testid="stChatInput"]:focus-within { border-color: #10b981 !important; box-shadow: 0 0 0 3px rgba(16,185,129,.1) !important; }
[data-testid="stChatInput"] > div { background: #1e293b !important; }
[data-testid="stChatInput"] textarea { color: #e2e8f0 !important; background: #1e293b !important; caret-color: #10b981 !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #64748b !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: #1e293b !important; color: #e2e8f0 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important;
    font-weight: 500 !important; font-size: .82rem !important; transition: all .15s !important;
}
.stButton > button:hover { background: #334155 !important; border-color: #3b82f6 !important; color: #fff !important; }

/* ── FORM ELEMENTS ── */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #0f172a !important; color: #e2e8f0 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important;
}
[data-testid="stFileUploader"] { background: #0f172a !important; border: 1.5px dashed #334155 !important; border-radius: 8px !important; }
[data-testid="stFileUploader"] * { color: #94a3b8 !important; }
[data-testid="stExpander"] { background: #1e293b !important; border: 1px solid #334155 !important; border-radius: 10px !important; }
[data-testid="stExpander"] * { color: #e2e8f0 !important; }

/* ── SOURCE TAGS ── */
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf { background:#7f1d1d33; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d33; color:#f87171; border:1px solid #991b1b; }
.src-text { background:#14532d33; color:#86efac; border:1px solid #14532d; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
</style>
"""

# ── Supabase ───────────────────────────────────────────────────────────────────
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
                        content = json.loads(s)["choices"][0]["delta"].get("content","")
                        if content: yield content
                    except: pass

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Técnico Especialista em Manutenção", page_icon="🔧", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada.")
    st.stop()

sb       = get_supabase() if SUPABASE_URL and SUPABASE_KEY else None
kb_count = count_docs(sb) if sb else 0

if "messages"     not in st.session_state: st.session_state.messages     = [{"role": "assistant", "content": WELCOME_MESSAGE}]
if "quick_prompt" not in st.session_state: st.session_state.quick_prompt = ""

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: coluna esquerda (painel) + coluna direita (chat)
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 3], gap="medium")

# ─────────────────────────────────────────────────
# PAINEL ESQUERDO
# ─────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)

    # Recursos adicionais
    st.markdown('<div class="panel-section-title">RECURSOS ADICIONAIS</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.76rem;font-weight:600;color:#94a3b8;margin-bottom:5px;">ANEXAR FOTO <span style="font-weight:400;color:#64748b">(opcional)</span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg","jpeg","png","webp"], label_visibility="collapsed", key="foto_upload")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Enviada com próxima mensagem")

    st.markdown("<br>", unsafe_allow_html=True)

    # Áreas de expertise
    st.markdown('<div class="panel-section-title">ÁREAS DE EXPERTISE</div>', unsafe_allow_html=True)
    for icon, label in [
        ("💧","Hidráulica Industrial"), ("⚡","Elétrica Industrial"),
        ("🔌","Eletrônica / VFD"),     ("⚙️","Eletromecânica / CNC"),
        ("🔩","Mecânica Industrial"),  ("🤖","Automação / CLP"),
        ("🌐","Redes Industriais"),
    ]:
        st.markdown(f'<div class="exp-item">{icon} {label}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin
    st.markdown('<div class="panel-section-title">🔐 PAINEL ADMIN</div>', unsafe_allow_html=True)
    if not st.session_state.get("admin_logged"):
        pwd = st.text_input("Senha", type="password", placeholder="Digite a senha", label_visibility="collapsed", key="admin_pwd")
        if st.button("Entrar", use_container_width=True, key="btn_entrar"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    else:
        st.success("✅ Admin conectado")
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            st.session_state.admin_logged = False
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Nova Conversa", use_container_width=True, key="btn_nova"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.session_state.quick_prompt = ""
        st.rerun()

    # Status
    st.markdown(f"""
    <div class="status-box">
        <div style="font-size:.65rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Sistema Operacional</div>
        <div style="font-size:.8rem;color:#10b981;font-weight:600;">● Online · {kb_count} fragmentos</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# COLUNA DIREITA — CHAT
# ─────────────────────────────────────────────────
with col_right:

    # Header
    st.markdown("""
    <div class="app-header">
      <div class="app-header-icon">🔧</div>
      <div>
        <h1>Técnico Especialista em Manutenção</h1>
        <p class="sub">🏆 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Botões de ação rápida
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔧 Diagnosticar Falha", use_container_width=True, key="q1"):
            st.session_state.quick_prompt = "Preciso diagnosticar uma falha no equipamento. Me faça as perguntas necessárias para identificar o problema."
            st.rerun()
    with b2:
        if st.button("🔍 Identificar Componente", use_container_width=True, key="q2"):
            st.session_state.quick_prompt = "Preciso identificar um componente hidráulico ou elétrico. Como posso descrevê-lo para você identificar?"
            st.rerun()
    with b3:
        if st.button("📋 Consultar Esquema", use_container_width=True, key="q3"):
            st.session_state.quick_prompt = "Preciso de ajuda para interpretar ou montar um esquema hidráulico ou elétrico."
            st.rerun()

    # Admin panel expandido
    if st.session_state.get("admin_logged") and sb:
        with st.expander("📚 BASE DE CONHECIMENTO — Adicionar / Gerenciar", expanded=True):
            tab1, tab2, tab3, tab4 = st.tabs(["📄 PDF","✍️ Texto","🎥 YouTube","🗂️ Gerenciar"])
            with tab1:
                pdf_title = st.text_input("Título", placeholder="Ex: Manual Bomba Rexroth A10V", key="pdf_title")
                pdf_file  = st.file_uploader("PDF", type=["pdf"], key="pdf_upload")
                if st.button("📤 Processar e Salvar", key="btn_pdf"):
                    if not pdf_title: st.warning("Digite um título.")
                    elif not pdf_file: st.warning("Selecione um PDF.")
                    else:
                        with st.spinner("Processando..."):
                            text = extract_pdf(pdf_file.read())
                            if text.startswith("Erro"): st.error(text)
                            else:
                                n = upload_doc(pdf_title, text, "pdf", pdf_file.name, sb)
                                st.success(f"✅ {n} fragmentos salvos!"); st.rerun()
            with tab2:
                txt_title   = st.text_input("Título", placeholder="Ex: Procedimento Troca de Óleo", key="txt_title")
                txt_content = st.text_area("Conteúdo", placeholder="Cole o texto técnico aqui...", height=160, key="txt_content")
                if st.button("💾 Salvar", key="btn_txt"):
                    if not txt_title: st.warning("Digite um título.")
                    elif not txt_content: st.warning("Digite o conteúdo.")
                    else:
                        with st.spinner("Salvando..."):
                            n = upload_doc(txt_title, txt_content, "text", "manual", sb)
                            st.success(f"✅ {n} fragmentos salvos!"); st.rerun()
            with tab3:
                yt_title = st.text_input("Título", placeholder="Ex: Aula Hidráulica Industrial", key="yt_title")
                yt_url   = st.text_input("URL do YouTube", placeholder="https://youtube.com/watch?v=...", key="yt_url")
                st.caption("⚠️ O vídeo precisa ter legendas em português ou inglês.")
                if st.button("📥 Extrair e Salvar", key="btn_yt"):
                    if not yt_title: st.warning("Digite um título.")
                    elif not yt_url: st.warning("Digite a URL.")
                    else:
                        with st.spinner("Extraindo..."):
                            text, error = get_youtube_transcript(yt_url)
                            if error: st.error(f"Erro: {error}")
                            else:
                                n = upload_doc(yt_title, text, "youtube", yt_url, sb)
                                st.success(f"✅ {n} fragmentos salvos!"); st.rerun()
            with tab4:
                docs = get_all_docs(sb)
                if not docs: st.info("Base vazia.")
                else:
                    for title in list({d["title"] for d in docs}):
                        chunks = [d for d in docs if d["title"] == title]
                        src    = chunks[0]["source_type"]
                        color  = {"pdf":"src-pdf","youtube":"src-youtube","text":"src-text"}.get(src,"src-text")
                        c1, c2 = st.columns([5,1])
                        with c1:
                            st.markdown(f'<span class="source-tag {color}">{src.upper()}</span> **{title}** <small style="color:#64748b">({len(chunks)} frag.)</small>', unsafe_allow_html=True)
                        with c2:
                            if st.button("🗑️", key=f"del_{title}"):
                                delete_doc(title, sb); st.rerun()
                        st.divider()

    # Mensagens do chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("image_bytes"):
                st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=300)

    # Ação rápida
    if st.session_state.quick_prompt:
        qp = st.session_state.quick_prompt
        st.session_state.quick_prompt = ""
        with st.chat_message("user"):
            st.markdown(qp)
        st.session_state.messages.append({"role":"user","content": qp})

        rag = ""
        if sb and kb_count > 0:
            results = search_knowledge(qp, sb)
            if results:
                rag = "\n\n---\n**CONHECIMENTO DA BASE:**\n" + "".join(f"\n📚 [{r['title']}]:\n{r['content']}\n" for r in results) + "---\n"

        api_msgs = [{"role":"system","content": SYSTEM_PROMPT + rag}]
        for m in st.session_state.messages[:-1]:
            if m["role"] in ("user","assistant"):
                api_msgs.append({"role":m["role"],"content":m["content"]})
        api_msgs.append({"role":"user","content": qp})

        with st.chat_message("assistant"):
            ph = st.empty(); full = ""
            try:
                for chunk in stream_groq(api_msgs, GROQ_API_KEY, TEXT_MODEL):
                    full += chunk; ph.markdown(full + "▌")
                ph.markdown(full)
            except Exception as e:
                ph.error(str(e)[:200]); full = ""
        if full:
            st.session_state.messages.append({"role":"assistant","content": full})

# ── Chat input (sempre no rodapé) ─────────────────────────────────────────────
if prompt := st.chat_input("Digite sua pergunta ou descreva o problema..."):
    image_bytes, mime_type, display_suffix = None, None, ""
    uploaded_file = st.session_state.get("foto_upload")
    if uploaded_file:
        image_bytes    = uploaded_file.read()
        mime_type      = uploaded_file.type
        display_suffix = f"\n\n📷 *[{uploaded_file.name}]*"

    display_text = prompt + display_suffix
    user_msg = {"role":"user","content": display_text}
    if image_bytes: user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with col_right:
        with st.chat_message("user"):
            st.markdown(display_text)
            if image_bytes:
                st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=300)

    rag = ""
    if sb and kb_count > 0:
        results = search_knowledge(prompt, sb)
        if results:
            rag = "\n\n---\n**CONHECIMENTO DA BASE:**\n" + "".join(f"\n📚 [{r['title']}]:\n{r['content']}\n" for r in results) + "---\n"

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

    with col_right:
        with st.chat_message("assistant"):
            if rag: st.caption("📚 Consultando base de conhecimento...")
            ph = st.empty(); full = ""
            try:
                for chunk in stream_groq(api_msgs, GROQ_API_KEY, model):
                    full += chunk; ph.markdown(full + "▌")
                ph.markdown(full)
            except requests.HTTPError as e:
                ph.error(f"Erro {e.response.status_code}: {e.response.text[:200]}"); full = ""

    if full:
        st.session_state.messages.append({"role":"assistant","content": full})
