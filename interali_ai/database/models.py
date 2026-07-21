"""Modelos ORM (SQLAlchemy): `usuarios` (login/autenticacao, 1:1 com
`empresas`) e `empresas` (dados de branding do cliente, o setor/nicho usado
pelos agentes para adaptar suas skills, o perfil de marca e o controle de
creditos mensais).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from interali_ai import config


class Base(DeclarativeBase):
    pass


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    nome_comercial: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Classificacao interna (auto-detectada a partir do nicho em texto livre,
    # nunca escolhida pelo cliente): 'saude', 'beleza', 'marketing',
    # 'gastronomia' ou 'generico' - ver interali_ai/nichos.py::classificar_nicho.
    setor_macro: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Nicho em texto livre, digitado pelo proprio cliente (ex: "Doceria Gourmet").
    sub_nicho: Mapped[str | None] = mapped_column(String(150), nullable=True)

    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # {"primaria": "#...", "secundaria": "#...", "destaque": "#..."}
    cores_hex: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Persona & instrucoes de negocio - editavel pelo cliente no Perfil da
    # Marca (com sugestao opcional por IA), reaproveitado por todos os
    # agentes de producao.
    persona_deduzida: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Diretrizes eticas - SEMPRE auto-geradas a partir do nicho (nunca
    # editaveis pelo cliente, para preservar a Trava de Etica).
    diretrizes_eticas_nicho: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Controle de creditos mensais
    limite_artes_mensal: Mapped[int] = mapped_column(
        Integer, default=config.LIMITE_ARTES_MENSAL_PADRAO
    )
    artes_usadas_no_mes: Mapped[int] = mapped_column(Integer, default=0)
    limite_videos_mensal: Mapped[int] = mapped_column(
        Integer, default=config.LIMITE_VIDEOS_MENSAL_PADRAO
    )
    videos_usados_no_mes: Mapped[int] = mapped_column(Integer, default=0)
    data_renovacao_creditos: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    def onboarding_completo(self) -> bool:
        return bool(self.persona_deduzida and self.sub_nicho)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    empresa_id: Mapped[str] = mapped_column(ForeignKey("empresas.id"), unique=True)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
