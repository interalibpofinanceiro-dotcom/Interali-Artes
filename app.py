"""Interali AI - Plataforma SaaS Multi-Nicho (nicho em texto livre).

Multi-tenant: cada usuario loga e so enxerga a propria empresa - nao ha
seletor de "empresa ativa". Fluxo:
 1) Login/Cadastro (tela unica, sem usuario logado)
 2) Perfil da Marca (nicho livre, identidade visual, persona com sugestao de
    IA) - obrigatorio antes de gerar pecas, editavel a qualquer momento depois
 3) Dashboard de creditos (saldo mensal de artes/videos)
 4) Gerar Peca: upload proprio OU banco de imagens gratuito (Pexels) + IA
    (Agentes 1-5), com tratamento etico e estetico do nicho

Rode com: streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from interali_ai import config
from interali_ai.crews.onboarding_crew import salvar_perfil_marca, sugerir_persona
from interali_ai.crews.production_crew import run_production_pipeline
from interali_ai.database.db import init_db
from interali_ai.services import auth_service, company_service, credit_manager
from interali_ai.services.auth_service import (
    CredenciaisInvalidasError,
    EmailInvalidoError,
    EmailJaCadastradoError,
)
from interali_ai.tools.stock_photo_tool import BuscaImagensError, baixar_imagem, buscar_imagens

st.set_page_config(page_title="Interali AI", page_icon="✨", layout="wide")

init_db()


def _injetar_css_responsivo() -> None:
    st.markdown(
        """
        <style>
        /* Alvo de toque confortavel para botoes no mobile e desktop */
        div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
            min-height: 2.75rem;
            font-size: 1rem;
            border-radius: 0.6rem;
        }
        @media (max-width: 640px) {
            /* Empilha colunas verticalmente no celular */
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column;
            }
            div[data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
            }
            div[data-testid="stFileUploader"], div[data-testid="stTextInput"],
            div[data-testid="stTextArea"] {
                width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_injetar_css_responsivo()

# --------------------------------------------------------------------------- #
# Autenticacao - gate de login/cadastro (sem usuario logado, para aqui)
# --------------------------------------------------------------------------- #

if "usuario_id" not in st.session_state:
    st.title("✨ Interali AI")
    st.caption("Plataforma SaaS de artes e videos com IA para o seu negocio.")

    aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])

    with aba_entrar:
        with st.form("form_login"):
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", type="primary")

            if entrar:
                try:
                    usuario = auth_service.autenticar(email_login, senha_login)
                    st.session_state["usuario_id"] = usuario.id
                    st.rerun()
                except CredenciaisInvalidasError as exc:
                    st.error(str(exc))

    with aba_criar:
        with st.form("form_cadastro"):
            nome_comercial = st.text_input("Nome comercial", placeholder="ex: Clinica Boa Vida")
            cnpj_cpf = st.text_input("CNPJ ou CPF")
            email_cadastro = st.text_input("E-mail do responsavel")
            senha_cadastro = st.text_input("Senha (minimo 6 caracteres)", type="password")
            criar_conta = st.form_submit_button("Criar conta", type="primary")

            if criar_conta:
                if not nome_comercial or not email_cadastro or len(senha_cadastro) < 6:
                    st.error(
                        "Preencha nome comercial, e-mail e uma senha com pelo menos 6 caracteres."
                    )
                else:
                    try:
                        usuario = auth_service.criar_usuario(
                            email=email_cadastro,
                            senha=senha_cadastro,
                            nome_comercial=nome_comercial,
                            cnpj_cpf=cnpj_cpf,
                        )
                        st.session_state["usuario_id"] = usuario.id
                        st.rerun()
                    except (EmailInvalidoError, EmailJaCadastradoError) as exc:
                        st.error(str(exc))
    st.stop()

empresa = auth_service.obter_empresa_do_usuario(st.session_state["usuario_id"])
if empresa is None:
    st.error("Conta invalida. Faca login novamente.")
    st.session_state.clear()
    st.stop()

