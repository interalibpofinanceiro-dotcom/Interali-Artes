"""Controle de consumo mensal (creditos de artes e videos).

Regra de negocio central do SaaS: antes de acionar a equipe de agentes de
producao, o sistema precisa confirmar que a empresa ainda tem saldo no mes
corrente. Este modulo tambem cuida da renovacao automatica do ciclo mensal.
"""
from __future__ import annotations

import datetime as dt
from typing import Literal

from interali_ai.database.db import get_session
from interali_ai.database.models import Empresa

TipoCredito = Literal["arte", "video"]


class SaldoInsuficienteError(Exception):
    """Levantada quando a empresa esgotou o limite do mes para o tipo pedido."""


def _proxima_renovacao(hoje: dt.date | None = None) -> dt.date:
    hoje = hoje or dt.date.today()
    ano, mes = hoje.year, hoje.month
    if mes == 12:
        return dt.date(ano + 1, 1, 1)
    return dt.date(ano, mes + 1, 1)


def resetar_creditos_se_necessario(empresa_id: str) -> Empresa:
    """Zera os contadores de uso quando o ciclo mensal virou."""
    with get_session() as session:
        empresa = session.get(Empresa, empresa_id)
        if empresa is None:
            raise ValueError(f"Empresa '{empresa_id}' nao encontrada.")

        hoje = dt.date.today()
        if empresa.data_renovacao_creditos is None or hoje >= empresa.data_renovacao_creditos:
            empresa.artes_usadas_no_mes = 0
            empresa.videos_usados_no_mes = 0
            empresa.data_renovacao_creditos = _proxima_renovacao(hoje)
            session.flush()

        session.refresh(empresa)
        session.expunge(empresa)
        return empresa


def possui_creditos(empresa_id: str, tipo: TipoCredito) -> bool:
    """Verifica `artes_usadas_no_mes < limite_artes_mensal` (ou equivalente p/ video)."""
    empresa = resetar_creditos_se_necessario(empresa_id)
    if tipo == "arte":
        return empresa.artes_usadas_no_mes < empresa.limite_artes_mensal
    return empresa.videos_usados_no_mes < empresa.limite_videos_mensal


def consumir_credito(empresa_id: str, tipo: TipoCredito) -> Empresa:
    """Desconta 1 credito do saldo do cliente (chamado pelo Agente 5 - QA, apos aprovacao)."""
    with get_session() as session:
        empresa = session.get(Empresa, empresa_id)
        if empresa is None:
            raise ValueError(f"Empresa '{empresa_id}' nao encontrada.")

        if tipo == "arte":
            if empresa.artes_usadas_no_mes >= empresa.limite_artes_mensal:
                raise SaldoInsuficienteError("Limite mensal de artes atingido.")
            empresa.artes_usadas_no_mes += 1
        else:
            if empresa.videos_usados_no_mes >= empresa.limite_videos_mensal:
                raise SaldoInsuficienteError("Limite mensal de videos atingido.")
            empresa.videos_usados_no_mes += 1

        session.flush()
        session.refresh(empresa)
        session.expunge(empresa)
        return empresa


def resumo_creditos(empresa_id: str) -> dict:
    """Usado pelo Dashboard (Tela 2 do Streamlit)."""
    empresa = resetar_creditos_se_necessario(empresa_id)
    return {
        "artes_restantes": empresa.limite_artes_mensal - empresa.artes_usadas_no_mes,
        "artes_limite": empresa.limite_artes_mensal,
        "videos_restantes": empresa.limite_videos_mensal - empresa.videos_usados_no_mes,
        "videos_limite": empresa.limite_videos_mensal,
        "data_renovacao": empresa.data_renovacao_creditos,
    }
