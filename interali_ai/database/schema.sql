-- Interali AI - Plataforma Multi-Nicho (Saude, Beleza, Marketing, Gastronomia)
-- Schema do banco de dados. Compativel com PostgreSQL. Para SQLite (usado por
-- padrao no MVP), o SQLAlchemy (models.py) cria a tabela equivalente
-- automaticamente.

CREATE TABLE IF NOT EXISTS empresas (
    id VARCHAR(255) PRIMARY KEY,
    nome_comercial VARCHAR(255),
    setor_macro VARCHAR(50),   -- 'saude', 'beleza', 'marketing', 'gastronomia'
    sub_nicho VARCHAR(100),    -- Ex: 'Psicologia Infantil', 'Harmonizacao Facial', 'Consultor B2B'
    logo_url VARCHAR(255),
    cores_hex JSON,            -- Armazena a paleta do cliente

    -- Onboarding Automatizado pela IA (Agente 0)
    persona_deduzida TEXT,
    tom_de_voz_deduzido TEXT,
    diretrizes_eticas_nicho TEXT, -- Regras especificas (ex: normas CFM/CFP para saude)

    -- Controle de Creditos Mensais (Plano: 30 artes / 8 videos)
    limite_artes_mensal INT DEFAULT 30,
    artes_usadas_no_mes INT DEFAULT 0,
    limite_videos_mensal INT DEFAULT 8,
    videos_usados_no_mes INT DEFAULT 0,
    data_renovacao_creditos DATE
);
