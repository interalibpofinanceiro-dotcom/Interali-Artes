"""Orquestracao da equipe de producao (Agentes 1 a 5).

Logica central: ANTES de acionar qualquer agente de criacao, verifica se a
empresa ainda possui creditos disponiveis no mes
(artes_usadas_no_mes < limite_artes_mensal, ou o equivalente para video).
So entao a equipe e executada, na ordem:

    Agente 1 (Diretor de Imagem)  -> trata a foto/video adaptado ao setor
    Agente 2 (Copywriter)         -> gera hook, texto do banner e legenda
    Trava de Etica (setor Saude)  -> cancela a geracao se houver termo proibido
    Agente 3 (Visual Composer)    -> monta o banner com logo/cores/layout do setor
    Agente 4 (Motion Producer)    -> (se objetivo == video) gera o take dinamico
    Agente 5 (QA)                 -> aprova a peca e so entao desconta 1 credito

A trava de etica roda logo apos o Copywriter (Agente 2) e ANTES do Designer
(Agente 3), para cancelar a geracao o mais cedo possivel quando o setor exige
bloqueio (hoje: Saude) - sem gastar credito nem montar banner/video.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.services import company_service, credit_manager, ethics_guard
from interali_ai.services.credit_manager import SaldoInsuficienteError
from interali_ai.tools.bannerbear_tool import simulate_bannerbear
from interali_ai.tools.motion_tool import simulate_motion
from interali_ai.tools.photoroom_tool import simulate_photoroom

Objetivo = Literal["arte", "video"]


class CopyGerado(BaseModel):
    gancho: str = Field(..., description="Gancho (hook) de impacto para os primeiros segundos.")
    desenvolvimento: str = Field(
        ..., description="Corpo do texto que conecta a dor/desejo do publico ao servico oferecido."
    )
    cta: str = Field(..., description="Chamada para acao (CTA) clara e especifica.")
    texto_banner: str = Field(..., description="Frase curta de impacto para estampar no banner.")
    legenda_instagram: str = Field(..., description="Legenda completa para o post do Instagram.")


class VeredictoQA(BaseModel):
    aprovado: bool = Field(..., description="Se a peca final esta legivel, harmoniosa e aprovada.")
    motivo: str = Field(..., description="Justificativa curta da decisao.")


# --------------------------------------------------------------------------- #
# Agente 2 - Copywriter (Niche Copywriter)
# --------------------------------------------------------------------------- #

_PROMPT_COPY = """
Voce esta criando conteudo para a empresa "{nome_comercial}" (setor: {setor_label}, \
sub-nicho: {sub_nicho}).

Persona deduzida do cliente:
\"\"\"{persona}\"\"\"

Tom de voz deduzido do cliente:
\"\"\"{tom_de_voz}\"\"\"

Servicos/produtos que o cliente mais vende (cadastrados uma unica vez no \
onboarding):
\"\"\"{servicos}\"\"\"

Diretrizes eticas e de comunicacao (respeite rigorosamente):
\"\"\"{diretrizes}\"\"\"

Tom exigido pelo setor: {tom_setor}
{regra_de_ouro}

O objetivo do post e: {objetivo}.

Briefing do cliente para ESTA peca especifica (o que ele quer comunicar / que \
tipo de banner deseja):
\"\"\"{briefing_usuario}\"\"\"

A partir do briefing acima (cruzado com os servicos cadastrados e a persona), \
identifique e estruture o texto em:
1. Gancho (Hook): frase que prende a atencao nos primeiros segundos.
2. Desenvolvimento: corpo do texto que conecta a dor/desejo do publico ao \
servico oferecido, com base no briefing do cliente.
3. CTA: chamada para acao clara e especifica (ex: agendar, comprar, chamar no \
whatsapp), coerente com o objetivo do post.
4. Uma frase curta de impacto (derivada do gancho) para estampar no banner.
5. A legenda completa do Instagram, unindo gancho + desenvolvimento + cta.

