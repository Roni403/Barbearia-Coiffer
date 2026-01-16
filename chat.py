import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pytz  # Para fuso horário

# ================= FUSO HORÁRIO =================
BRASILIA = pytz.timezone('America/Sao_Paulo')

# ================= ARQUIVOS =================
ARQ_AGENDAMENTOS = "agendamentos.json"

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
        if dia.weekday() < 6 and dia.weekday() != 0:  # Terça a Domingo
            datas.append(dia)
    return datas

def gerar_horarios(dia):
    horarios = []
    if dia.weekday() == 6:  # Domingo
        inicio = 9
        fim = 13
    else:
        inicio = 9
        fim = 22
    for h in range(inicio, fim):
        horarios.append(f"{h:02d}:00")
        horarios.append(f"{h:02d}:40")  # Cada corte dura 40 min
    return horarios

def filtrar_agendamentos_validos(agendamentos):
    """Mantém só os agendamentos cuja hora ainda não passou + 15 minutos"""
    agora = datetime.now(BRASILIA)
    ag_validos = []
    for a in agendamentos:
        try:
            hora_parts = a["hora"].split(":")
            dt = datetime.strptime(a["data"], "%d/%m/%Y")
            # Adiciona hora e fuso horário de Brasília
            dt = BRASILIA.localize(dt.replace(hour=int(hora_parts[0]), minute=int(hora_parts[1]), second=0))
            if agora <= dt + timedelta(minutes=15):
                ag_validos.append(a)
        except:
            ag_validos.append(a)
    return ag_validos

# ================= STREAMLIT CONFIG =================
st.set_page_config(page_title="IA Inteligente - Agendamento", page_icon="🤖")

# ======== FUNDO DA PÁGINA ========
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("fundo.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    div.stButton > button {
        background-color: #4CAF50;  
        color: white;
        height: 50px;
        width: 200px;
        border-radius: 10px;
        font-size: 18px;
        margin: 5px;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
        height: 35px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🤖 Barbearia do Coiffer ")

# ================= ESTADO =================
if "etapa" not in st.session_state:
    st.session_state.etapa = "login_cliente"
if "nome_cliente" not in st.session_state:
    st.session_state.nome_cliente = ""
if "dono_logado" not in st.session_state:
    st.session_state.dono_logado = False

# ================= LOGIN CLIENTE =================
if st.session_state.etapa == "login_cliente":
    st.subheader("💬 Bem-vindo! Para agendamento, digite seu nome:")
    nome = st.text_input("Seu nome:")
    if st.button("Continuar"):
        if nome.strip() != "":
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
        dia = datetime.strptime(st.session_state.dia_escolhido, "%d/%m/%Y")
        dia = BRASILIA.localize(dia)
    data_str = dia.strftime("%d/%m/%Y")
    horarios = gerar_horarios(dia)
    agendamentos = carregar_agendamentos()
    horarios_ocupados = [a["hora"] for a in agendamentos if a["data"] == data_str]
    horarios_disponiveis = [h for h in horarios if h not in horarios_ocupados]
    if not horarios_disponiveis:
        st.warning("Nenhum horário disponível nesse dia.")
    else:
        horario = st.selectbox("Horários disponíveis:", horarios_disponiveis)
        if st.button("Confirmar agendamento"):
            agendamentos.append({
                "nome": st.session_state.nome_cliente,
                "data": data_str,
                "hora": horario,
                "servico": "Corte",
                "visualizado": False
            })
            salvar_agendamentos(agendamentos)
            st.success(f"Agendamento confirmado! {data_str} às {horario}")
            st.session_state.etapa = "menu_cliente"

# ================= ÁREA DO DONO =================
elif st.session_state.etapa == "painel_dono":
    if not st.session_state.dono_logado:
        st.subheader("🔐 Login do Dono")
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            if usuario == "coiffer" and senha == "7070":
                st.session_state.dono_logado = True
                st.success("Login bem-sucedido!")
            else:
                st.error("Usuário ou senha incorretos!")
    else:
        st.subheader("🔐 Área do Dono - Agendamentos")
        agendamentos = carregar_agendamentos()
        agendamentos_validos = filtrar_agendamentos_validos(agendamentos)
        salvar_agendamentos(agendamentos_validos)
        st.markdown(f"**📝 Agendamentos na fila: {len(agendamentos_validos)}**")
        st.markdown("---")
        if not agendamentos_validos:
            st.info("Nenhum agendamento válido no momento.")
        else:
            for i, a in enumerate(agendamentos_validos):
                st.markdown(f"""
                <div style='border:1px solid #ddd; padding:10px; margin-bottom:5px; border-radius:10px; box-shadow: 2px 2px 5px #ccc'>
                    👤 <b>{a.get('nome','Cliente')}</b><br>
                    📅 {a.get('data','-')} ⏰ {a.get('hora','-')} 💈 {a.get('servico','-')}
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1,3])
                if col1.button("❌ Cancelar", key=f"cancel_{i}"):
                    remover_agendamento(i)
                    st.success("Agendamento cancelado com sucesso!")

# ================= BOTÕES DE NAVEGAÇÃO =================
st.sidebar.title("Navegação")
if st.sidebar.button("Área do Dono"):
    st.session_state.etapa = "painel_dono"
if st.sidebar.button("Menu Cliente"):
    st.session_state.etapa = "menu_cliente"
