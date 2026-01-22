import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pytz
import base64
import math

# ================= ARQUIVOS =================
ARQ_AGENDAMENTOS = "agendamentos.json"
ARQ_FUNCIONARIOS = "funcionarios.json"
ARQ_CLIENTES = "clientes.json"  # arquivo para guardar emails de clientes

# ================= FUSO =================
BRASILIA = pytz.timezone("America/Sao_Paulo")

# ================= IMAGEM =================
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("fundo.jpg")

# ================= FUNÇÕES JSON =================
def carregar_json(arq, padrao):
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao

def salvar_json(arq, dados):
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def gerar_datas_disponiveis():
    hoje = datetime.now(BRASILIA)
    datas = []
    for i in range(7):
        dia = hoje + timedelta(days=i)
        if dia.weekday() < 6 and dia.weekday() != 0:
            datas.append(dia)
    return datas

# ================= HORÁRIOS (AJUSTADO) =================
def gerar_horarios_30min():
    horarios = []
    for h in range(9, 21):
        horarios.append(f"{h:02d}:00")
        if h != 20:
            horarios.append(f"{h:02d}:30")
    return horarios

def proximo_bloco_30min(dt):
    minuto = dt.minute
    prox = int(math.ceil(minuto / 30) * 30)
    if prox == 60:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(minute=prox, second=0, microsecond=0)
    return dt

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

st.title("💈 Barbearia Do Coiffer")
st.write("🤖 Seu estilo é nosso compromisso")

# ================= ESTADO =================
if "etapa" not in st.session_state:
    st.session_state.etapa = "login_cliente"

if "idx_pedido_cliente" not in st.session_state:
    st.session_state.idx_pedido_cliente = None

# ================= LOGIN CLIENTE VIA EMAIL =================
if st.session_state.etapa == "login_cliente":
    st.subheader("✉️ Entre com seu e-mail")

    # tenta carregar email salvo no session_state (celular já logado)
    if "email_cliente" not in st.session_state:
        st.session_state.email_cliente = ""

    email = st.text_input("Email", value=st.session_state.email_cliente, placeholder="seu@email.com")

    if st.button("Entrar") and email.strip():
        # salva o email no arquivo de clientes se não existir
        clientes = carregar_json(ARQ_CLIENTES, [])
        if email not in clientes:
            clientes.append(email)
            salvar_json(ARQ_CLIENTES, clientes)

        st.session_state.email_cliente = email
        st.session_state.etapa = "nome_cliente"  # próxima tela para colocar nome para marcação

# ================= NOME CLIENTE PARA MARCAÇÃO =================
elif st.session_state.etapa == "nome_cliente":
    st.subheader("✂️ Digite seu nome para a marcação")
    nome = st.text_input("Nome", placeholder="Ex: João")

    col1, col2 = st.columns(2)

    if col1.button("Continuar") and nome.strip():
        st.session_state.nome_cliente = nome.strip()
        st.session_state.etapa = "funcionario"

    if col2.button("📌 Ver status do pedido"):
        if nome.strip():
            st.session_state.nome_cliente = nome.strip()
            st.session_state.etapa = "status_cliente"
        elif "nome_cliente" in st.session_state and st.session_state.nome_cliente:
            st.session_state.etapa = "status_cliente"
        else:
            st.warning("Digite seu nome")

