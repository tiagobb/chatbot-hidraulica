import streamlit as st
import requests
import json
import base64
import PIL.Image
import io
import os

SYSTEM_PROMPT = """Você é um especialista técnico sênior em manutenção industrial, com mais de 20 anos de experiência nas seguintes áreas:

- Hidráulica Industrial (circuitos, componentes, óleos, simbologia ISO 1219, servo-hidráulica, hidráulica móvel e estacionária)
- Elétrica Industrial (instalações, motores, quadros de comando, NR-10, NBR 5410, NR-12)
- Eletrônica Industrial (componentes, inversores de frequência VFD, soft-starters, instrumentação)
- Eletromecânica (servo-motores, freios eletromagnéticos, CNC)
- Mecânica Industrial (transmissões, rolamentos, vedações, pneumática)
- Informática Industrial (redes Ethernet/IP, Profibus, Modbus, Profinet, SCADA, HMI, CMMS)
- Automação Industrial (CLPs, Ladder/FBD/ST, PID, Industria 4.0, IIoT)

Comportamento:
- Use linguagem técnica precisa e clara
- Cite normas técnicas relevantes (ISO, NBR, NR, etc.)
- Ofereça exemplos práticos e procedimentos passo a passo quando necessário
- Quando receber uma imagem ou foto, analise-a detalhadamente: identifique componentes, sintomas visíveis, desgastes, vazamentos, conexões incorretas, códigos de erro, esquemas elétricos/hidráulicos etc.
- Faça perguntas de diagnóstico para entender melhor o problema antes de dar uma resposta definitiva
- Analise de forma integrada quando o problema envolve múltiplas áreas
- Priorize segurança: sempre alerte sobre riscos antes de procedimentos
- Sugira ferramentas e equipamentos necessários para as intervenções
- Responda sempre em português do Brasil"""

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

WELCOME_MESSAGE = (
    "Olá! Sou especialista sênior em manutenção industrial com mais de 20 anos de experiência. "
    "Atuo em hidráulica, elétrica, eletrônica, mecânica, automação e muito mais.\n\n"
    "Você pode digitar sua dúvida técnica ou anexar uma **foto** do equipamento para análise.\n\n"
    "Como posso ajudá-lo hoje?"
)

CSS = """
<style>
/* Esconde elementos padrão do Streamlit */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* Fundo geral */
.stApp {
    background-color: #0f1923;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1f2d 0%, #1a2f42 100%);
    border-right: 2px solid #f4a61d;
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f4a61d !important;
}
[data-testid="stSidebar"] hr {
    border-color: #f4a61d44;
}

/* Área principal */
.main .block-container {
    padding-top: 1rem;
    max-width: 900px;
}

/* Header customizado */
.app-header {
    background: linear-gradient(135deg, #0d1f2d 0%, #1a3a5c 100%);
    border-left: 5px solid #f4a61d;
    border-radius: 8px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.app-header .icon { font-size: 2.5rem; }
.app-header h1 {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}
.app-header p {
    margin: 4px 0 0 0;
    font-size: 0.85rem;
    color: #f4a61d;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Mensagens do chat */
[data-testid="stChatMessage"] {
    background-color: #1a2f42 !important;
    border-radius: 10px !important;
    margin-bottom: 10px !important;
    border: 1px solid #1e3a52 !important;
    padding: 12px 16px !important;
    color: #e0e0e0 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #12263a !important;
    border-left: 3px solid #f4a61d !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: #1a2f42 !important;
    border-left: 3px solid #4da8da !important;
}

/* Texto nas mensagens */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] strong {
    color: #dde8f0 !important;
}

/* Input do chat */
[data-testid="stChatInput"] {
    background-color: #1a2f42 !important;
    border: 1px solid #f4a61d !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background-color: #1a2f42 !important;
}

/* Botão de envio */
[data-testid="stChatInputSubmitButton"] {
    background-color: #f4a61d !important;
    border-radius: 6px !important;
}

/* Botão limpar */
.stButton button {
    background-color: #c0392b !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    width: 100% !important;
    font-weight: 600 !important;
}
.stButton button:hover {
    background-color: #e74c3c !important;
}

/* Badge de status */
.status-badge {
    display: inline-block;
    background-color: #27ae60;
    color: white;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 12px;
    margin-top: 6px;
    letter-spacing: 0.5px;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #12263a !important;
    border: 1px dashed #f4a61d !important;
    border-radius: 8px !important;
    padding: 8px !important;
}

/* Divisor */
.section-title {
    color: #f4a61d;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid #f4a61d44;
}
</style>
"""


def stream_groq(api_messages, api_key, model):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    with requests.post(GROQ_URL, headers=headers, json=body, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        content = data["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass


st.set_page_config(
    page_title="Técnico Industrial — Manutenção",
    page_icon="⚙️",
    layout="wide",
)

st.markdown(CSS, unsafe_allow_html=True)

api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    st.error("⚠️ Chave da API não encontrada. Configure a variável `GROQ_API_KEY`.")
    st.stop()

# Header principal
st.markdown("""
<div class="app-header">
    <div class="icon">⚙️</div>
    <div>
        <h1>Técnico Especialista em Manutenção Industrial</h1>
        <p>Hidráulica · Elétrica · Automação · Mecânica · Eletrônica · CLP</p>
        <span class="status-badge">● Online</span>
    </div>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

# Sidebar
with st.sidebar:
    st.markdown('<div class="section-title">📎 Anexar Imagem</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Foto do equipamento",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        st.caption("📌 Será enviado com sua próxima mensagem.")

    st.markdown("---")
    st.markdown('<div class="section-title">🏭 Áreas de Expertise</div>', unsafe_allow_html=True)
    areas = [
        "🔧 Hidráulica Industrial",
        "⚡ Elétrica Industrial",
        "🔌 Eletrônica / VFD",
        "⚙️ Eletromecânica / CNC",
        "🔩 Mecânica Industrial",
        "🌐 Redes Industriais",
        "🤖 Automação / CLP",
    ]
    for area in areas:
        st.markdown(f"<small>{area}</small>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">ℹ️ Informações</div>', unsafe_allow_html=True)
    st.markdown("<small>Modelo: Llama 3.3 70B<br>Provedor: Groq<br>Versão: 2.0</small>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.rerun()

# Histórico do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image_bytes"):
            st.image(PIL.Image.open(io.BytesIO(message["image_bytes"])), width=380)

# Input
if prompt := st.chat_input("Descreva o problema ou faça sua pergunta técnica..."):
    image_bytes = None
    mime_type = None
    display_suffix = ""

    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        display_suffix = f"\n\n📷 *[Imagem: {uploaded_file.name}]*"

    display_text = prompt + display_suffix
    user_msg = {"role": "user", "content": display_text}
    if image_bytes:
        user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(display_text)
        if image_bytes:
            st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=380)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user", "assistant"):
            api_messages.append({"role": m["role"], "content": m["content"]})

    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        api_messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ],
        })
        model = VISION_MODEL
    else:
        api_messages.append({"role": "user", "content": prompt})
        model = TEXT_MODEL

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            for chunk in stream_groq(api_messages, api_key, model):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except requests.HTTPError as e:
            placeholder.error(f"Erro na API: {e.response.status_code} — {e.response.text[:300]}")
            full_response = ""

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
