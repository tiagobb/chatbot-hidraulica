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
VISION_MODEL = "llama-3.2-11b-vision-preview"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

WELCOME_MESSAGE = (
    "Olá! Sou especialista sênior em manutenção industrial com mais de 20 anos de experiência. "
    "Atuo em hidráulica, elétrica, eletrônica, mecânica, automação e muito mais.\n\n"
    "Você pode:\n"
    "- Digitar sua dúvida técnica\n"
    "- Anexar uma **foto** do equipamento, componente ou problema\n\n"
    "Como posso ajudá-lo hoje?"
)


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
    page_title="Técnico Industrial",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Técnico Especialista — Manutenção Industrial")
st.caption("Hidráulica · Elétrica · Automação · Mecânica · Eletrônica")

api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    st.error("⚠️ Chave da API não encontrada. Configure a variável `GROQ_API_KEY`.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image_bytes"):
            st.image(PIL.Image.open(io.BytesIO(message["image_bytes"])), width=380)

with st.sidebar:
    st.header("📎 Anexar imagem")
    uploaded_file = st.file_uploader(
        "Foto do equipamento",
        type=["jpg", "jpeg", "png", "webp"],
        help="Anexe uma foto do equipamento ou problema",
    )
    if uploaded_file:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
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

    # Monta histórico no formato OpenAI
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state.messages[:-1]:
        if m["role"] in ("user", "assistant"):
            api_messages.append({"role": m["role"], "content": m["content"]})

    # Mensagem atual com ou sem imagem
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
