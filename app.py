import streamlit as st
import google.generativeai as genai
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
- Faça perguntas de diagnóstico para entender melhor o problema antes de dar uma resposta definitiva
- Analise de forma integrada quando o problema envolve múltiplas áreas
- Priorize segurança: sempre alerte sobre riscos antes de procedimentos
- Sugira ferramentas e equipamentos necessários para as intervenções
- Responda sempre em português do Brasil"""

MODEL = "gemini-2.0-flash"

WELCOME_MESSAGE = (
    "Olá! Sou especialista sênior em manutenção industrial com mais de 20 anos de experiência. "
    "Atuo em hidráulica, elétrica, eletrônica, mecânica, automação e muito mais.\n\n"
    "Como posso ajudá-lo hoje? Descreva o equipamento, o sintoma e qualquer informação relevante "
    "sobre o problema que está enfrentando."
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
    st.info(
        "**Como configurar localmente (PowerShell):**\n"
        "```powershell\n"
        "$env:GEMINI_API_KEY = 'sua-chave-aqui'\n"
        "streamlit run app.py\n"
        "```\n\n"
        "Obtenha sua chave gratuita em: https://aistudio.google.com"
    )
    st.stop()

genai.configure(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Descreva o problema ou faça sua pergunta técnica..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Monta histórico para o Gemini (ignora mensagens de assistente no início)
    gemini_history = []
    messages_for_api = st.session_state.messages[:-1]  # sem o último (será enviado como prompt)
    start = next(
        (i for i, m in enumerate(messages_for_api) if m["role"] == "user"),
        len(messages_for_api),
    )
    for m in messages_for_api[start:]:
        role = "user" if m["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [m["content"]]})

    model = genai.GenerativeModel(MODEL, system_instruction=SYSTEM_PROMPT)
    chat = model.start_chat(history=gemini_history)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        response = chat.send_message(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

with st.sidebar:
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
