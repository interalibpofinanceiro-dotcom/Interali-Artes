"""Autenticacao (login/cadastro) e isolamento multi-tenant.

Cada `Usuario` esta ligado a exatamente uma `Empresa` (1:1). Toda a aplicacao
deriva `empresa_id` do usuario logado (`st.session_state["usuario_id"]`) -
nunca de uma escolha na tela, o que garante que um cliente jamais acesse os
dados de outro.
"""
from __future__ import annotations

import datetime as dt
import re
import uuid
from typing import Optional

import bcrypt
from sqlalchemy import select

from interali_ai.database.db import get_session
from interali_ai.database.models import Empresa, Usuario
from interali_ai.services import company_service

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailInvalidoError(Exception):
    pass


class EmailJaCadastradoError(Exception):
    pass


class CredenciaisInvalidasError(Exception):
    pass


def criar_usuario(email: str, senha: str, nome_comercial: str, cnpj_cpf: str = "") -> Usuario:
    """Cria a conta (Usuario + Empresa vazia, ja linkados) no cadastro inicial."""
    email = email.strip().lower()
    if not _EMAIL_REGEX.match(email):
        raise EmailInvalidoError("Informe um e-mail valido.")

    with get_session() as session:
        existente = session.scalar(select(Usuario).where(Usuario.email == email))
        if existente is not None:
            raise EmailJaCadastradoError("Ja existe uma conta com esse e-mail.")

    empresa_id = uuid.uuid4().hex
    company_service.criar_empresa(empresa_id, nome_comercial=nome_comercial, cnpj_cpf=cnpj_cpf)

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    usuario = Usuario(
        id=uuid.uuid4().hex,
        email=email,
        senha_hash=senha_hash,
        empresa_id=empresa_id,
        criado_em=dt.datetime.utcnow(),
    )
    with get_session() as session:
        session.add(usuario)
        session.flush()
        session.refresh(usuario)
        session.expunge(usuario)
        return usuario


def autenticar(email: str, senha: str) -> Usuario:
    email = email.strip().lower()
    with get_session() as session:
        usuario = session.scalar(select(Usuario).where(Usuario.email == email))
        if usuario is None or not bcrypt.checkpw(
            senha.encode("utf-8"), usuario.senha_hash.encode("utf-8")
        ):
            raise CredenciaisInvalidasError("E-mail ou senha invalidos.")
        session.expunge(usuario)
        return usuario


def obter_empresa_do_usuario(usuario_id: str) -> Optional[Empresa]:
    with get_session() as session:
        usuario = session.get(Usuario, usuario_id)
        if usuario is None:
            return None
        empresa = session.get(Empresa, usuario.empresa_id)
        if empresa:
            session.expunge(empresa)
        return empresa
