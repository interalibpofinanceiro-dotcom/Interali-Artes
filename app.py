"""Interali AI - Plataforma SaaS White Label Multi-Nicho.

Setores atendidos: Saude & Bem-Estar, Beleza & Estetica, Marketing & Social
Media e Gastronomia (ver interali_ai/nichos.py).

Quatro telas:
 1) Cadastro com selecao de Setor (selectbox) / Sub-nicho
 2) Chat de Onboarding Automatizado (Agente 0 - Branding Profiler), com
    perguntas adaptadas ao setor escolhido
 3) Dashboard de creditos (saldo mensal de artes/videos)
 4) Upload da foto/video + geracao da peca (Agentes 1-5), com tratamento
    etico e estetico do nicho

Rode com: streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from interali_ai import config
from interali_ai.crews.onboarding_crew import run_onboarding
from interali_ai.crews.production_crew import run_production_pipeline
from interali_ai.database.db import init_db
from interali_ai.nichos import listar_setores, obter_config_setor
from interali_ai.services import company_service, credit_manager

st.set_page_config(page_title="Interali AI", page_icon="✨", layout="wide")

init_db()

# --------------------------------------------------------------------------- #
# Sidebar - selecao / criacao da empresa (cliente White Label)
# --------------------------------------------------------------------------- #

st.sidebar.title("✨ Interali AI")
st.sidebar.caption("Plataforma Multi-Nicho: Saude, Beleza, Marketing e Gastronomia")
if not config.USE_LLM:
    st.sidebar.warning(
        "OPENAI_API_KEY nao configurada. Rodando em **modo simulado** "
        "(sem chamadas reais de LLM). Configure o arquivo .env para usar a IA de verdade."
    )

empresas = company_service.listar_empresas()
opcoes = {f"{e.nome_comercial} ({e.id})": e.id for e in empresas}
opcoes["+ Nova empresa..."] = "__nova__"

escolha = st.sidebar.selectbox("Empresa ativa", list(opcoes.keys()))
empresa_id_selecionada = opcoes[escolha]

if empresa_id_selecionada == "__nova__":
    with st.sidebar.form("nova_empresa_form"):
        st.subheader("Cadastrar nova empresa")
        novo_id = st.text_input("ID da empresa (slug unico)", placeholder="ex: clinica-boa-vida")
        novo_nome = st.text_input("Nome comercial", placeholder="ex: Clinica Boa Vida")

        setores = listar_setores()
        labels_setor = [label for _valor, label in setores]
        indice_setor = st.selectbox(
            "Setor", options=range(len(setores)), format_func=lambda i: labels_setor[i]
        )
        novo_setor_macro = setores[indice_setor][0]
        cfg_preview = obter_config_setor(novo_setor_macro)

        novo_sub_nicho = st.text_input(
            "Sub-nicho especifico",
            placeholder="Ex: " + ", ".join(cfg_preview.sub_nicho_exemplos[:3]),
        )
        cor_primaria = st.color_picker("Cor primaria da marca", "#2d4d4c")
        cor_secundaria = st.color_picker("Cor secundaria da marca", "#FFFFFF")
        logo_upload = st.file_uploader("Logotipo (opcional)", type=["png", "jpg", "jpeg"])
        criar = st.form_submit_button("Criar empresa")

        if criar:
            if not novo_id or not novo_nome:
                st.sidebar.error("Informe ao menos o ID e o Nome comercial.")
            else:
                logo_path = None
                if logo_upload is not None:
                    logo_path = str(config.UPLOADS_DIR / f"{novo_id}_logo_{logo_upload.name}")
                    Path(logo_path).write_bytes(logo_upload.getbuffer())

                company_service.criar_empresa(
                    empresa_id=novo_id,
                    nome_comercial=novo_nome,
                    setor_macro=novo_setor_macro,
                    sub_nicho=novo_sub_nicho,
                    logo_url=logo_path,
                    cores_hex={"primaria": cor_primaria, "secundaria": cor_secundaria},
                )
                st.sidebar.success(f"Empresa '{novo_nome}' criada!")
                st.session_state["empresa_ativa"] = novo_id
                st.rerun()
    st.info("Cadastre uma empresa na barra lateral para comecar.")
    st.stop()
else:
    st.session_state["empresa_ativa"] = empresa_id_selecionada

empresa_id = st.session_state["empresa_ativa"]
empresa = company_service.obter_empresa(empresa_id)
cfg_setor = obter_config_setor(empresa.setor_macro)

st.sidebar.markdown("---")
st.sidebar.caption(f"Setor: {cfg_setor.label}")
st.sidebar.caption(f"Sub-nicho: {empresa.sub_nicho or '-'}")
st.sidebar.caption(f"Onboarding concluido: {'Sim' if empresa.onboarding_completo() else 'Nao'}")
if cfg_setor.bloqueio_etico:
    st.sidebar.info("🛡️ Este setor possui trava etica ativa (normas de conselho de classe).")

# --------------------------------------------------------------------------- #
# Abas principais
# --------------------------------------------------------------------------- #

tela1, tela2, tela3 = st.tabs(
    ["💬 Onboarding Automatizado", "📊 Dashboard de Creditos", "🎨 Gerar Peca"]
)

# --------------------------------------------------------------------------- #
# Tela 1 - Chat de Onboarding Automatizado
# --------------------------------------------------------------------------- #

with tela1:
    st.header("Chat de Onboarding Automatizado")
    st.write(
        f"Setor selecionado: **{cfg_setor.label}**. Conte, com suas palavras, "
        "sobre o seu negocio - inclua **quais servicos voce mais vende**. A IA "
        "(Agente 0) vai deduzir sozinha a persona, o tom de voz, as diretrizes "
        "eticas e os servicos cadastrados da sua marca, adaptados ao seu setor. "
        "Esse cadastro e feito **uma unica vez** (no momento da assinatura) e "
        "sera reaproveitado automaticamente em toda peca gerada dai em diante."
    )

    chave_historico = f"chat_onboarding_{empresa_id}"
    if chave_historico not in st.session_state:
        st.session_state[chave_historico] = [
            {"role": "assistant", "content": cfg_setor.pergunta_inicial}
        ]

    for msg in st.session_state[chave_historico]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    resposta_usuario = st.chat_input("Escreva sua resposta...")
    if resposta_usuario:
        st.session_state[chave_historico].append({"role": "user", "content": resposta_usuario})
        with st.chat_message("user"):
            st.markdown(resposta_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Analisando suas respostas e estruturando o perfil de marca..."):
                perfil = run_onboarding(
                    empresa_id=empresa_id,
                    respostas_brutas=resposta_usuario,
                    setor_macro=empresa.setor_macro or "",
                )
            resumo = (
                "Perfil de marca atualizado com sucesso! ✅\n\n"
                f"**Persona deduzida:**\n{perfil['persona_deduzida']}\n\n"
                f"**Tom de voz deduzido:**\n{perfil['tom_de_voz_deduzido']}\n\n"
                f"**Servicos que voce mais vende:**\n{perfil['servicos_oferecidos']}\n\n"
                f"**Diretrizes eticas do nicho:**\n{perfil['diretrizes_eticas_nicho']}\n\n"
                "_Este cadastro e feito uma unica vez - as proximas pecas vao "
                "reaproveitar esses servicos automaticamente, sem perguntar de novo._"
            )
            st.markdown(resumo)
        st.session_state[chave_historico].append({"role": "assistant", "content": resumo})

# --------------------------------------------------------------------------- #
# Tela 2 - Dashboard de creditos
# --------------------------------------------------------------------------- #

with tela2:
    st.header("Dashboard de Creditos")
    resumo = credit_manager.resumo_creditos(empresa_id)

    col1, col2 = st.columns(2)
    col1.metric(
        "Artes disponiveis este mes",
        f"{resumo['artes_restantes']} / {resumo['artes_limite']}",
    )
    col2.metric(
        "Videos disponiveis este mes",
        f"{resumo['videos_restantes']} / {resumo['videos_limite']}",
    )

    st.info(
        f"Voce ainda tem **{resumo['artes_restantes']} artes** e "
        f"**{resumo['videos_restantes']} videos** este mes."
    )
    st.caption(f"Proxima renovacao do ciclo: {resumo['data_renovacao']}")

    st.progress(
        resumo["artes_restantes"] / resumo["artes_limite"] if resumo["artes_limite"] else 0,
        text="Saldo de artes",
    )
    st.progress(
        resumo["videos_restantes"] / resumo["videos_limite"] if resumo["videos_limite"] else 0,
        text="Saldo de videos",
    )

# --------------------------------------------------------------------------- #
# Tela 3 - Upload da foto + geracao da peca
# --------------------------------------------------------------------------- #

with tela3:
    st.header("Gerar Peca (Banner ou Video)")
    st.caption(f"Tratamento visual e de copy adaptados ao setor: {cfg_setor.label}")

    if not empresa.onboarding_completo():
        st.warning(
            "Esta empresa ainda nao concluiu o Onboarding Automatizado. "
            "Va na aba 'Onboarding Automatizado' antes de gerar pecas para "
            "obter textos alinhados a persona do cliente."
        )

    foto = st.file_uploader("Foto/imagem bruta", type=["png", "jpg", "jpeg"])
    objetivo = st.radio("Objetivo do post", options=["arte", "video"], horizontal=True)
    briefing_usuario = st.text_area(
        "Qual o tipo de banner voce deseja?",
        placeholder=(
            "Descreva com suas palavras o que quer comunicar nesta peca "
            "(ex: 'quero divulgar 20% de desconto na consulta esta semana, "
            "foco em fisioterapia esportiva'). A IA vai usar isso, junto com "
            "os servicos ja cadastrados no onboarding, para montar o gancho, "
            "o desenvolvimento e o CTA do texto."
        ),
        height=120,
    )

    gerar = st.button("✨ Gerar peca com a IA", type="primary", disabled=foto is None)

    if gerar and foto is not None:
        caminho_upload = config.UPLOADS_DIR / foto.name
        caminho_upload.write_bytes(foto.getbuffer())

        with st.spinner("Equipe de agentes trabalhando na sua peca..."):
            resultado = run_production_pipeline(
                empresa_id=empresa_id,
                image_path=str(caminho_upload),
                objetivo=objetivo,
                briefing_usuario=briefing_usuario,
            )

        if resultado.get("bloqueado_etica"):
            st.error(f"🚫 {resultado['erro']}")
            st.caption(
                "A geracao foi cancelada automaticamente pela Trava de Etica "
                "(Agente 5 - QA Specialist) antes de consumir credito."
            )
        elif not resultado["sucesso"]:
            st.error(resultado["erro"])
        elif not resultado["aprovado"]:
            st.error(f"Peca reprovada pelo QA: {resultado['motivo_qa']}")
        else:
            st.success(f"Peca aprovada pelo QA: {resultado['motivo_qa']}")
            if resultado.get("aviso_etico"):
                st.warning(resultado["aviso_etico"])

            col_img, col_texto = st.columns([2, 1])
            with col_img:
                st.image(resultado["banner_path"], caption="Banner final", use_container_width=True)
                if resultado["video_path"]:
                    st.image(resultado["video_path"], caption="Video (GIF simulado)")

            with col_texto:
                st.subheader("Textos gerados (Agente 2)")
                st.markdown(f"**Gancho:** {resultado['gancho']}")
                st.markdown(f"**Desenvolvimento:** {resultado['desenvolvimento']}")
                st.markdown(f"**CTA:** {resultado['cta']}")
                st.markdown(f"**Texto do banner:** {resultado['texto_banner']}")
                st.text_area("Legenda do Instagram", resultado["legenda_instagram"], height=200)

                with open(resultado["banner_path"], "rb") as fh:
                    st.download_button(
                        "⬇️ Baixar banner (PNG)", fh, file_name=Path(resultado["banner_path"]).name
                    )
                if resultado["video_path"]:
                    with open(resultado["video_path"], "rb") as fh:
                        st.download_button(
                            "⬇️ Baixar video (GIF)",
                            fh,
                            file_name=Path(resultado["video_path"]).name,
                        )

            if resultado["creditos_restantes"]:
                st.caption(
                    "Saldo apos esta geracao: "
                    f"{resultado['creditos_restantes']['artes_restantes']} artes / "
                    f"{resultado['creditos_restantes']['videos_restantes']} videos."
                )
