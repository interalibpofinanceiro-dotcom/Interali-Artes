"""Agente 4 - O Editor de Video (Motion Producer AI).

O cliente envia seu proprio video (ate config.DURACAO_MAXIMA_VIDEO_SEGUNDOS)
e o Agente 4 o edita de verdade com ffmpeg: corta no limite do plano,
enquadra em 9:16 (Reels/TikTok/Shorts) e aplica a barra de marca (logo/cores/
nome) com o layout adaptado ao setor - ver interali_ai/nichos.py e
tools/video_editor_tool.py.

Passo deterministico, chamado diretamente por crews/production_crew.py via
`process_client_video`. O Agent CrewAI abaixo fica disponivel para um
pipeline 100% orientado a tool-calling.
"""
from __future__ import annotations

from crewai import Agent
from crewai.tools import tool

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.tools.video_editor_tool import process_client_video


@tool("Editar Video do Cliente")
def video_editor_tool(
    video_path: str, logo_path: str = "", setor_macro: str = "", nome_comercial: str = ""
) -> str:
    """Corta o video enviado pelo cliente no limite de duracao do plano,
    enquadra em 9:16 e aplica a barra de marca (logo/cores/nome) adaptada ao
    setor. Recebe o caminho do video bruto, devolve o caminho do .mp4 final."""
    return process_client_video(
        video_path, logo_path=logo_path or None, setor_macro=setor_macro, nome_comercial=nome_comercial
    )


def build_video_agent(setor_macro: str = "") -> Agent:
    cfg = obter_config_setor(setor_macro)
    return Agent(
        role=f"Editor de Video (Motion Producer AI) - {cfg.label}",
        goal=(
            "Editar o video enviado pelo cliente para uma peca curta e "
            "profissional, aplicando a identidade da marca, seguindo o "
            f"estilo do setor: {cfg.estilo_video}"
        ),
        backstory=(
            f"Voce e um editor de video especializado em conteudo de "
            f"{cfg.label} para redes sociais, dominando os cortes, "
            "enquadramentos e aplicacao de marca que mais convertem em cada "
            "nicho."
        ),
        tools=[video_editor_tool],
        llm=config.get_llm(),
        allow_delegation=False,
        verbose=True,
    )