# ================= STATUS CLIENTE =================
elif st.session_state.etapa == "status_cliente":
    st.subheader("📌 Status do pedido")

    nome = st.session_state.get("nome_cliente", "")
    email = st.session_state.get("email_cliente", "")
    ag = carregar_json(ARQ_AGENDAMENTOS, [])

    # identifica pelo email e nome
    pedidos = [(i, a) for i, a in enumerate(ag) if a.get("email") == email and a.get("nome") == nome]

    if not pedidos:
        st.info("Nenhum pedido encontrado.")
        if st.button("Voltar"):
            st.session_state.etapa = "nome_cliente"
        st.stop()

    idx, p = pedidos[-1]

    st.write(f"💈 Barbeiro: **{p.get('funcionario','')}**")
    st.write(f"📅 Data: **{p.get('data','')}**")
    st.write(f"⏰ Horário: **{p.get('hora','')}**")
    st.write(f"📌 Status: **{p.get('status','').upper()}**")

    if p.get("status") == "sugerido" and p.get("sugestao_hora"):
        st.warning(f"🔁 Sugestão do salão: **{p['sugestao_hora']}**")
        c1, c2 = st.columns(2)

        if c1.button("✅ Aceitar sugestão"):
            ag[idx]["hora"] = p["sugestao_hora"]
            ag[idx]["status"] = "aceito"
            ag[idx]["notificacao_dono"] = "✅ Cliente confirmou o horário"
            ag[idx].pop("sugestao_hora", None)
            salvar_json(ARQ_AGENDAMENTOS, ag)
            st.success("Agendamento confirmado!")
            st.session_state.etapa = "nome_cliente"

        if c2.button("🔄 Escolher outro horário"):
            st.session_state.idx_pedido_cliente = idx
            st.session_state.funcionario = p.get("funcionario")
            st.session_state.etapa = "dia"

    elif p.get("status") == "pendente":
        st.info("⏳ Pedido pendente. Aguarde confirmação do salão.")

    elif p.get("status") == "aceito":
        st.success("✅ Pedido aceito e agendado.")

    if st.button("⬅ Voltar"):
        st.session_state.etapa = "nome_cliente"

# ================= ESCOLHER BARBEIRO =================
elif st.session_state.etapa == "funcionario":
    funcs = carregar_json(ARQ_FUNCIONARIOS, [{"nome": "coiffer"}])
    nomes = [f["nome"] for f in funcs]

    st.subheader("💈 Escolha o barbeiro")
    st.session_state.funcionario = st.selectbox("Barbeiro", nomes)

    if st.button("Próximo"):
        st.session_state.etapa = "dia"

# ================= ESCOLHER DIA =================
elif st.session_state.etapa == "dia":
    datas = gerar_datas_disponiveis()
    opcoes = ["Hoje", "Amanhã"] + [d.strftime("%d/%m/%Y") for d in datas[2:]]

    escolha = st.selectbox("Dia", opcoes)

    if st.button("Próximo"):
        if escolha == "Hoje":
            dia = datetime.now(BRASILIA)
        elif escolha == "Amanhã":
            dia = datetime.now(BRASILIA) + timedelta(days=1)
        else:
            dia = BRASILIA.localize(datetime.strptime(escolha, "%d/%m/%Y"))

        st.session_state.data = dia.strftime("%d/%m/%Y")
        st.session_state.dia_escolhido_raw = escolha
        st.session_state.etapa = "hora"

# ================= ESCOLHER HORÁRIO =================
elif st.session_state.etapa == "hora":
    ag = carregar_json(ARQ_AGENDAMENTOS, [])
    horarios = gerar_horarios_30min()

    ocupados = [
        a["hora"] for a in ag
        if a.get("data") == st.session_state.data
        and a.get("funcionario") == st.session_state.funcionario
        and a.get("status", "aceito") in ["pendente", "aceito", "sugerido"]
    ]

    livres = [h for h in horarios if h not in ocupados]

    if st.session_state.get("dia_escolhido_raw") == "Hoje":
        agora = datetime.now(BRASILIA)
        limite_dt = proximo_bloco_30min(agora)
        limite_str = limite_dt.strftime("%H:%M")
        livres = [h for h in livres if h >= limite_str]

    if not livres:
        st.error("❌ Nenhum horário disponível para esse barbeiro nesse dia.")
        if st.button("Voltar"):
            st.session_state.etapa = "dia"
    else:
        hora = st.selectbox("Horário", livres)

        if st.button("Confirmar"):
            ag = carregar_json(ARQ_AGENDAMENTOS, [])

            if st.session_state.idx_pedido_cliente is not None:
                i = st.session_state.idx_pedido_cliente
                ag[i]["data"] = st.session_state.data
                ag[i]["hora"] = hora
                ag[i]["status"] = "pendente"
                ag[i].pop("sugestao_hora", None)
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.session_state.idx_pedido_cliente = None
                st.success("Pedido reenviado!")
            else:
                ag.append({
                    "nome": st.session_state.nome_cliente,
                    "email": st.session_state.email_cliente,
                    "data": st.session_state.data,
                    "hora": hora,
                    "funcionario": st.session_state.funcionario,
                    "status": "pendente"
                })
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.success("⏳ Pedido enviado! Aguarde confirmação.")

            st.session_state.etapa = "nome_cliente"

