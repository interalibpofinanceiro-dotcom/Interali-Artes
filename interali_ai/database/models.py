"""Modelo ORM (SQLAlchemy) da tabela `empresas`.

Espelha fielmente o schema.sql: dados de branding do cliente, o setor/nicho
(usado pelos agentes para adaptar suas skills), o perfil que a IA de
Onboarding preenche sozinha e o controle de creditos mensais.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from interali_ai import config


class Base(DeclarativeBase):
    pass


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    nome_comercial: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Seletor de setor (Multi-Nicho): 'saude', 'beleza', 'marketing' ou 'gastronomia'
    setor_macro: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sub_nicho: Mapped[str | None] = mapped_column(String(100), nullable=True)

    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cores_hex: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Preenchido automaticamente pelo Agente 0 (Onboarding Inteligente)
    persona_deduzida: Mapped[str | None] = mapped_column(Text, nullable=True)
    tom_de_voz_deduzido: Mapped[str | None] = mapped_column(Text, nullable=True)
    diretrizes_eticas_nicho: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Servicos/produtos que o cliente mais vende - preenchido uma unica vez no
    # Onboarding (momento da assinatura) e reaproveitado em toda geracao de peca.
    servicos_oferecidos: Mapped[str | None] = mapped_column(Text, nullable=True)

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
        return bool(
            self.persona_deduzida and self.tom_de_voz_deduzido and self.servicos_oferecidos
        )
