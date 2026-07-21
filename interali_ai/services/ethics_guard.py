"""Trava de Etica do Agente 5 (QA Specialist).

Verifica se os textos gerados pelo Copywriter contem termos proibidos pelo
nicho do cliente (ex.: normas de conselhos de classe em Saude). Quando o
setor tem `bloqueio_etico=True` (hoje, apenas Saude) e algum termo proibido
e encontrado, a geracao inteira e cancelada ANTES de gastar credito ou de
montar banner/video - o usuario e avisado com o motivo exato.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from interali_ai.nichos import ConfigSetor


@dataclass
class ResultadoEtica:
    aprovado: bool
    termos_encontrados: list[str]
    mensagem: str


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower()


def verificar_conformidade_etica(config_setor: ConfigSetor, textos: list[str]) -> ResultadoEtica:
    """Varre `textos` (hook, texto do banner, legenda) atras de termos proibidos.

    So bloqueia efetivamente a geracao quando `config_setor.bloqueio_etico`
    for True; para os demais setores, a lista de termos_proibidos e apenas
    informativa (poderia futuramente virar um aviso brando na UI).
    """
    conteudo_normalizado = _normalizar(" \n ".join(t or "" for t in textos))

    encontrados = [
        termo
        for termo in config_setor.termos_proibidos
        if re.search(re.escape(_normalizar(termo)), conteudo_normalizado)
    ]

    if encontrados and config_setor.bloqueio_etico:
        return ResultadoEtica(
            aprovado=False,
            termos_encontrados=encontrados,
            mensagem=(
                f"Geracao cancelada: o conteudo fere as diretrizes eticas do "
                f"setor '{config_setor.label}' (conselho de classe). Termos "
                f"proibidos identificados: {', '.join(encontrados)}. Ajuste as "
                "respostas do onboarding ou revise manualmente o pedido."
            ),
        )

    if encontrados:
        return ResultadoEtica(
            aprovado=True,
            termos_encontrados=encontrados,
            mensagem=(
                "Aviso: termos sensiveis identificados "
                f"({', '.join(encontrados)}), mas o setor nao exige bloqueio "
                "automatico."
            ),
        )

    return ResultadoEtica(aprovado=True, termos_encontrados=[], mensagem="Sem termos proibidos identificados.")