Respeite rigorosamente a persona, o tom de voz e as diretrizes eticas acima. \
Se o briefing do cliente estiver vazio, baseie-se apenas nos servicos \
cadastrados e na persona.
"""


def _copy_simulado(empresa, objetivo: str, briefing_usuario: str = "") -> CopyGerado:
    cfg = obter_config_setor(empresa.setor_macro)
    nome = empresa.nome_comercial or "seu negocio"
    servicos = empresa.servicos_oferecidos or cfg.label
    briefing = briefing_usuario.strip() if briefing_usuario else ""

    if cfg.valor == "saude":
        gancho = "[Simulado] Voce sabia? Cuidar da sua saude comeca com informacao."
    else:
        gancho = f"[Simulado] Voce nunca viu {nome} assim antes..."

    desenvolvimento = (
        f"[Modo simulado] {nome} atua com {servicos.strip()[:180]}."
        + (f" Sobre o que voce pediu: \"{briefing[:180]}\"." if briefing else "")
        + " Configure OPENAI_API_KEY no .env para um desenvolvimento gerado de verdade."
    )
    cta = (
        "[Simulado] Agende agora e converse com a nossa equipe."
        if cfg.valor == "saude"
        else "[Simulado] Chame no WhatsApp e garanta o seu."
    )
    legenda = (
        f"{gancho}\n\n{desenvolvimento}\n\n{cta} "
        f"#{(nome or 'marca').replace(' ', '')}"
    )
    return CopyGerado(
        gancho=gancho,
        desenvolvimento=desenvolvimento,
        cta=cta,
        texto_banner=f"{nome}: {cfg.label}",
        legenda_instagram=legenda,
    )


def _copy_via_llm(empresa, objetivo: str, briefing_usuario: str = "") -> CopyGerado:
    from crewai import Crew, Process, Task

    from interali_ai.agents.copywriter_agent import build_copywriter_agent

    cfg = obter_config_setor(empresa.setor_macro)
    agente = build_copywriter_agent(empresa.setor_macro)
    task = Task(
        description=_PROMPT_COPY.format(
            nome_comercial=empresa.nome_comercial or "",
            setor_label=cfg.label,
            sub_nicho=empresa.sub_nicho or "",
            persona=empresa.persona_deduzida or "",
            tom_de_voz=empresa.tom_de_voz_deduzido or "",
            servicos=empresa.servicos_oferecidos or "",
            diretrizes=empresa.diretrizes_eticas_nicho or cfg.diretrizes_eticas_padrao,
            tom_setor=cfg.tom_copywriting,
            regra_de_ouro=cfg.regra_de_ouro or "",
            objetivo=objetivo,
            briefing_usuario=briefing_usuario or "",
        ),
        expected_output=(
            "Um objeto estruturado com gancho, desenvolvimento, cta, texto_banner "
            "e legenda_instagram."
        ),
        agent=agente,
        output_pydantic=CopyGerado,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=True)
    crew.kickoff()
    resultado = task.output.pydantic if task.output else None
    return resultado or _copy_simulado(empresa, objetivo, briefing_usuario)


# --------------------------------------------------------------------------- #
# Agente 5 - QA
# --------------------------------------------------------------------------- #

_PROMPT_QA = """
Uma peca grafica final foi gerada para a empresa "{nome_comercial}" (setor: \
{setor_label}), contendo o seguinte texto sobreposto: "{texto_banner}".

