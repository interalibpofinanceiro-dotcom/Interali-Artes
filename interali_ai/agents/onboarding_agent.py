"""Agente 0 - O Estrategista de Onboarding (Branding Profiler).

Entrevista o cliente no primeiro acesso (chat de boas-vindas) e estrutura,
de forma 100% autonoma, o manual de marca: persona, tom de voz e diretrizes
eticas do nicho. Nenhuma consultoria humana e necessaria (Automacao Total).

Skill adaptativa: o foco da entrevista muda de acordo com `setor_macro`
(Saude, Beleza, Marketing ou Gastronomia) - ver interali_ai/nichos.py.
"""
from __future__ import annotations

from crewai import Agent

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def build_onboarding_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Estrategista de Onboarding (Branding Profiler) - {cfg.label}",
        goal=(
            "Transformar respostas brutas e informais do cliente sobre o proprio "
            f"negocio de {cfg.label} em um perfil de marca estruturado e "
            "cientifico, sem exigir nenhuma consultoria humana - incluindo, "
            "obrigatoriamente, a lista objetiva dos servicos/produtos que o "
            "cliente mais vende ou quer divulgar (cadastro feito uma unica vez, "
            "no momento da assinatura, reaproveitado em toda geracao futura de "
            f"peca). {cfg.onboarding_foco}"
        ),
        backstory=(
            f"Voce e um estrategista de branding especializado no setor de "
            f"{cfg.label}. Ja treinou centenas de pequenos empreendedores do "
            "ramo e sabe extrair, de uma unica descricao informal, a persona "
            "demografica/psicografica, o tom de voz, as diretrizes eticas e os "
            "servicos/produtos mais vendidos, todos adequados ao nicho "
            "especifico do cliente."
        ),
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
