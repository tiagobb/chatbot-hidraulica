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
When houver CONHECIMENTO RELEVANTE DA BASE DE DADOS no contexto, use-o como referência principal, citando a fonte.
Use linguagem técnica precisa, cite normas (ISO, NBR, NR), ofereça procedimentos passo a passo.
Ao receber imagem, analise detalhadamente. Priorize sempre a segurança.
Responda sempre em português do Brasil."""

WELCOME_MSG = "Olá! Sou seu assistente técnico experiente. Estou aqui para diagnosticar problemas e sugerir soluções rápidas para seu equipamento. Como posso ajudar?"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp, .main { background: #12151C !important; }
.block-container { padding: 1.2rem 1.2rem 5rem 1.2rem !important; max-width: 100% !important; }

/* ═══════════════════════════════
   PAINEL ESQUERDO (coluna)
═══════════════════════════════ */
.left-col {
    background: #1C2030;
    border-radius: 14px;
    border: 1px solid #252B3B;
    padding: 20px 16px;
    min-height: 85vh;
}
.sec-title {
    font-size: .68rem; font-weight: 700; letter-spacing: 2px;
    color: #6C7A96; text-transform: uppercase;
    border-bottom: 1px solid #252B3B; padding-bottom: 10px; margin-bottom: 14px;
    margin-top: 10px;
}
/* Upload box personalizado */
.upload-label {
    font-size: .8rem; font-weight: 600; color: #A2B1CD; margin-bottom: 8px;
}
.upload-label span { font-weight: 400; color: #5A6478; }
[data-testid="stFileUploader"] { background: transparent !important; border: none !important; padding: 0 !important; }
[data-testid="stFileDropzone"] {
    background: #12151C !important; border: 1.5px dashed #2D3448 !important;
    border-radius: 10px !important; padding: 15px 10px !important;
}
[data-testid="stFileDropzone"] * { color: #8A96AD !important; }
[data-testid="stFileDropzone"] button {
    background: #252B3B !important; color: #C8D0E0 !important;
    border: 1px solid #363D55 !important; border-radius: 8px !important;
    font-size: .8rem !important; padding: 6px 16px !important;
    font-weight: 500 !important;
}
/* Lista de Expertise */
.exp-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px; border-radius: 8px; margin-bottom: 6px;
    background: #151824; border: 1px solid #202637;
    font-size: .85rem; color: #C8D0E0;
    transition: all 0.2s;
}
.exp-item:hover {
    background: #1C2132;
    border-color: #2D364F;
}
.exp-item .ei { font-size: 1.1rem; min-width: 22px; text-align: center; }

/* Status Pill */
.status-pill {
    background: #12151C; border: 1px solid #22293A;
    border-radius: 10px; padding: 12px 16px; margin-top: 20px;
}
.status-pill .s-label { font-size: .65rem; color: #5A6478; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
.status-pill .s-val   { font-size: .85rem; color: #2ECC71; font-weight: 600; display: flex; align-items: center; gap: 6px; }

/* ═══════════════════════════════
   HEADER PRINCIPAL
═══════════════════════════════ */
.app-header {
    background: #1C2030;
    border-radius: 14px; padding: 22px 26px; margin-bottom: 18px;
    border: 1px solid #252B3B; box-shadow: 0 6px 20px rgba(0,0,0,.2);
}
.app-header h1 { color: #FFFFFF; font-size: 1.5rem; font-weight: 700; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px; }
.app-header .sub { color: #8A96AD; font-size: .88rem; margin: 0; display: flex; align-items: center; gap: 6px; }

/* ═══════════════════════════════
   BOTÕES DE AÇÃO RÁPIDA (Grid)
═══════════════════════════════ */
.stButton > button {
    background: #1C2030 !important; color: #D8E0F0 !important;
    border: 1px solid #252B3B !important; border-radius: 10px !important;
    font-size: .9rem !important; font-weight: 500 !important;
    padding: 14px 18px !important; transition: all .2s ease-in-out !important;
    width: 100% !important;
    text-align: center !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}
.stButton > button:hover {
    background: #22273B !important; border-color: #3B4766 !important;
    color: #FFFFFF !important; transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(0,0,0,0.25) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ═══════════════════════════════
   CHAT E BALÕES
═══════════════════════════════ */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 8px 0 !important; }
[data-testid="stChatMessage"] > div { background: transparent !important; padding: 0 !important; }

/* Balão do assistente (Robô) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: #1C2030 !important; border-radius: 4px 14px 14px 14px !important;
    padding: 14px 18px !important; border: 1px solid #252B3B !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}
/* Balão do usuário */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg, #1A5C3F, #1E7A52) !important;
    border-radius: 14px 4px 14px 14px !important; padding: 14px 18px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: #DEE5F2 !important; font-size: .95rem !important; line-height: 1.6 !important; margin: 0 !important;
}
[data-testid="stChatMessage"] strong { color: #FFFFFF !important; font-weight: 600; }
[data-testid="stChatMessage"] code { background: #12151C !important; color: #FFD269 !important; padding: 3px 6px !important; border-radius: 4px !important; }

/* Avatar customizado fix */
[data-testid="chatAvatarIcon-assistant"], [data-testid="chatAvatarIcon-user"] {
    background-color: #252B3B !important;
}

/* ═══════════════════════════════
   INPUT DE TEXTO INFERIOR
═══════════════════════════════ */
[data-testid="stBottom"] { background: #12151C !important; border-top: 1px solid #1C2030 !important; padding-bottom: 20px !important; }
[data-testid="stChatInput"] { background: #1C2030 !important; border: 1.5px solid #252B3B !important; border-radius: 12px !important; padding: 4px !important; }
[data-testid="stChatInput"]:focus-within { border-color: #3B4766 !important; box-shadow: 0 0 0 3px rgba(59,71,102,.2) !important; }
[data-testid="stChatInput"] > div { background: #1C2030 !important; }
[data-testid="stChatInput"] textarea { color: #DEE5F2 !important; background: #1C2030 !important; caret-color: #4A7AC8 !important; font-size: 0.95rem !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #5A6478 !important; }

/* Painel expander de Admin */
[data-testid="stExpander"] { background: #1C2030 !important; border: 1px solid #252B3B !important; border-radius: 12px !important; margin-bottom: 10px !important; }
[data-testid="stExpander"] * { color: #D8E0F0 !important; }
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
# LAYOUT DE COLUNAS EQUILIBRADO
# ══════════════════════════════════════════════════════════════════════════════
col_L, col_R = st.columns([1, 3.2], gap="medium")

# ─────────────────────────────────────────────────
# PAINEL ESQUERDO
# ─────────────────────────────────────────────────
with col_L:
    st.markdown('<div class="left-col">', unsafe_allow_html=True)

    # Foto / Upload
    st.markdown('<div class="sec-title">RECURSOS ADICIONAIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-label">ANEXAR FOTO <span>(opcional)</span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("foto", type=["jpg","jpeg","png","webp"],
                                     label_visibility="collapsed", key="foto_up")
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.caption("✅ Será enviada com a próxima mensagem")

    # Expertise — Ajustada com ícones limpos
    st.markdown('<div class="sec-title">ÁREAS DE EXPERTISE</div>', unsafe_allow_html=True)
    for icon, label in [
        ("🔧", "Hidráulica Industrial"),
        ("⚡", "Elétrica Industrial"),
        ("🔌", "Eletrônica / VFD"),
        ("⚙️", "Eletromecânica / CNC"),
        ("🔩", "Mecânica Industrial"),
        ("🤖", "Automação / CLP"),
        ("🌐", "Redes Industriais"),
    ]:
        st.markdown(f'<div class="exp-item"><span class="ei">{icon}</span>{label}</div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
        st.success("✅ Admin Ativo")
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            st.session_state.admin_logged = False; st.rerun()

    if st.button("🗑️ Nova Conversa", use_container_width=True, key="btn_nova"):
        st.session_state.messages = [{"role":"assistant","content":WELCOME_MSG}]
        st.session_state.quick_prompt = ""; st.rerun()

    # Status
    st.markdown(f"""
    <div class="status-pill">
        <div class="s-label">Sistema Operacional</div>
        <div class="s-val">● Online <span style="color:#5A6478; font-weight:normal; margin-left:4px;">({kb_count} frags)</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# COLUNA DIREITA (Área principal do Chat)
# ─────────────────────────────────────────────────
with col_R:

    # Header customizado limpo
    st.markdown("""
    <div class="app-header">
        <h1>🛠️ Técnico Especialista em Manutenção Industrial</h1>
        <p class="sub">🧑‍🔧 Mais de 20 anos de experiência em Hidráulica, Pneumática, Elétrica &amp; Automação</p>
    </div>
    """, unsafe_allow_html=True)

    # Botões de ação rápida com ícones injetados
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

    # Base de conhecimento Admin (Painel de Uploads)
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

    # Renderização do histórico de mensagens
    for msg in st.session_state.messages:
        avatar = "🔧" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image_bytes"):
                st.image(PIL.Image.open(io.BytesIO(msg["image_bytes"])), width=300)

    # Execução das ações rápidas (prompts dos botões)
    if st.session_state.quick_prompt:
        qp = st.session_state.quick_prompt
        st.session_state.quick_prompt = ""
        with st.chat_message("user", avatar="👤"): st.markdown(qp)
        st.session_state.messages.append({"role":"user","content":qp})
        full = do_chat(qp, None, None, sb, kb_count)
        if full: st.session_state.messages.append({"role":"assistant","content":full})

# ── Input de texto principal ──────────────────────────────────────────────────
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