Avalie (com base na descricao acima, ja que voce nao pode abrir a imagem
diretamente) se e plausivel que a peca esteja legivel e harmoniosa, e decida
se ela deve ser APROVADA para entrega ao cliente e desconto do credito.
Seja permissivo: reprove apenas se houver um problema claro (ex.: texto vazio).
"""


def _qa_simulado(texto_banner: str) -> VeredictoQA:
    if not texto_banner or not texto_banner.strip():
        return VeredictoQA(aprovado=False, motivo="[Simulado] Texto do banner esta vazio.")
    return VeredictoQA(aprovado=True, motivo="[Simulado] Peca legivel e harmoniosa.")


def _qa_via_llm(empresa, texto_banner: str) -> VeredictoQA:
    from crewai import Crew, Process, Task

    from interali_ai.agents.qa_agent import build_qa_agent

    cfg = obter_config_setor(empresa.setor_macro)
    agente = build_qa_agent(empresa.setor_macro)
    task = Task(
        description=_PROMPT_QA.format(
            nome_comercial=empresa.nome_comercial or "",
            setor_label=cfg.label,
            texto_banner=texto_banner,
        ),
        expected_output="Um objeto estruturado com aprovado (bool) e motivo.",
        agent=agente,
        output_pydantic=VeredictoQA,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=True)
    crew.kickoff()
    resultado = task.output.pydantic if task.output else None
    return resultado or _qa_simulado(texto_banner)


# --------------------------------------------------------------------------- #
# Orquestracao principal
# --------------------------------------------------------------------------- #


def run_production_pipeline(
    empresa_id: str,
    image_path: str,
    objetivo: Objetivo,
    logo_path: Optional[str] = None,
    briefing_usuario: str = "",
) -> dict:
    """Executa a equipe de producao completa, respeitando o limite de creditos
    e a trava de etica do setor do cliente."""
    empresa = company_service.obter_empresa(empresa_id)
    if empresa is None:
        return {"sucesso": False, "erro": f"Empresa '{empresa_id}' nao encontrada."}

    cfg = obter_config_setor(empresa.setor_macro)
    tipo_credito = "video" if objetivo == "video" else "arte"

    # --- Verificacao de limites ANTES de acionar os agentes de criacao ---
    if not credit_manager.possui_creditos(empresa_id, tipo_credito):
        limite = (
            empresa.limite_videos_mensal if tipo_credito == "video" else empresa.limite_artes_mensal
        )
        return {
            "sucesso": False,
            "erro": (
                f"Limite mensal de {tipo_credito}s atingido ({limite}). "
                "Aguarde a renovacao do ciclo ou faca upgrade do plano."
            ),
        }

    cores_hex = empresa.cores_hex or {}

    # Agente 1 - Diretor de Imagem & Estetica (Visual Specialist AI)
    imagem_estilizada = simulate_photoroom(image_path, cores_hex=cores_hex, setor_macro=empresa.setor_macro)

    # Agente 2 - Estrategista de Copywriting (Niche Copywriter)
    copy = (
        _copy_via_llm(empresa, objetivo, briefing_usuario)
        if config.USE_LLM
        else _copy_simulado(empresa, objetivo, briefing_usuario)
    )

    # --- Trava de Etica (Agente 5 / QA Specialist) -----------------------
    # Roda ANTES do Designer/Motion para cancelar a geracao cedo, sem gastar
    # credito, caso o setor exija bloqueio (hoje: Saude) e algum termo
    # proibido pelo conselho de classe seja identificado.
    resultado_etica = ethics_guard.verificar_conformidade_etica(
        cfg,
        [copy.gancho, copy.desenvolvimento, copy.cta, copy.texto_banner, copy.legenda_instagram],
    )
    if not resultado_etica.aprovado:
        return {
            "sucesso": False,
            "bloqueado_etica": True,
            "erro": resultado_etica.mensagem,
            "termos_encontrados": resultado_etica.termos_encontrados,
        }

    # Agente 3 - Designer Grafico (Visual Composer)
    banner_path = simulate_bannerbear(
        imagem_estilizada,
        texto_banner=copy.texto_banner,
        logo_path=logo_path or empresa.logo_url,
        cores_hex=cores_hex,
        setor_macro=empresa.setor_macro,
    )

    # Agente 4 - Editor de Video (Motion Producer AI), somente se objetivo == video
    video_path = None
    if objetivo == "video":
        video_path = simulate_motion(banner_path, setor_macro=empresa.setor_macro)

    # Agente 5 - Inspetor de Qualidade e Etica (QA Specialist)
    veredito = _qa_via_llm(empresa, copy.texto_banner) if config.USE_LLM else _qa_simulado(
        copy.texto_banner
    )

    creditos_restantes = None
    if veredito.aprovado:
        try:
            credit_manager.consumir_credito(empresa_id, tipo_credito)
            creditos_restantes = credit_manager.resumo_creditos(empresa_id)
        except SaldoInsuficienteError as exc:  # corrida entre verificacao e consumo
            return {"sucesso": False, "erro": str(exc)}

    return {
        "sucesso": True,
        "aprovado": veredito.aprovado,
        "motivo_qa": veredito.motivo,
        "aviso_etico": resultado_etica.mensagem if resultado_etica.termos_encontrados else None,
        "imagem_estilizada": imagem_estilizada,
        "banner_path": banner_path,
        "video_path": video_path,
        "gancho": copy.gancho,
        "desenvolvimento": copy.desenvolvimento,
        "cta": copy.cta,
        "texto_banner": copy.texto_banner,
        "legenda_instagram": copy.legenda_instagram,
        "creditos_restantes": creditos_restantes,
    }
