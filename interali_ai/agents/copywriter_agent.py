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
            "A partir do briefing do cliente (o que ele quer comunicar nesta "
            "peca especifica) e da persona/instrucoes de negocio cadastradas "
            "no Perfil da Marca, identificar e estruturar o texto em tres "
            "partes classicas de copywriting: 1) Gancho (hook) que prende "
            "atencao nos primeiros segundos; 2) Desenvolvimento, que conecta a "
            "dor/desejo do publico ao servico oferecido; 3) CTA (chamada para "
            "acao) clara e especifica. Sempre respeitando a persona cadastrada "
            f"pelo cliente. Tom exigido pelo setor: {cfg.tom_copywriting}{regra_de_ouro}"
        ),
        backstory=(
            f"Voce e um copywriter especializado em {cfg.label} para redes "
            "sociais, com anos de experiencia estruturando textos no formato "
            "gancho-desenvolvimento-CTA que prendem a atencao e convertem, "
            "sempre dentro dos limites eticos e de tom exigidos pelo nicho do "
            "cliente."
        ),
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
