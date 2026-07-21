# Interali AI - Plataforma Multi-Nicho

MVP do backend/agentes para a plataforma SaaS White Label **Interali AI**,
atendendo 4 setores: **Saude & Bem-Estar**, **Beleza & Estetica**,
**Marketing & Social Media** e **Gastronomia**.

Multi-tenant, com **Onboarding 100% automatizado** (a IA entrevista o
cliente e deduz persona/tom de voz/diretrizes eticas do nicho, sem
consultoria humana) e **controle de creditos mensais** (30 artes / 8 videos
por empresa).

Construido em Python com **CrewAI** (agentes + orquestracao), **SQLAlchemy**
(banco SQL) e **Streamlit** (interface do MVP).

## Setores e skills adaptativas

Cada agente adapta goal/prompt/tratamento de acordo com o `setor_macro` da
empresa (registry central em `interali_ai/nichos.py`):

| Setor | Imagem (Agente 1) | Copy (Agente 2) | Layout (Agente 3) | Video (Agente 4) |
|---|---|---|---|---|
| Saude | Cenario limpo, luz soft, acolhedor | Empatico/educativo, **sem promessas de cura** | Clean, minimalista, muito espaco em branco | Transicoes suaves, legendas acessiveis |
| Beleza | Brilho/tom de pele, editorial | Inspirador, autoestima, chamada p/ agendamento | Sofisticado, linha fina de destaque | Ritmo dinamico (antes/depois) |
| Marketing | Visual tech, grid corporativo | B2B, autoridade, ROI, dor do cliente | Dinamico, bloco de dado/metrica em destaque | Cortes rapidos, elementos caindo na tela |
| Gastronomia | Suculencia/textura, cenario rustico | Fome visual, escassez, urgencia | Promocional vibrante, prato em destaque | Zoom in + "fumaca" animada |

O **Agente 5 (QA Specialist)** roda a **Trava de Etica**: para setores com
`bloqueio_etico=True` (hoje, apenas Saude), se o texto gerado contiver
termos proibidos pelos conselhos de classe (ex: "garantia de cura", "o
melhor medico da cidade", "desconto imperdivel em procedimento medico"), a
geracao inteira e **cancelada antes de gastar credito**, e o usuario e
avisado com o motivo.

## Estrutura do projeto

```
interali_ai/
  config.py                   # variaveis de ambiente, LLM, diretorios de assets
  nichos.py                   # registry central dos 4 setores (skills adaptativas)
  database/
    schema.sql                # DDL de referencia (Postgres)
    models.py                 # modelo ORM `Empresa` (SQLAlchemy)
    db.py                     # engine/session/init_db
  services/
    company_service.py        # CRUD de empresas
    credit_manager.py         # verificacao/consumo/renovacao de creditos
    ethics_guard.py            # trava de etica (Agente 5 / setor Saude)
  agents/
    onboarding_agent.py        # Agente 0 - Branding Profiler
    visual_curator_agent.py     # Agente 1 - Diretor de Imagem & Estetica (+ tool Photoroom)
    copywriter_agent.py         # Agente 2 - Niche Copywriter
    designer_agent.py           # Agente 3 - Visual Composer (+ tool BannerBear)
    video_agent.py               # Agente 4 - Motion Producer AI (+ tool de edicao real via ffmpeg)
    qa_agent.py                  # Agente 5 - QA Specialist
  tools/
    photoroom_tool.py          # simulacao da API Photoroom (Pillow), adaptada por setor
    bannerbear_tool.py         # simulacao da API BannerBear (Pillow), layout por setor
    video_editor_tool.py        # edicao REAL (ffmpeg) do video do cliente: corta, enquadra 9:16, aplica marca
  crews/
    onboarding_crew.py         # roda o Agente 0 e salva o perfil no banco
    production_crew.py         # verifica creditos + roda Agentes 1-5 + trava de etica

app.py                         # interface Streamlit (Cadastro por setor + 3 telas do MVP)
requirements.txt
.env.example
```

## Como rodar

1. Crie e ative um ambiente virtual (opcional, mas recomendado):

   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Instale as dependencias:

   ```
   pip install -r requirements.txt
   ```

3. Copie `.env.example` para `.env` e configure sua chave da OpenAI:

   ```
   copy .env.example .env
   ```

   > **Sem chave configurada**, o sistema roda em **modo simulado**: os
   > Agentes 0 (Onboarding), 2 (Copywriter) e 5 (QA) retornam respostas
   > heuristicas em vez de chamar um LLM, para que voce possa testar o
   > fluxo completo do MVP imediatamente, sem custo. Os Agentes 1, 3 e 4
   > (tratamento de imagem, montagem do banner e edicao do video) sempre
   > funcionam de verdade - imagem/banner via Pillow, video via ffmpeg (binario
   > gratuito obtido automaticamente pelo pacote `imageio-ffmpeg`, sem
   > instalacao manual nem custo) - ja adaptados ao setor escolhido.

4. Rode a interface:

   ```
   streamlit run app.py
   ```

5. No app: cadastre uma empresa na barra lateral escolhendo o **Setor**
   (Saude, Beleza, Marketing ou Gastronomia) e o sub-nicho, converse na aba
   **Onboarding Automatizado** para a IA deduzir a persona/tom de voz/
   diretrizes eticas, veja o saldo de creditos no **Dashboard** e faca
   upload de uma foto na aba **Gerar Peca** para rodar a equipe completa de
   agentes.

## Banco de dados

Por padrao usa SQLite local (`interali.db`, criado automaticamente por
`init_db()`). Para usar Postgres em producao, defina `DATABASE_URL` no `.env`
(ex: `postgresql+psycopg2://usuario:senha@host:5432/interali`) — o schema em
`interali_ai/database/schema.sql` documenta a tabela `empresas` em SQL puro,
incluindo `setor_macro`, `sub_nicho` e `diretrizes_eticas_nicho`.

## Regra de creditos

Antes de acionar os Agentes de producao (1 a 5), `production_crew.py`
verifica `artes_usadas_no_mes < limite_artes_mensal` (ou o equivalente para
video). O credito so e efetivamente descontado apos o **Agente 5 (QA)**
aprovar a peca final **e** a peca passar pela Trava de Etica. O ciclo mensal
e renovado automaticamente com base em `data_renovacao_creditos`.

## Adicionar um novo setor

Basta adicionar uma nova entrada em `SETORES` em `interali_ai/nichos.py`
(label, foco de onboarding, estilo de imagem/copy/layout/video, termos
proibidos e se tem bloqueio etico). Todos os agentes e tools ja consultam
esse registry automaticamente - nenhum outro arquivo precisa mudar.
