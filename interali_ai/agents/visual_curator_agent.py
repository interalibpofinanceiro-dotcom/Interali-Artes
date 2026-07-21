"""Agente 1 - O Diretor de Imagem & Estetica (Visual Specialist AI).

Trata a foto/video bruto do cliente adaptando o tratamento visual ao setor
(simulando a API Photoroom): Saude usa iluminacao soft e ambiente acolhedor,
Beleza realca brilho/tom de pele, Marketing usa visual tech/corporativo e
Gastronomia realca suculencia/textura - ver interali_ai/nichos.py.

Este passo e deterministico, entao a orquestracao principal
(crews/production_crew.py) chama diretamente `simulate_photoroom`. O Agent
CrewAI abaixo (com a tool anexada) fica disponivel caso se queira rodar o
pipeline inteiro como um Crew 100% orientado a tool-calling via LLM.
"""
from __future__ import annotations

from crewai import Agent
from crewai.tools import tool

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.tools.photoroom_tool import simulate_photoroom


@tool("Simular Photoroom")
def photoroom_tool(image_path: str, setor_macro: str = "") -> str:
    """Trata a foto bruta do cliente (recorte, iluminacao e cenario) de forma
    adaptada ao setor do negocio. Recebe o caminho de um arquivo de imagem e
    o setor_macro, devolve o caminho da imagem processada."""
    return simulate_photoroom(image_path, setor_macro=setor_macro)


def build_visual_curator_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Diretor de Imagem & Estetica (Visual Specialist AI) - {cfg.label}",
        goal=(
            "Transformar a foto/video bruto do cliente em uma imagem de alta "
            f"qualidade, seguindo a diretriz visual do setor: {cfg.estilo_imagem}"
        ),
        backstory=(
            f"Voce e um diretor de imagem digital especializado em {cfg.label}, "
            "que usa ferramentas de recorte, reiluminacao e composicao de "
            "cenario (estilo Photoroom) para elevar fotos amadoras ao nivel de "
            "campanhas publicitarias profissionais do nicho."
        ),
        tools=[photoroom_tool],
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
