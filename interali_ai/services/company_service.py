"""CRUD basico da entidade Empresa (conta do cliente, isolada por usuario)."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from interali_ai import config
from interali_ai.database.db import get_session
from interali_ai.database.models import Empresa


def _proxima_renovacao(hoje: dt.date | None = None) -> dt.date:
    hoje = hoje or dt.date.today()
    ano, mes = hoje.year, hoje.month
    if mes == 12:
        return dt.date(ano + 1, 1, 1)
    return dt.date(ano, mes + 1, 1)


def criar_empresa(empresa_id: str, nome_comercial: str, cnpj_cpf: str = "") -> Empresa:
    """Cria a conta/empresa do cliente com o plano padrao (chamado no cadastro,
    via auth_service.criar_usuario). Setor/nicho/persona sao preenchidos
    depois, no Perfil da Marca."""
    with get_session() as session:
        empresa = Empresa(
            id=empresa_id,
            nome_comercial=nome_comercial,
            cnpj_cpf=cnpj_cpf or None,
            cores_hex={},
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


def atualizar_perfil(
    empresa_id: str,
    sub_nicho: Optional[str] = None,
    persona_deduzida: Optional[str] = None,
    setor_macro: Optional[str] = None,
    diretrizes_eticas_nicho: Optional[str] = None,
    logo_url: Optional[str] = None,
    cores_hex: Optional[dict] = None,
) -> Empresa:
    """Grava o Perfil da Marca. So atualiza os campos explicitamente passados
    (None = mantem o valor atual). `setor_macro`/`diretrizes_eticas_nicho` sao
    sempre calculados pelo sistema (classificacao automatica do nicho em
    onboarding_crew.py), nunca escolhidos diretamente pelo cliente."""
    with get_session() as session:
        empresa = session.get(Empresa, empresa_id)
        if empresa is None:
            raise ValueError(f"Empresa '{empresa_id}' nao encontrada.")

        if sub_nicho is not None:
            empresa.sub_nicho = sub_nicho
        if persona_deduzida is not None:
            empresa.persona_deduzida = persona_deduzida
        if setor_macro is not None:
            empresa.setor_macro = setor_macro
        if diretrizes_eticas_nicho is not None:
            empresa.diretrizes_eticas_nicho = diretrizes_eticas_nicho
        if logo_url is not None:
            empresa.logo_url = logo_url
        if cores_hex is not None:
            empresa.cores_hex = cores_hex

        session.flush()
        session.refresh(empresa)
        session.expunge(empresa)
        return empresa
