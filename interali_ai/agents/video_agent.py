"""Agente 4 - O Editor de Video (Motion Producer AI).

Quando o objetivo do post e video, transforma a imagem final em um take
dinamico com o estilo de motion adaptado ao setor (ex: zoom in + fumaca para
Gastronomia, cortes dinamicos estilo Hormozi para Marketing) - ver
interali_ai/nichos.py.

Passo deterministico, chamado diretamente por crews/production_crew.py via
`simulate_motion`. O Agent CrewAI abaixo fica disponivel para um pipeline
100% orientado a tool-calling.
"""
from __future__ import annotations

from crewai import Agent
from crewai.tools import tool

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.tools.motion_tool import simulate_motion


@tool("Simular Motion Producer")
def motion_tool(image_path: str, setor_macro: str = "") -> str:
    """Transforma uma imagem estatica em um take dinamico curto, com o
    estilo de motion adaptado ao setor. Recebe o caminho da imagem e o
    setor_macro, devolve o caminho do video (GIF)."""
    return simulate_motion(image_path, setor_macro=setor_macro)


def build_video_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Editor de Video (Motion Producer AI) - {cfg.label}",
        goal=(
            "Transformar a peca final em um video curto e dinamico quando o "
            "objetivo do post for video, seguindo o estilo de motion do "
            f"setor: {cfg.estilo_video}"
        ),
        backstory=(
            f"Voce e um editor de video especializado em conteudo de "
            f"{cfg.label} para redes sociais, dominando os ritmos, "
            "transicoes e recursos (legendas, filtros, elementos graficos) "
            "que mais convertem em cada nicho."
        ),
        tools=[motion_tool],
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
