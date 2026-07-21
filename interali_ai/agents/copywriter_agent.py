"""Agente 2 - O Estrategista de Copywriting (Niche Copywriter).

Skill adaptativa: o tom e as regras de redacao mudam de acordo com
`setor_macro` - inclusive a Regra de Ouro etica de Saude (nunca promete cura
nem usa ganchos sensacionalistas) - ver interali_ai/nichos.py.
"""
from __future__ import annotations

from crewai import Agent

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def build_copywriter_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    regra_de_ouro = f" {cfg.regra_de_ouro}" if cfg.regra_de_ouro else ""
    return Agent(
        role=f"Estrategista de Copywriting (Niche Copywriter) - {cfg.label}",
        goal=(
            "Criar textos de altissima conversao: um gancho (hook) para os "
            "primeiros segundos, uma frase de impacto para o banner e a "
            "legenda completa do Instagram, sempre respeitando a "
            "persona_deduzida e o tom_de_voz_deduzido ja armazenados do "
            f"cliente. Tom exigido pelo setor: {cfg.tom_copywriting}{regra_de_ouro}"
        ),
        backstory=(
            f"Voce e um copywriter especializado em {cfg.label} para redes "
            "sociais, com anos de experiencia gerando ganchos que prendem a "
            "atencao nos primeiros segundos e legendas que convertem, sempre "
            "dentro dos limites eticos e de tom exigidos pelo nicho do cliente."
        ),
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
