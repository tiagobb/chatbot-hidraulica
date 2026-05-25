import streamlit as st
from google import genai
from google.genai import types
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
- Quando receber um PDF, leia e interprete o documento: manuais, esquemas, datasheets, relatórios de manutenção etc.
- Faça perguntas de diagnóstico para entender melhor o problema antes de dar uma resposta definitiva
- Analise de forma integrada quando o problema envolve múltiplas áreas
- Priorize segurança: sempre alerte sobre riscos antes de procedimentos
- Sugira ferramentas e equipamentos necessários para as intervenções
- Responda sempre em português do Brasil"""

MODEL = "gemini-1.5-flash"

WELCOME_MESSAGE = (
    "Olá! Sou especialista sênior em manutenção industrial com mais de 20 anos de experiência. "
    "Atuo em hidráulica, elétrica, eletrônica, mecânica, automação e muito mais.\n\n"
    "Você pode:\n"
    "- Digitar sua dúvida técnica\n"
    "- Anexar uma **foto** do equipamento, componente ou problema\n"
    "- Anexar um **PDF** (manual, esquema, datasheet)\n\n"
    "Como posso ajudá-lo hoje?"
)

st.set_page_config(
    page_title="Técnico Industrial",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Técnico Especialista — Manutenção Industrial")
st.caption("Hidráulica · Elétrica · Automação · Mecânica · Eletrônica")

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("⚠️ Chave da API não encontrada. Configure a variável `GEMINI_API_KEY`.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image_bytes"):
            st.image(PIL.Image.open(io.BytesIO(message["image_bytes"])), width=380)

with st.sidebar:
    st.header("📎 Anexar arquivo")
    uploaded_file = st.file_uploader(
        "Foto ou PDF",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        help="Anexe uma foto do equipamento ou documento PDF",
    )
    if uploaded_file:
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        else:
            st.success(f"📄 {uploaded_file.name}")
        st.caption("Será enviado com sua próxima mensagem.")

    st.divider()
    st.header("ℹ️ Sobre")
    st.markdown(
        "Assistente especialista em **manutenção industrial**.\n\n"
        "**Áreas de expertise:**\n"
        "- Hidráulica Industrial\n"
        "- Elétrica Industrial\n"
        "- Eletrônica / VFD\n"
        "- Eletromecânica / CNC\n"
        "- Mecânica Industrial\n"
        "- Redes Industriais\n"
        "- Automação / CLP"
    )
    st.divider()
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        st.rerun()

if prompt := st.chat_input("Descreva o problema ou faça sua pergunta técnica..."):
    file_part = None
    image_bytes = None
    display_suffix = ""

    if uploaded_file is not None:
        raw_bytes = uploaded_file.read()
        mime_type = uploaded_file.type

        if mime_type.startswith("image/"):
            image_bytes = raw_bytes
            file_part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
            display_suffix = f"\n\n📷 *[Imagem: {uploaded_file.name}]*"
        elif mime_type == "application/pdf":
            file_part = types.Part.from_bytes(data=raw_bytes, mime_type="application/pdf")
            display_suffix = f"\n\n📄 *[PDF: {uploaded_file.name}]*"

    display_text = prompt + display_suffix
    user_msg = {"role": "user", "content": display_text}
    if image_bytes:
        user_msg["image_bytes"] = image_bytes
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(display_text)
        if image_bytes:
            st.image(PIL.Image.open(io.BytesIO(image_bytes)), width=380)

    # Monta histórico para a API
    contents = []
    messages_for_api = st.session_state.messages[:-1]
    start = next(
        (i for i, m in enumerate(messages_for_api) if m["role"] == "user"),
        len(messages_for_api),
    )
    for m in messages_for_api[start:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

    current_parts = [types.Part(text=prompt)]
    if file_part is not None:
        current_parts.append(file_part)
    contents.append(types.Content(role="user", parts=current_parts))

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        ):
            if chunk.text:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
