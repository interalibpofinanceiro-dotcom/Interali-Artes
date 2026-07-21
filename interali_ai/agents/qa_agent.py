"""Agente 5 - O Inspetor de Qualidade e Etica (QA Specialist).

Aprova ou reprova a peca final (legibilidade/harmonia) e, para setores com
`bloqueio_etico=True` (hoje: Saude), a checagem de termos proibidos pelos
conselhos de classe (ver interali_ai/services/ethics_guard.py) e feita em
codigo ANTES deste agente rodar - cancelando a geracao sem gastar credito.
Somente quando a peca e aprovada em ambas as frentes o credito e
efetivamente descontado (ver crews/production_crew.py).
"""
from __future__ import annotations

from crewai import Agent

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def build_qa_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    diretrizes_eticas = cfg.regra_de_ouro or cfg.diretrizes_eticas_padrao or (
        "Nenhuma diretriz etica especifica alem das boas praticas gerais de "
        "publicidade."
    )
    return Agent(
        role=f"Inspetor de Qualidade e Etica (QA Specialist) - {cfg.label}",
        goal=(
            "Garantir que a peca final (banner ou video) esteja perfeitamente "
            "legivel, harmoniosa, alinhada a paleta de cores da marca e em "
            f"conformidade com as diretrizes eticas do setor: {diretrizes_eticas}"
        ),
        backstory=(
            "Voce e um revisor de qualidade minucioso de uma agencia de design, "
            f"focado em legibilidade, contraste, coerencia visual e nas normas "
            f"eticas especificas do setor de {cfg.label}."
        ),
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