empresa_id = empresa.id

st.sidebar.title("✨ Interali AI")
st.sidebar.caption(empresa.nome_comercial or "")
if not config.USE_LLM:
    st.sidebar.warning(
        "OPENAI_API_KEY nao configurada. Rodando em **modo simulado** "
        "(sem chamadas reais de LLM)."
    )
if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()

# --------------------------------------------------------------------------- #
# Badge de creditos - visivel em qualquer tela, no topo do painel
# --------------------------------------------------------------------------- #

st.title("✨ Interali AI")
resumo_topo = credit_manager.resumo_creditos(empresa_id)
col_artes, col_videos = st.columns(2)
col_artes.metric("Artes disponiveis este mes", f"{resumo_topo['artes_restantes']} / {resumo_topo['artes_limite']}")
col_videos.metric("Videos disponiveis este mes", f"{resumo_topo['videos_restantes']} / {resumo_topo['videos_limite']}")
st.divider()


# --------------------------------------------------------------------------- #
# Perfil da Marca (nicho livre + identidade visual + persona)
# --------------------------------------------------------------------------- #

_SUGESTOES_NICHO = (
    "Doceria Gourmet",
    "Psicologia Infantil",
    "Salao de Beleza Afro",
    "Consultoria de Marketing B2B",
    "Petshop",
    "Escritorio de Advocacia",
)


def _renderizar_perfil_marca(empresa) -> None:
    st.header("Perfil da Marca")
    st.write(
        "Preencha uma unica vez: nicho, identidade visual e persona do seu "
        "negocio. A IA usa isso automaticamente em toda peca gerada dai em "
        "diante - voce pode voltar aqui e editar quando quiser."
    )

    st.subheader("Nicho")
    pill_nicho = st.pills(
        "Sugestoes (clique para preencher, ou digite o seu abaixo)",
        _SUGESTOES_NICHO,
        selection_mode="single",
        key=f"pill_nicho_{empresa.id}",
    )
    if pill_nicho:
        st.session_state[f"nicho_input_{empresa.id}"] = pill_nicho
    nicho = st.text_input(
        "Qual o nicho do seu negocio?",
        value=empresa.sub_nicho or "",
        placeholder="Ex: Doceria Gourmet",
        key=f"nicho_input_{empresa.id}",
    )

    st.subheader("Identidade visual")
    cores_atuais = empresa.cores_hex or {}
    logo_upload = st.file_uploader("Logotipo (PNG com fundo transparente)", type=["png"])
    col_c1, col_c2, col_c3 = st.columns(3)
    cor_primaria = col_c1.color_picker("Cor primaria", cores_atuais.get("primaria", "#2d4d4c"))
    cor_secundaria = col_c2.color_picker("Cor secundaria", cores_atuais.get("secundaria", "#FFFFFF"))
    cor_destaque = col_c3.color_picker("Cor de destaque", cores_atuais.get("destaque", "#C9A227"))

    st.subheader("Persona & Instrucoes da IA")
    st.info(
        "Descreva aqui para quem voce vende, o tom de voz desejado e os "
        "diferenciais da sua marca. Quanto mais detalhes colocar, mais "
        "precisa a IA sera."
    )
    if st.button("✨ Gerar Sugestao de Persona com IA", disabled=not nicho.strip()):
        with st.spinner("Gerando sugestao..."):
            st.session_state[f"persona_input_{empresa.id}"] = sugerir_persona(nicho)
    persona = st.text_area(
        "Persona e instrucoes de negocio",
        value=empresa.persona_deduzida or "",
        placeholder=(
            "Ex: Vendo para mulheres de 25 a 45 anos que buscam praticidade. "
            "Tom de voz acolhedor e direto. Meu diferencial e o atendimento "
            "personalizado e os ingredientes artesanais."
        ),
        height=160,
        key=f"persona_input_{empresa.id}",
    )

    if st.button("💾 Salvar Perfil", type="primary", disabled=not (nicho.strip() and persona.strip())):
        logo_url = empresa.logo_url
        if logo_upload is not None:
            logo_url = str(config.UPLOADS_DIR / f"{empresa.id}_logo_{logo_upload.name}")
            Path(logo_url).write_bytes(logo_upload.getbuffer())

        company_service.atualizar_perfil(
            empresa_id=empresa.id,
            logo_url=logo_url,
            cores_hex={
                "primaria": cor_primaria,
                "secundaria": cor_secundaria,
                "destaque": cor_destaque,
            },
        )
        with st.spinner("Salvando perfil e ajustando diretrizes eticas do seu nicho..."):
            salvar_perfil_marca(empresa.id, nicho=nicho, persona=persona)
        st.success("Perfil da Marca salvo!")
        st.rerun()