# ================= LOGIN DONO =================
elif st.session_state.etapa == "login_dono":
    st.subheader("🔐 Login do Dono")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == "coiffer" and senha == "707060":
            st.session_state.etapa = "painel_dono"
            st.session_state.acao = None
        else:
            st.error("Usuário ou senha inválidos")

# ================= PAINEL DO DONO =================
elif st.session_state.etapa == "painel_dono":
    ag = carregar_json(ARQ_AGENDAMENTOS, [])
    pendentes = [a for a in ag if a.get("status") == "pendente"]

    st.subheader("📊 Painel do Dono")

    c1, c2, c3, c4, c5 = st.columns(5)

    if c1.button("📋 Agendamentos"):
        st.session_state.acao = "ag"

    if c2.button("📌 Meus pedidos (" + str(len(pendentes)) + ")"):
        st.session_state.acao = "ped"

    if c3.button("➕ Adicionar barbeiro"):
        st.session_state.acao = "add"

    if c4.button("❌ Remover barbeiro"):
        st.session_state.acao = "rem"

    if c5.button("🚪 Sair"):
        st.session_state.etapa = "login_cliente"

    st.markdown("---")

    # ===== MEUS PEDIDOS =====
    if st.session_state.acao == "ped":
        for i, a in enumerate(ag):
            if a.get("status") != "pendente":
                continue

            st.write(f"👤 {a['nome']} | 📅 {a['data']} ⏰ {a['hora']} | 💈 {a['funcionario']}")

            col1, col2, col3 = st.columns(3)

            if col1.button("✅ Aceitar", key=f"ok{i}"):
                ag[i]["status"] = "aceito"
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.rerun()

            if col2.button("❌ Recusar", key=f"no{i}"):
                ag.pop(i)
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.rerun()

            novo = col3.text_input("Novo horário", placeholder="Ex: 14:30", key=f"novo{i}")
            if col3.button("🔁 Sugerir", key=f"sug{i}") and novo.strip():
                ag[i]["status"] = "sugerido"
                ag[i]["sugestao_hora"] = novo.strip()
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.rerun()

    # ===== AGENDAMENTOS (ORDENADOS POR HORÁRIO) =====
    elif st.session_state.acao == "ag":
        aceitos = [x for x in ag if x.get("status") == "aceito"]

        # Ordena por hora (HH:MM) antes de mostrar
        aceitos.sort(key=lambda x: datetime.strptime(x["hora"], "%H:%M"))

        for i, a in enumerate(aceitos):
            if a.get("notificacao_dono"):
                st.success(a["notificacao_dono"])
                a.pop("notificacao_dono", None)
                salvar_json(ARQ_AGENDAMENTOS, ag)

            st.write(f"👤 {a['nome']} | 📅 {a['data']} ⏰ {a['hora']} | 💈 {a['funcionario']}")
            if st.button("❌ Cancelar", key=f"can{i}"):
                ag.remove(a)
                salvar_json(ARQ_AGENDAMENTOS, ag)
                st.rerun()

    # ===== ADICIONAR BARBEIRO =====
    elif st.session_state.acao == "add":
        nome = st.text_input("Nome do barbeiro")
        if st.button("Salvar"):
            funcs = carregar_json(ARQ_FUNCIONARIOS, [])
            funcs.append({"nome": nome})
            salvar_json(ARQ_FUNCIONARIOS, funcs)
            st.success("Barbeiro adicionado")

    # ===== REMOVER BARBEIRO =====
    elif st.session_state.acao == "rem":
        funcs = carregar_json(ARQ_FUNCIONARIOS, [])
        nomes = [f["nome"] for f in funcs]
        barb = st.selectbox("Barbeiro", nomes)

        if st.button("Remover"):
            funcs = [f for f in funcs if f["nome"] != barb]
            salvar_json(ARQ_FUNCIONARIOS, funcs)
            st.success("Barbeiro removido")

# ================= SIDEBAR =================
st.sidebar.title("Menu")

if st.sidebar.button("Área do Dono"):
    st.session_state.etapa = "login_dono"

if st.sidebar.button("Cliente"):
    st.session_state.etapa = "login_cliente"
