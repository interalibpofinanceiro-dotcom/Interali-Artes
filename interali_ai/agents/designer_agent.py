"""Agente 3 - O Designer Grafico (Visual Composer).

Monta o banner aplicando o logotipo, o texto do Agente 2 (Copywriter) e as
cores_hex do cliente (simulando a API BannerBear), com o layout adaptado ao
setor - ver interali_ai/nichos.py.

Assim como o Agente 1, este passo e deterministico e por isso e chamado
diretamente por crews/production_crew.py via `simulate_bannerbear`. O Agent
CrewAI abaixo fica disponivel para um pipeline 100% orientado a tool-calling.
"""
from __future__ import annotations

from crewai import Agent
from crewai.tools import tool

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.tools.bannerbear_tool import simulate_bannerbear


@tool("Simular BannerBear")
def bannerbear_tool(image_path: str, texto_banner: str, setor_macro: str = "") -> str:
    """Monta o banner final aplicando logotipo, cores da marca, o texto de
    impacto e o layout do setor sobre a imagem processada. Recebe o caminho
    da imagem, o texto do banner e o setor_macro, devolve o caminho do
    banner final."""
    return simulate_bannerbear(image_path, texto_banner, setor_macro=setor_macro)


def build_designer_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Designer Grafico (Visual Composer) - {cfg.label}",
        goal=(
            "Montar o banner final aplicando logotipo, texto de impacto e a "
            "paleta de cores da marca do cliente, seguindo o estilo de layout "
            f"do setor: {cfg.estilo_layout}"
        ),
        backstory=(
            f"Voce e um designer grafico automatizado especializado em "
            f"{cfg.label}, que usa templates (estilo BannerBear) para compor "
            "pecas finais consistentes com a identidade visual de cada cliente "
            "white label e com as convencoes visuais do nicho."
        ),
        tools=[bannerbear_tool],
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
