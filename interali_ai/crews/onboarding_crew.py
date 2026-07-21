"""Agente 0 (Estrategista de Marca): sugestao de persona e classificacao
automatica do nicho para o Perfil da Marca.

Substitui o antigo chat de onboarding: o cliente preenche nicho + persona em
texto livre diretamente no Perfil da Marca, com um botao opcional de
sugestao por IA para a persona. Ao salvar, o nicho e classificado
automaticamente num perfil visual/etico interno (`setor_macro`) e diretrizes
eticas sao geradas - o cliente nunca escolhe nem edita essa classificacao
diretamente, preservando a Trava de Etica.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from interali_ai import config
from interali_ai.nichos import classificar_nicho, obter_config_setor
from interali_ai.services import company_service

# --------------------------------------------------------------------------- #
# Sugestao de persona (botao "Gerar Sugestao de Persona com IA")
# --------------------------------------------------------------------------- #


class SugestaoPersona(BaseModel):
    persona_sugerida: str = Field(
        ..., description="Rascunho de persona/instrucoes de negocio para o cliente revisar."
    )


def _persona_sugerida_simulada(nicho: str) -> str:
    cfg = obter_config_setor(classificar_nicho(nicho))
    return (
        f"[Modo simulado] Publico-alvo tipico de \"{nicho.strip()}\": pessoas "
        f"interessadas em {cfg.label.lower()}, que valorizam confianca e "
        "clareza na comunicacao. Tom de voz sugerido: proximo, direto e "
        f"consistente com o posicionamento do negocio. {cfg.onboarding_foco} "
        "Configure OPENAI_API_KEY no .env para uma sugestao gerada de verdade "
        "pela IA - revise e ajuste este texto antes de salvar."
    )


def _persona_sugerida_via_llm(nicho: str) -> str:
    from crewai import Crew, Process, Task

    from interali_ai.agents.onboarding_agent import build_onboarding_agent

    setor_heuristico = classificar_nicho(nicho)
    cfg = obter_config_setor(setor_heuristico)
    agente = build_onboarding_agent(setor_heuristico)
    task = Task(
        description=(
            f"O cliente atua no nicho \"{nicho}\". Escreva um rascunho de "
            "persona e instrucoes de negocio (para quem ele vende, tom de voz "
            "desejado e diferenciais tipicos desse nicho) para ele revisar e "
            f"ajustar antes de salvar. Foco esperado: {cfg.onboarding_foco}"
        ),
        expected_output="Um objeto estruturado com persona_sugerida.",
        agent=agente,
        output_pydantic=SugestaoPersona,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=True)
    crew.kickoff()
    resultado = task.output.pydantic if task.output else None
    return resultado.persona_sugerida if resultado else _persona_sugerida_simulada(nicho)


def sugerir_persona(nicho: str) -> str:
    """Usado pelo botao "Gerar Sugestao de Persona com IA" no Perfil da Marca."""
    if not nicho or not nicho.strip():
        return ""
    return _persona_sugerida_via_llm(nicho) if config.USE_LLM else _persona_sugerida_simulada(nicho)


# --------------------------------------------------------------------------- #
# Classificacao automatica do nicho (ao salvar o Perfil da Marca)
# --------------------------------------------------------------------------- #


class ClassificacaoNicho(BaseModel):
    setor_mais_proximo: str = Field(
        ..., description="Uma destas chaves: saude, beleza, marketing, gastronomia ou generico."
    )
    diretrizes_eticas_nicho: str = Field(
        ..., description="Diretrizes eticas e de comunicacao especificas para este nicho exato."
    )


def _classificar_via_llm(nicho: str) -> ClassificacaoNicho:
    from crewai import Crew, Process, Task

    from interali_ai.agents.onboarding_agent import build_onboarding_agent

    setor_heuristico = classificar_nicho(nicho)
    agente = build_onboarding_agent(setor_heuristico)
    task = Task(
        description=(
            f"O cliente atua no nicho \"{nicho}\". Escolha, dentre 'saude', "
            "'beleza', 'marketing', 'gastronomia' ou 'generico', qual perfil "
            "visual/etico mais se aproxima deste nicho especifico (o palpite "
            f"inicial por palavra-chave foi '{setor_heuristico}' - use-o se "
            "fizer sentido, ou escolha outro se for mais preciso). Em seguida, "
            "escreva diretrizes eticas e de comunicacao especificas para este "
            "nicho exato (o que pode e o que NAO pode ser dito) - considere "
            "normas de conselho de classe se for uma profissao regulamentada "
            "(saude, direito, financas etc.)."
        ),
        expected_output="Um objeto estruturado com setor_mais_proximo e diretrizes_eticas_nicho.",
        agent=agente,
        output_pydantic=ClassificacaoNicho,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=True)
    crew.kickoff()
    resultado = task.output.pydantic if task.output else None
    if resultado:
        return resultado
    return _classificacao_simulada(nicho)


def _classificacao_simulada(nicho: str) -> ClassificacaoNicho:
    setor_macro = classificar_nicho(nicho)
    cfg = obter_config_setor(setor_macro)
    diretrizes = cfg.regra_de_ouro or cfg.diretrizes_eticas_padrao or (
        "Evite promessas irreais, comparacoes agressivas com concorrentes e "
        "linguagem sensacionalista; priorize clareza e honestidade."
    )
    return ClassificacaoNicho(setor_mais_proximo=setor_macro, diretrizes_eticas_nicho=diretrizes)


def salvar_perfil_marca(empresa_id: str, nicho: str, persona: str) -> dict:
    """Classifica o nicho (setor interno + diretrizes eticas) e persiste o
    Perfil da Marca inteiro. Chamado pelo botao "Salvar Perfil"."""
    classificacao = (
        _classificar_via_llm(nicho) if config.USE_LLM else _classificacao_simulada(nicho)
    )

    empresa = company_service.atualizar_perfil(
        empresa_id=empresa_id,
        sub_nicho=nicho,
        persona_deduzida=persona,
        setor_macro=classificacao.setor_mais_proximo,
        diretrizes_eticas_nicho=classificacao.diretrizes_eticas_nicho,
    )
    return {
        "setor_macro": empresa.setor_macro,
        "diretrizes_eticas_nicho": empresa.diretrizes_eticas_nicho,
    }
