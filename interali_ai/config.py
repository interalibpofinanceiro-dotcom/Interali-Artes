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

# Groq (https://console.groq.com/keys) - API gratuita, sem cartao de credito,
# usada como provedor padrao de IA real (upgrade sem custo em relacao ao modo
# simulado). Se OPENAI_API_KEY tambem estiver configurada, ela tem prioridade
# (permite trocar para o plano pago sem mudar nenhum outro codigo).
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'interali.db').as_posix()}")

# Modo simulado: ativado automaticamente quando nenhuma chave de LLM esta
# configurada, permitindo rodar e testar o MVP (Streamlit) sem depender de
# nenhuma API externa.
USE_LLM = bool(OPENAI_API_KEY or GROQ_API_KEY)

# Banco de imagens gratuito (Pexels - https://www.pexels.com/api/). Sem chave
# configurada, a aba "Banco de Imagens" fica desabilitada (so upload proprio).
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
USE_BANCO_IMAGENS = bool(PEXELS_API_KEY)

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

    So deve ser chamada quando USE_LLM for True (alguma chave configurada).
    Prioriza OPENAI_API_KEY (plano pago) se estiver definida; senao usa
    GROQ_API_KEY (gratuita) - assim, ativar o plano pago no futuro e so
    preencher o .env, sem mudar nenhum outro codigo.
    """
    if OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL_NAME, api_key=OPENAI_API_KEY, temperature=0.4)

    from langchain_groq import ChatGroq

    return ChatGroq(model=GROQ_MODEL_NAME, api_key=GROQ_API_KEY, temperature=0.4)
