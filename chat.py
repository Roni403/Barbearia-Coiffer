import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pytz
import base64

# ================= ARQUIVOS =================
ARQ_AGENDAMENTOS = "agendamentos.json"

# ================= FUSO HORÁRIO =================
BRASILIA = pytz.timezone('America/Sao_Paulo')

# ================= IMAGEM LOCAL =================
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("fundo.jpg")

# ================= FUNÇÕES =================
def carregar_agendamentos():
    if os.path.exists(ARQ_AGENDAMENTOS):
        with open(ARQ_AGENDAMENTOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_agendamentos(agendamentos):
    with open(ARQ_AGENDAMENTOS, "w", encoding="utf-8") as f:
        json.dump(agendamentos, f, indent=4, ensure_ascii=False)

def remover_agendamento(index):
    agendamentos = carregar_agendamentos()
    if 0 <= index < len(agendamentos):
        agendamentos.pop(index)
        salvar_agendamentos(agendamentos)

def gerar_datas_disponiveis():
    hoje = datetime.now(BRASILIA)
    datas = []
    for i in range(7):
        dia = hoje + timedelta(days=i)
        if dia.weekday() < 6 and dia.weekday() != 0:
            datas.append(dia)
    return datas

def gerar_horarios(dia):
    horarios = []
    if dia.weekday() == 6:
        inicio = 9
        fim = 13
    else:
        inicio = 9
        fim = 22
    for h in range(inicio, fim):
        horarios.append(f"{h:02d}:00")
        horarios.append(f"{h:02d}:40")
    return horarios

def filtrar_agendamentos_validos(agendamentos):
    agora = datetime.now(BRASILIA)
    ag_validos = []
    for a in agendamentos:
        try:
            hora_parts = a["hora"].split(":")
            dt = datetime.strptime(a["data"], "%d/%m/%Y")
            dt = BRASILIA.localize(
                dt.replace(hour=int(hora_parts[0]), minute=int(hora_parts[1]))
            )
            if agora <= dt + timedelta(minutes=15):
                ag_validos.append(a)
        except:
            ag_validos.append(a)
    return ag_validos

# ================= STREAMLIT CONFIG =================
st.set_page_config(page_title="IA Inteligente - Agendamento", page_icon="🤖")

# ================= FUNDO =================
# (seu código inteiro mantido... apenas a parte de CSS do fundo alterada)

st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/jpg;base64,{img}");
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

div.stButton > button {{
    background-color: #4CAF50;
    color: white;
    height: 50px;
    width: 200px;
    border-radius: 10px;
    font-size: 18px;
}}

.stTextInput>div>div>input {{
    border-radius: 10px;
    height: 35px;
}}
</style>
""", unsafe_allow_html=True)


st.title("🤖 ")

# ================= ESTADO =================
if "etapa" not in st.session_state:
    st.session_state.etapa = "login_cliente"
if "nome_cliente" not in st.session_state:
    st.session_state.nome_cliente = ""
if "dono_logado" not in st.session_state:
    st.session_state.dono_logado = False

# ================= LOGIN CLIENTE =================
if st.session_state.etapa == "login_cliente":
    st.subheader("✂️ Bem-vindo! Para agendamento, digite seu nome:")
    with st.form("form_login_cliente"):
        nome = st.text_input("Seu nome:")
        if st.form_submit_button("Continuar"):
            if nome.strip():
                st.session_state.nome_cliente = nome.strip()
                st.session_state.etapa = "menu_cliente"
            else:
                st.warning("Digite um nome válido!")

# ================= MENU CLIENTE =================
elif st.session_state.etapa == "menu_cliente":
    st.subheader(f"Olá, {st.session_state.nome_cliente}! O que deseja fazer?")
    col1, col2 = st.columns(2)
    if col1.button("✂️ Marcar corte"):
        st.session_state.etapa = "escolher_dia"
    if col2.button("💈 Outros serviços"):
        st.info("Ainda em desenvolvimento!")

# ================= ESCOLHER DIA =================
elif st.session_state.etapa == "escolher_dia":
    st.subheader("Escolha o dia do agendamento:")
    datas = gerar_datas_disponiveis()
    opcoes = ["Hoje", "Amanhã"] + [d.strftime("%d/%m/%Y") for d in datas[2:]]
    dia_escolhido = st.selectbox("Selecione:", opcoes)
    if st.button("Próximo"):
        st.session_state.dia_escolhido = dia_escolhido
        st.session_state.etapa = "escolher_horario"

# ================= ESCOLHER HORÁRIO =================
elif st.session_state.etapa == "escolher_horario":
    st.subheader("Escolha o horário:")
    if st.session_state.dia_escolhido == "Hoje":
        dia = datetime.now(BRASILIA)
    elif st.session_state.dia_escolhido == "Amanhã":
        dia = datetime.now(BRASILIA) + timedelta(days=1)
    else:
        dia = BRASILIA.localize(datetime.strptime(st.session_state.dia_escolhido, "%d/%m/%Y"))

    data_str = dia.strftime("%d/%m/%Y")
    horarios = gerar_horarios(dia)
    ag = carregar_agendamentos()
    ocupados = [a["hora"] for a in ag if a["data"] == data_str]
    livres = [h for h in horarios if h not in ocupados]

    horario = st.selectbox("Horários disponíveis:", livres)
    if st.button("Confirmar agendamento"):
        ag.append({
            "nome": st.session_state.nome_cliente,
            "data": data_str,
            "hora": horario,
            "servico": "Corte"
        })
        salvar_agendamentos(ag)
        st.success("Agendamento confirmado!")
        st.session_state.etapa = "menu_cliente"

# ================= PAINEL DO DONO =================
elif st.session_state.etapa == "painel_dono":
    if not st.session_state.dono_logado:
        st.subheader("🔐 Login do Dono")
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if usuario == "coiffer" and senha == "707060":
                st.session_state.dono_logado = True
            else:
                st.error("Usuário ou senha incorretos!")
    else:
        st.subheader("📋 Agendamentos")
        if st.button("🔄 Atualizar"):
            st.rerun()


        ag = filtrar_agendamentos_validos(carregar_agendamentos())
        ag.sort(key=lambda a: datetime.strptime(a["data"]+" "+a["hora"], "%d/%m/%Y %H:%M"))

        for i, a in enumerate(ag):
            st.markdown(f"""
            <div style="
                background-color: rgba(255,255,255,0.95);
                color: #000;
                padding: 15px;
                border-radius: 12px;
                margin-bottom: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                border-left: 6px solid #4CAF50;
            ">
                <div style="font-size:20px; font-weight:bold;">👤 {a['nome']}</div>
                <div style="font-size:16px;">📅 {a['data']} ⏰ {a['hora']} 💈 {a['servico']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("❌ Cancelar", key=f"c{i}"):
                remover_agendamento(i)
                st.rerun()


# ================= SIDEBAR =================
st.sidebar.title("Navegação")
if st.sidebar.button("Área do Dono"):
    st.session_state.etapa = "painel_dono"
if st.sidebar.button("Menu Cliente"):
    st.session_state.etapa = "menu_cliente"
