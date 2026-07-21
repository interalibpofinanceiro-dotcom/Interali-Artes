"""CRUD basico da entidade Empresa (cliente White Label multi-nicho)."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import select

from interali_ai import config
from interali_ai.database.db import get_session
from interali_ai.database.models import Empresa


def _proxima_renovacao(hoje: dt.date | None = None) -> dt.date:
    hoje = hoje or dt.date.today()
    ano, mes = hoje.year, hoje.month
    if mes == 12:
        return dt.date(ano + 1, 1, 1)
    return dt.date(ano, mes + 1, 1)


def criar_empresa(
    empresa_id: str,
    nome_comercial: str,
    setor_macro: str = "",
    sub_nicho: str = "",
    logo_url: Optional[str] = None,
    cores_hex: Optional[dict] = None,
) -> Empresa:
    """Cria (ou retorna, se ja existir) uma empresa com o plano padrao."""
    with get_session() as session:
        existente = session.get(Empresa, empresa_id)
        if existente:
            return existente

        empresa = Empresa(
            id=empresa_id,
            nome_comercial=nome_comercial,
            setor_macro=setor_macro,
            sub_nicho=sub_nicho,
            logo_url=logo_url,
            cores_hex=cores_hex or {},
            limite_artes_mensal=config.LIMITE_ARTES_MENSAL_PADRAO,
            artes_usadas_no_mes=0,
            limite_videos_mensal=config.LIMITE_VIDEOS_MENSAL_PADRAO,
            videos_usados_no_mes=0,
            data_renovacao_creditos=_proxima_renovacao(),
        )
        session.add(empresa)
        session.flush()
        session.refresh(empresa)
        session.expunge(empresa)
        return empresa


def obter_empresa(empresa_id: str) -> Optional[Empresa]:
    with get_session() as session:
        empresa = session.get(Empresa, empresa_id)
        if empresa:
            session.expunge(empresa)
        return empresa


def listar_empresas() -> list[Empresa]:
    with get_session() as session:
        empresas = list(session.scalars(select(Empresa)).all())
        for e in empresas:
            session.expunge(e)
        return empresas


def salvar_perfil_ia(
    empresa_id: str,
    persona_deduzida: str,
    tom_de_voz_deduzido: str,
    diretrizes_eticas_nicho: str,
) -> Empresa:
    """Grava o resultado do Agente 0 (Onboarding) diretamente na empresa."""
    with get_session() as session:
        empresa = session.get(Empresa, empresa_id)
        if empresa is None:
            raise ValueError(f"Empresa '{empresa_id}' nao encontrada.")

        empresa.persona_deduzida = persona_deduzida
        empresa.tom_de_voz_deduzido = tom_de_voz_deduzido
        empresa.diretrizes_eticas_nicho = diretrizes_eticas_nicho
        session.flush()
        session.refresh(empresa)
        session.expunge(empresa)
        return empresa
