"""Configuracoes centrais do Interali AI Gastronomia.

Le variaveis de ambiente (.env) e expoe constantes usadas pelo restante
do projeto: acesso ao banco, chave de LLM e diretorios de assets.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'interali.db').as_posix()}")

# Modo simulado: ativado automaticamente quando nao ha chave de LLM configurada,
# permitindo rodar e testar o MVP (Streamlit) sem depender de uma API externa.
USE_LLM = bool(OPENAI_API_KEY)

ASSETS_DIR = BASE_DIR / "assets"
UPLOADS_DIR = ASSETS_DIR / "uploads"
PROCESSED_DIR = ASSETS_DIR / "processed"
OUTPUT_DIR = ASSETS_DIR / "output"

for _dir in (UPLOADS_DIR, PROCESSED_DIR, OUTPUT_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Plano padrao contratado (usado ao criar novas empresas).
LIMITE_ARTES_MENSAL_PADRAO = 30
LIMITE_VIDEOS_MENSAL_PADRAO = 8

# Duracao maxima aceita para o video enviado pelo cliente (Agente 4 corta o
# excedente automaticamente). 90s cobre o formato padrao de Reels/TikTok/Shorts.
DURACAO_MAXIMA_VIDEO_SEGUNDOS = 90


def get_llm():
    """Retorna a instancia de LLM usada pelos agentes CrewAI.

    So deve ser chamada quando USE_LLM for True (chave configurada).
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0.4,
    )
