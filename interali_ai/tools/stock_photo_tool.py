"""Banco de imagens gratuito (Pexels) - alternativa ao upload proprio na
tela "Gerar Peca".

Usa a API oficial e gratuita do Pexels (https://www.pexels.com/api/). Sem
`PEXELS_API_KEY` configurada (`config.USE_BANCO_IMAGENS`), esta funcionalidade
fica desabilitada na UI - nao ha modo simulado aqui pois depende de acervo
real de fotos.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import requests

from interali_ai import config

_PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


class BuscaImagensError(Exception):
    pass


def buscar_imagens(query: str, por_pagina: int = 9) -> list[dict]:
    """Busca fotos gratuitas no Pexels. Retorna uma lista de dicts com
    id, thumbnail_url, url_original e fotografo."""
    if not config.USE_BANCO_IMAGENS:
        raise BuscaImagensError("PEXELS_API_KEY nao configurada.")
    if not query or not query.strip():
        return []

    resposta = requests.get(
        _PEXELS_SEARCH_URL,
        headers={"Authorization": config.PEXELS_API_KEY},
        params={"query": query.strip(), "per_page": por_pagina},
        timeout=15,
    )
    resposta.raise_for_status()
    dados = resposta.json()

    return [
        {
            "id": foto["id"],
            "thumbnail_url": foto["src"]["medium"],
            "url_original": foto["src"]["large2x"],
            "fotografo": foto.get("photographer", ""),
        }
        for foto in dados.get("photos", [])
    ]


def baixar_imagem(url_original: str, prefixo: str = "pexels") -> str:
    """Baixa a foto escolhida pelo cliente e salva em assets/uploads/, para
    entrar no mesmo `image_path` que o upload proprio alimenta em
    crews/production_crew.py."""
    resposta = requests.get(url_original, timeout=30)
    resposta.raise_for_status()

    destino = config.UPLOADS_DIR / f"{prefixo}_{uuid.uuid4().hex[:8]}.jpg"
    Path(destino).write_bytes(resposta.content)
    return str(destino)
