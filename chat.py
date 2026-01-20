import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pytz
import base64

# ================= ARQUIVOS =================
ARQ_AGENDAMENTOS = "agendamentos.json"
ARQ_FUNCIONARIOS = "funcionarios.json"

# ================= FUSO =================
BRASILIA = pytz.timezone("America/Sao_Paulo")

# ================= IMAGEM =================
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("fundo.jpg")

# ================= FUNÇÕES =================
def carregar_json(arq, padrao):
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao

def salvar_json(arq, dados):
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def remover_agendamento(index):
    ag = carregar_json(ARQ_AGENDAMENTOS, [])
    if 0 <= index < len(ag):
        ag.pop(index)
        salvar_json(ARQ_AGENDAMENTOS, ag)

def gerar_datas_disponiveis():
    hoje = datetime.now(BRASILIA)
    datas = []
    for i in range(7):
        dia = hoje + timedelta(days=i)
        if dia.weekday() < 6 and dia.weekday() != 0:
            datas.append(dia)
    return datas

def gerar_horarios(dia):
    inicio, fim = (9, 13) if dia.weekday() == 6 else (9, 22)
    horarios = []
    for h in range(inicio, fim):
        horarios.append(f"{h:02d}:00")
        horarios.append(f"{h:02d}:40")
    return horarios

def filtrar_agendamentos_validos(ag):
    agora = datetime.now(BRASILIA)
    validos = []
    for a in ag:
        try:
            dt = BRASILIA.localize(
                datetime.strptime(a["data"] + " " + a["hora"], "%d/%m/%Y %H:%M")
            )
            if agora <= dt + timedelta(minutes=15):
                validos.append(a)
        except:
            validos.append(a)
    return validos

# ================= CONFIG =================
st.set_page_config(page_title="Barbearia IA", page_icon="💈")

st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/jpg;base64,{img}");
    background-size: cover;
}}
</style>
""", unsafe_allow_html=True)
st.title(" Barbearia Do Coifeer")
st.title("🤖 Seu estilo é nosso compromisso")

# ================= ESTADO =================
if "etapa" not in st.session_state:
    st.session_state.etapa = "login_cliente"

# ================= LOGIN CLIENTE =================
if st.session_state.etapa == "login_cliente":
    st.subheader("✂️ Digite seu nome")
    nome = st.text_input("Nome")

    if st.button("Continuar") and nome.strip():
        st.session_state.nome_cliente = nome.strip()
        st.session_state.etapa = "escolher_funcionario"

# ================= ESCOLHER BARBEIRO =================
elif st.session_state.etapa == "escolher_funcionario":
    funcs = carregar_json(ARQ_FUNCIONARIOS, [{"nome": "coiffer"}])
    nomes = [f["nome"] for f in funcs]

    st.subheader("💈 Escolha o barbeiro")
    func = st.selectbox("Barbeiro", nomes)

    if st.button("Próximo"):
        st.session_state.funcionario = func
        st.session_state.etapa = "escolher_dia"

# ================= ESCOLHER DIA =================
elif st.session_state.etapa == "escolher_dia":
    datas = gerar_datas_disponiveis()
    opcoes = ["Hoje", "Amanhã"] + [d.strftime("%d/%m/%Y") for d in datas[2:]]

    dia = st.selectbox("Dia", opcoes)

    if st.button("Próximo"):
        st.session_state.dia = dia
        st.session_state.etapa = "escolher_horario"

# ================= ESCOLHER HORÁRIO =================
elif st.session_state.etapa == "escolher_horario":
    if st.session_state.dia == "Hoje":
        dia = datetime.now(BRASILIA)
    elif st.session_state.dia == "Amanhã":
        dia = datetime.now(BRASILIA) + timedelta(days=1)
    else:
        dia = BRASILIA.localize(datetime.strptime(st.session_state.dia, "%d/%m/%Y"))

    data_str = dia.strftime("%d/%m/%Y")
    horarios = gerar_horarios(dia)

    ag = carregar_json(ARQ_AGENDAMENTOS, [])
    ocupados = [
        a["hora"] for a in ag
        if a["data"] == data_str and a["funcionario"] == st.session_state.funcionario
    ]

    livres = [h for h in horarios if h not in ocupados]

    hora = st.selectbox("Horário", livres)

    if st.button("Confirmar"):
        ag.append({
            "nome": st.session_state.nome_cliente,
            "data": data_str,
            "hora": hora,
            "servico": "Corte",
            "funcionario": st.session_state.funcionario
        })
        salvar_json(ARQ_AGENDAMENTOS, ag)
        st.success("Agendamento confirmado!")
        st.session_state.etapa = "login_cliente"

# ================= LOGIN DONO =================
elif st.session_state.etapa == "login_dono":
    st.subheader("🔐 Login do Dono")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == "coiffer" and senha == "707060":
            st.session_state.etapa = "painel_dono"
        else:
            st.error("Usuário ou senha inválidos")

# ================= PAINEL DO DONO =================
elif st.session_state.etapa == "painel_dono":

    if "acao_painel" not in st.session_state:
        st.session_state.acao_painel = None

    st.subheader("📊 Painel do Dono")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("📋 Agendamentos"):
        st.session_state.acao_painel = "ag"

    if col2.button("➕ Adicionar barbeiro"):
        st.session_state.acao_painel = "add"

    if col3.button("❌ Remover barbeiro"):
        st.session_state.acao_painel = "rem"

    if col4.button("🚪 Sair"):
        st.session_state.etapa = "login_cliente"
        st.session_state.acao_painel = None

    st.markdown("---")

    # AGENDAMENTOS + CANCELAR (RESTAURADO)
    if st.session_state.acao_painel == "ag":
        ag = filtrar_agendamentos_validos(carregar_json(ARQ_AGENDAMENTOS, []))

        for i, a in enumerate(ag):
            st.markdown(
                f"👤 {a['nome']} | 💈 {a['funcionario']} | 📅 {a['data']} ⏰ {a['hora']}"
            )
            if st.button("❌ Cancelar", key=f"c{i}"):
                remover_agendamento(i)
                st.rerun()

    # ADICIONAR BARBEIRO
    elif st.session_state.acao_painel == "add":
        nome = st.text_input("Nome do barbeiro")
        if st.button("Salvar"):
            if nome.strip():
                funcs = carregar_json(ARQ_FUNCIONARIOS, [])
                funcs.append({"nome": nome.strip()})
                salvar_json(ARQ_FUNCIONARIOS, funcs)
                st.success("Barbeiro adicionado")
                st.session_state.acao_painel = None

    # REMOVER BARBEIRO
    elif st.session_state.acao_painel == "rem":
        funcs = carregar_json(ARQ_FUNCIONARIOS, [])
        nomes = [f["nome"] for f in funcs]

        barb = st.selectbox("Escolha o barbeiro", nomes)
        if st.button("Remover"):
            funcs = [f for f in funcs if f["nome"] != barb]
            salvar_json(ARQ_FUNCIONARIOS, funcs)
            st.success("Barbeiro removido")
            st.session_state.acao_painel = None

# ================= SIDEBAR =================
st.sidebar.title("Menu")
if st.sidebar.button("Área do Dono"):
    st.session_state.etapa = "login_dono"

if st.sidebar.button("Cliente"):
    st.session_state.etapa = "login_cliente"
