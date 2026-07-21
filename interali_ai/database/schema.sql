-- Interali AI - Plataforma SaaS Multi-Nicho (nicho em texto livre)
-- Schema do banco de dados. Compativel com PostgreSQL. Para SQLite (usado por
-- padrao no MVP), o SQLAlchemy (models.py) cria a tabela equivalente
-- automaticamente.

CREATE TABLE IF NOT EXISTS empresas (
    id VARCHAR(255) PRIMARY KEY,
    nome_comercial VARCHAR(255),
    cnpj_cpf VARCHAR(20),

    -- Classificacao interna, auto-detectada a partir do nicho em texto livre
    -- (nunca escolhida pelo cliente): 'saude', 'beleza', 'marketing',
    -- 'gastronomia' ou 'generico'.
    setor_macro VARCHAR(50),
    sub_nicho VARCHAR(150),    -- Nicho em texto livre digitado pelo cliente (ex: 'Doceria Gourmet')
    logo_url VARCHAR(255),
    cores_hex JSON,            -- {"primaria", "secundaria", "destaque"}

    -- Perfil da Marca (editavel pelo cliente, com sugestao opcional por IA)
    persona_deduzida TEXT,
    -- Diretrizes eticas - SEMPRE auto-geradas a partir do nicho, nunca
    -- editaveis pelo cliente (preserva a Trava de Etica).
    diretrizes_eticas_nicho TEXT,

    -- Controle de Creditos Mensais (Plano: 30 artes / 8 videos)
    limite_artes_mensal INT DEFAULT 30,
    artes_usadas_no_mes INT DEFAULT 0,
    limite_videos_mensal INT DEFAULT 8,
    videos_usados_no_mes INT DEFAULT 0,
    data_renovacao_creditos DATE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    empresa_id VARCHAR(255) UNIQUE REFERENCES empresas(id),
    criado_em TIMESTAMP
);