if not empresa.onboarding_completo():
    st.info(
        "Complete o Perfil da Marca abaixo para comecar a gerar artes e videos."
    )
    _renderizar_perfil_marca(empresa)
    st.stop()

# --------------------------------------------------------------------------- #
# Abas principais (Perfil completo)
# --------------------------------------------------------------------------- #

tela_perfil, tela_dashboard, tela_gerar = st.tabs(
    ["🧬 Perfil da Marca", "📊 Dashboard de Creditos", "🎨 Gerar Peca"]
)

with tela_perfil:
    _renderizar_perfil_marca(empresa)

# --------------------------------------------------------------------------- #
# Dashboard de creditos
# --------------------------------------------------------------------------- #

with tela_dashboard:
    st.header("Dashboard de Creditos")
    resumo = credit_manager.resumo_creditos(empresa_id)

    col1, col2 = st.columns(2)
    col1.metric("Artes disponiveis este mes", f"{resumo['artes_restantes']} / {resumo['artes_limite']}")
    col2.metric("Videos disponiveis este mes", f"{resumo['videos_restantes']} / {resumo['videos_limite']}")

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
# Gerar Peca - upload proprio OU banco de imagens gratuito + video
# --------------------------------------------------------------------------- #

with tela_gerar:
    st.header("Gerar Peca (Banner ou Video)")
    st.caption(f"Tratamento visual e de copy adaptados ao nicho: {empresa.sub_nicho}")

    objetivo = st.radio("Objetivo do post", options=["arte", "video"], horizontal=True)

    foto = None
    video_bruto = None
    caminho_banco_imagens = None

    if objetivo == "arte":
        opcoes_origem = ["📤 Enviar minha foto"]
        if config.USE_BANCO_IMAGENS:
            opcoes_origem.append("🖼️ Banco de imagens gratuito")
        origem_imagem = st.radio("Origem da imagem", opcoes_origem, horizontal=True)
        if not config.USE_BANCO_IMAGENS:
            st.caption(
                "Banco de imagens desabilitado - configure PEXELS_API_KEY no "
                ".env para habilitar a busca de fotos gratuitas."
            )

        if origem_imagem == "📤 Enviar minha foto":
            foto = st.file_uploader("Foto/imagem bruta", type=["png", "jpg", "jpeg"])
        else:
            busca = st.text_input(
                "Buscar fotos gratuitas",
                placeholder="Ex: cabelo hidratado, pizza saindo do forno, consultorio acolhedor",
            )
            if st.button("🔎 Buscar fotos"):
                try:
                    st.session_state["resultados_banco_imagens"] = buscar_imagens(busca)
                except BuscaImagensError as exc:
                    st.error(str(exc))
                    st.session_state["resultados_banco_imagens"] = []
                except Exception:
                    st.error("Nao foi possivel buscar fotos agora. Tente novamente.")
                    st.session_state["resultados_banco_imagens"] = []

            resultados = st.session_state.get("resultados_banco_imagens", [])
            if resultados:
                colunas_galeria = st.columns(3)
                for indice, foto_banco in enumerate(resultados):
                    with colunas_galeria[indice % 3]:
                        st.image(foto_banco["thumbnail_url"], use_container_width=True)
                        st.caption(f"Foto: {foto_banco['fotografo']}")
                        if st.button("Selecionar", key=f"selecionar_{foto_banco['id']}"):
                            st.session_state["caminho_banco_imagens"] = baixar_imagem(
                                foto_banco["url_original"]
                            )
                            st.success("Imagem selecionada!")

            caminho_banco_imagens = st.session_state.get("caminho_banco_imagens")
            if caminho_banco_imagens:
                st.image(caminho_banco_imagens, caption="Imagem selecionada", width=220)
    else:
        video_bruto = st.file_uploader("Seu video (MP4, MOV ou WEBM)", type=["mp4", "mov", "webm"])
        st.caption(
            f"Envie um video de ate {config.DURACAO_MAXIMA_VIDEO_SEGUNDOS}s "
            "(formato Reels/TikTok/Shorts). Se for mais longo, a IA corta "
            "automaticamente nesse limite. A IA enquadra em 9:16 e aplica a "
            "barra de marca (logo + cores + nome) na base do video."
        )

    briefing_usuario = st.text_area(
        "Qual o tipo de banner voce deseja?",
        placeholder=(
            "Descreva com suas palavras o que quer comunicar nesta peca "
            "(ex: 'quero avisar que temos vaga para promocao de hidratacao "
            "nesta terca'). A IA vai usar isso, junto com a persona "
            "cadastrada, para montar o gancho, o desenvolvimento e o CTA."
        ),
        height=120,
    )

    if objetivo == "arte":
        arquivo_pronto = foto is not None or caminho_banco_imagens is not None
    else:
        arquivo_pronto = video_bruto is not None

    gerar = st.button("✨ Gerar peca com a IA", type="primary", disabled=not arquivo_pronto)

    if gerar and arquivo_pronto:
        caminho_imagem = None
        caminho_video = None
        if objetivo == "arte":
            if caminho_banco_imagens:
                caminho_imagem = caminho_banco_imagens
            else:
                caminho_imagem = str(config.UPLOADS_DIR / foto.name)
                Path(caminho_imagem).write_bytes(foto.getbuffer())
        else:
            caminho_video = config.UPLOADS_DIR / video_bruto.name
            caminho_video.write_bytes(video_bruto.getbuffer())

        with st.spinner("Equipe de agentes trabalhando na sua peca..."):
            resultado = run_production_pipeline(
                empresa_id=empresa_id,
                objetivo=objetivo,
                image_path=caminho_imagem,
                video_path_bruto=str(caminho_video) if caminho_video else None,
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
                if resultado["banner_path"]:
                    st.image(resultado["banner_path"], caption="Banner final", use_container_width=True)
                if resultado["video_path"]:
                    st.video(resultado["video_path"])

            with col_texto:
                st.subheader("Textos gerados (Agente 2)")
                st.markdown(f"**Gancho:** {resultado['gancho']}")
                st.markdown(f"**Desenvolvimento:** {resultado['desenvolvimento']}")
                st.markdown(f"**CTA:** {resultado['cta']}")
                st.markdown(f"**Texto do banner:** {resultado['texto_banner']}")
                st.text_area("Legenda do Instagram", resultado["legenda_instagram"], height=200)

                if resultado["banner_path"]:
                    with open(resultado["banner_path"], "rb") as fh:
                        st.download_button(
                            "⬇️ Baixar banner (PNG)", fh, file_name=Path(resultado["banner_path"]).name
                        )
                if resultado["video_path"]:
                    with open(resultado["video_path"], "rb") as fh:
                        st.download_button(
                            "⬇️ Baixar video (MP4)",
                            fh,
                            file_name=Path(resultado["video_path"]).name,
                        )

            if resultado["creditos_restantes"]:
                st.caption(
                    "Saldo apos esta geracao: "
                    f"{resultado['creditos_restantes']['artes_restantes']} artes / "
                    f"{resultado['creditos_restantes']['videos_restantes']} videos."
                )
