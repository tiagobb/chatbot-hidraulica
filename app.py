import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os

# ── Configurações ─────────────────────────────────────────────────────────────
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
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
    "Olá! Sou especialista sênior em **manutenção industrial** com mais de 20 anos de experiência "
    "e acesso à base de conhecimento técnico da sua empresa.\n\n"
    "Pode digitar sua pergunta ou anexar uma **foto** do equipamento.\n\n"
    "Como posso ajudá-lo hoje?"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stApp, .main { background-color: #111827 !important; }
.block-container { padding: 1.5rem 2rem 5rem 2rem !important; max-width: 880px !important; }
[data-testid="stSidebar"] { background-color: #1f2937 !important; border-right: 1px solid #374151 !important; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #f59e0b !important; }
.app-header { background: linear-gradient(135deg,#1e3a5f 0%,#1e40af 100%); border-radius:12px; padding:22px 28px; margin-bottom:20px; border:1px solid #2563eb44; box-shadow:0 4px 24px rgba(37,99,235,.2); }
.app-header h1 { color:#fff; font-size:1.4rem; font-weight:700; margin:0 0 4px 0; }
.app-header .subtitle { color:#93c5fd; font-size:.78rem; margin:0; }
.header-badge { display:inline-flex; align-items:center; background:#052e1644; border:1px solid #10b981; color:#10b981; font-size:.65rem; font-weight:600; padding:3px 10px; border-radius:20px; margin-top:10px; text-transform:uppercase; letter-spacing:1px; }
.kb-badge { display:inline-flex; align-items:center; background:#1e3a5f44; border:1px solid #3b82f6; color:#93c5fd; font-size:.65rem; font-weight:600; padding:3px 10px; border-radius:20px; margin-top:4px; margin-left:6px; }
[data-testid="stChatMessage"] { background-color:#1f2937 !important; border-radius:10px !important; border:1px solid #374151 !important; margin-bottom:8px !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background-color:#1a2535 !important; border-left:3px solid #f59e0b !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { border-left:3px solid #3b82f6 !important; }
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li { color:#e5e7eb !important; font-size:.92rem !important; line-height:1.6 !important; }
[data-testid="stChatMessage"] strong { color:#f3f4f6 !important; }
[data-testid="stChatMessage"] code { background:#374151 !important; color:#fbbf24 !important; padding:2px 6px !important; border-radius:4px !important; }
[data-testid="stBottom"] { background-color:#111827 !important; }
[data-testid="stChatInput"] { background-color:#1f2937 !important; border:1.5px solid #374151 !important; border-radius:10px !important; }
[data-testid="stChatInput"]:focus-within { border-color:#3b82f6 !important; }
[data-testid="stChatInput"] textarea { color:#f9fafb !important; background-color:transparent !important; }
[data-testid="stFileUploader"] { background-color:#1f2937 !important; border:1.5px dashed #374151 !important; border-radius:8px !important; }
.stButton > button { border-radius:8px !important; font-weight:600 !important; }
.stTextInput > div > div > input { background-color:#1f2937 !important; color:#f9fafb !important; border:1px solid #374151 !important; border-radius:8px !important; }
.stTextArea > div > div > textarea { background-color:#1f2937 !important; color:#f9fafb !important; border:1px solid #374151 !important; border-radius:8px !important; }
.admin-box { background:#1f2937; border:1px solid #374151; border-radius:10px; padding:16px; margin-bottom:12px; }
.source-tag { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.7rem; font-weight:600; }
.src-pdf { background:#7f1d1d44; color:#fca5a5; border:1px solid #7f1d1d; }
.src-youtube { background:#7f1d1d44; color:#f87171; border:1px solid #991b1b; }
.src-text { background:#14532d44; color:#86efac; border:1px solid #14532d; }
::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:#111827; } ::-webkit-scrollbar-thumb { background:#374151; border-radius:3px; }
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
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
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
        if "youtu.be/" in url:
            vid = url.split("youtu.be/")[1].split("?")[0]
        elif "v=" in url:
            vid = url.split("v=")[1].split("&")[0]
        else:
            return None, "URL inválida"
        transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["pt", "pt-BR", "en"])
        return " ".join(t["text"] for t in transcript), None
    except Exception as e:
        return None, str(e)

# ── Banco de conhecimento ──────────────────────────────────────────────────────
def search_knowledge(query, sb):
    try:
        r = sb.rpc("buscar_conhecimento", {"consulta": query, "max_resultados": 4}).execute()
        return r.data or []
    except:
        return []

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
    except:
        return []

def delete_doc(title, sb):
    try:
        sb.table("knowledge_base").delete().eq("title", title).execute()
        return True
    except:
        return False

def count_docs(sb):
    try:
        r = sb.table("knowledge_base").select("id", count="exact").execute()
        return r.count or 0
    except:
        return 0

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
                    if s == "[DONE]":
                        break
                    try:
                        content = json.loads(s)["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except:
                        pass

# ── App ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Técnico Industrial", page_icon="⚙️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY não configurada.")
    st.stop()

sb = get_supabase() if SUPABASE_URL and SUPABASE_KEY else None
kb_count = count_docs(sb) if sb else 0

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding-bottom:1rem;border-bottom:1px solid #374151;margin-bottom:1rem;">
        <div style="font-size:2.5rem;">⚙️</div>
        <div style="color:#f9fafb;font-size:.95rem;font-weight:700;margin:6px 0 2px;">Técnico Industrial</div>
        <div style="color:#f59e0b;font-size:.65rem;text-transform:uppercase;letter-spacing:1.5px;">Assistente de Manutenção</div>
        <div style="margin-top:8px;">
            <span style="background:#052e1644;border:1px solid #10b981;color:#10b981;font-size:.65rem;padding:3px 10px;border-radius:20px;">● Online</span>
            <span style="background:#1e3a5f44;border:1px solid #3b82f6;color:#93c5fd;font-size:.65rem;padding:3px 10px;border-radius:20px;margin-left:4px;">📚 {kb_count} fragmentos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Imagem
    st.markdown('<div style="font-size:.7rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">📎 Anexar Imagem</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Será enviado com a próxima mensagem")

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin panel
    st.markdown('<div style="font-size:.7rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">🔐 Painel Admin</div>', unsafe_allow_html=True)

    if not st.session_state.get("admin_logged"):
        pwd = st.text_input("Senha", type="password", placeholder="Digite a senha admin", label_visibility="collapsed")
        if st.button("Entrar", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    else:
        st.success("✅ Admin conectado")
        if st.button("Sair do Admin", use_container_width=True):
            st.session_state.admin_logged = False
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Nova Conversa", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <h1>⚙️ Técnico Especialista em Manutenção Industrial</h1>
    <p class="subtitle">HIDRÁULICA &nbsp;·&nbsp; ELÉTRICA &nbsp;·&nbsp; AUTOMAÇÃO &nbsp;·&nbsp; MECÂNICA &nbsp;·&nbsp; ELETRÔNICA</p>
    <div class="header-badge">● IA Especializada · Groq · Llama 3.3</div>
    <div class="kb-badge">📚 Base de Conhecimento: {kb_count} fragmentos indexados</div>
</div>
""", unsafe_allow_html=True)

# ── Painel Admin (área principal) ──────────────────────────────────────────────
if st.session_state.get("admin_logged") and sb:
    with st.expander("📚 PAINEL DE ADMINISTRAÇÃO — Base de Conhecimento", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload PDF", "✍️ Texto", "🎥 YouTube", "🗂️ Gerenciar"])

        # ── Tab PDF ──
        with tab1:
            st.markdown("**Envie manuais, livros e documentos em PDF**")
            pdf_title = st.text_input("Título do documento", placeholder="Ex: Manual Bomba Rexroth A10V", key="pdf_title")
            pdf_file = st.file_uploader("Selecione o PDF", type=["pdf"], key="pdf_upload")
            if st.button("📤 Processar e Salvar PDF", key="btn_pdf"):
                if not pdf_title:
                    st.warning("Digite um título para o documento.")
                elif not pdf_file:
                    st.warning("Selecione um arquivo PDF.")
                else:
                    with st.spinner("Processando PDF..."):
                        text = extract_pdf(pdf_file.read())
                        if text.startswith("Erro"):
                            st.error(text)
                        else:
                            n = upload_doc(pdf_title, text, "pdf", pdf_file.name, sb)
                            st.success(f"✅ PDF salvo em {n} fragmentos na base de conhecimento!")
                            st.rerun()

        # ── Tab Texto ──
        with tab2:
            st.markdown("**Cole procedimentos, normas ou qualquer texto técnico**")
            txt_title = st.text_input("Título", placeholder="Ex: Procedimento Troca de Óleo Hidráulico", key="txt_title")
            txt_content = st.text_area("Conteúdo", placeholder="Cole o texto técnico aqui...", height=200, key="txt_content")
            if st.button("💾 Salvar Texto", key="btn_txt"):
                if not txt_title:
                    st.warning("Digite um título.")
                elif not txt_content:
                    st.warning("Digite o conteúdo.")
                else:
                    with st.spinner("Salvando..."):
                        n = upload_doc(txt_title, txt_content, "text", "manual", sb)
                        st.success(f"✅ Texto salvo em {n} fragmentos!")
                        st.rerun()

        # ── Tab YouTube ──
        with tab3:
            st.markdown("**Extraia a legenda/transcrição de vídeos do YouTube**")
            yt_title = st.text_input("Título do vídeo", placeholder="Ex: Aula Hidráulica Industrial - Circuitos", key="yt_title")
            yt_url = st.text_input("URL do YouTube", placeholder="https://www.youtube.com/watch?v=...", key="yt_url")
            st.caption("⚠️ O vídeo precisa ter legendas (automáticas ou manuais) em português ou inglês.")
            if st.button("📥 Extrair e Salvar Transcrição", key="btn_yt"):
                if not yt_title:
                    st.warning("Digite um título.")
                elif not yt_url:
                    st.warning("Digite a URL do YouTube.")
                else:
                    with st.spinner("Extraindo transcrição do YouTube..."):
                        text, error = get_youtube_transcript(yt_url)
                        if error:
                            st.error(f"Erro: {error}")
                        else:
                            n = upload_doc(yt_title, text, "youtube", yt_url, sb)
                            st.success(f"✅ Transcrição salva em {n} fragmentos!")
                            st.rerun()

        # ── Tab Gerenciar ──
        with tab4:
            st.markdown("**Documentos na base de conhecimento**")
            docs = get_all_docs(sb)
            if not docs:
                st.info("Base de conhecimento vazia. Adicione documentos nas outras abas.")
            else:
                titles = list({d["title"] for d in docs})
                for title in titles:
                    doc_chunks = [d for d in docs if d["title"] == title]
                    src = doc_chunks[0]["source_type"]
                    color = {"pdf": "src-pdf", "youtube": "src-youtube", "text": "src-text"}.get(src, "src-text")
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f'<span class="source-tag {color}">{src.upper()}</span> **{title}** <small style="color:#6b7280">({len(doc_chunks)} fragmentos)</small>', unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️", key=f"del_{title}", help=f"Excluir '{title}'"):
                            delete_doc(title, sb)
                            st.success(f"'{title}' removido!")
                            st.rerun()
                    st.divider()

# ── Chat ───────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image_bytes"):
            st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=360)

if prompt := st.chat_input("Digite sua pergunta técnica..."):
    image_bytes, mime_type, display_suffix = None, None, ""

    if uploaded_file:
        image_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        display_suffix = f"\n\n📷 *[{uploaded_file.name}]*"

    display_text = prompt + display_suffix
    user_msg = {"role": "user", "content": display_text}
    if image_bytes:
        user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(display_text)
        if image_bytes:
            st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=360)

    # RAG: busca conhecimento relevante
    rag_context = ""
    if sb and kb_count > 0:
        results = search_knowledge(prompt, sb)
        if results:
            rag_context = "\n\n---\n**CONHECIMENTO RELEVANTE DA BASE DE DADOS:**\n"
            for r in results:
                rag_context += f"\n📚 [{r['title']}]:\n{r['content']}\n"
            rag_context += "---\n"

    system_with_rag = SYSTEM_PROMPT + rag_context

    # Monta histórico
    api_messages = [{"role": "system", "content": system_with_rag}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user", "assistant"):
            api_messages.append({"role": m["role"], "content": m["content"]})

    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        api_messages.append({"role": "user", "content": [
            {"type": "text", "text": prompt + rag_context},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
        ]})
        model = VISION_MODEL
    else:
        api_messages.append({"role": "user", "content": prompt})
        model = TEXT_MODEL

    with st.chat_message("assistant"):
        if rag_context:
            st.caption("📚 Consultando base de conhecimento...")
        placeholder = st.empty()
        full_response = ""
        try:
            for chunk in stream_groq(api_messages, GROQ_API_KEY, model):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except requests.HTTPError as e:
            placeholder.error(f"Erro {e.response.status_code}: {e.response.text[:200]}")
            full_response = ""

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
