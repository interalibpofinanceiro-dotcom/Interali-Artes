"""Agente 0 - O Estrategista de Marca (Branding Strategist).

Usado em dois momentos do Perfil da Marca (nunca num chat - o cliente
preenche o proprio perfil, a IA so assiste):
 1) Sugerir um rascunho de persona/instrucoes de negocio a partir do nicho em
    texto livre digitado pelo cliente (botao "Gerar Sugestao com IA").
 2) Classificar esse nicho num dos perfis visuais/eticos internos e redigir
    diretrizes eticas especificas (ao salvar o perfil).

Skill adaptativa: o foco muda de acordo com o `setor_macro` classificado
(Saude, Beleza, Marketing, Gastronomia ou Generico) - ver interali_ai/nichos.py.
"""
from __future__ import annotations

from crewai import Agent

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def build_onboarding_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Estrategista de Marca (Branding Strategist) - {cfg.label}",
        goal=(
            "Ajudar o cliente a estruturar o Perfil da Marca do proprio "
            f"negocio de {cfg.label} sem exigir nenhuma consultoria humana: "
            "sugerir um rascunho de persona/tom de voz para o cliente revisar, "
            "e classificar o nicho especifico num perfil visual/etico interno "
            f"com diretrizes eticas adequadas. {cfg.onboarding_foco}"
        ),
        backstory=(
            f"Voce e um estrategista de branding especializado no setor de "
            f"{cfg.label}. Ja treinou centenas de pequenos empreendedores do "
            "ramo e sabe redigir, a partir de um nicho descrito livremente "
            "pelo cliente, um rascunho solido de persona/tom de voz e as "
            "diretrizes eticas mais adequadas a esse nicho especifico."
        ),
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
