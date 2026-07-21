# Interali AI - Plataforma SaaS Multi-Nicho

Plataforma SaaS **multi-tenant** (cada cliente loga e só enxerga a própria
conta) para gerar artes e vídeos com IA, adaptados ao nicho **em texto
livre** de cada negócio (ex: "Doceria Gourmet", "Psicologia Infantil",
"Consultoria de Marketing B2B" - sem lista fixa de setores).

**Perfil da Marca** (nicho, identidade visual, persona) preenchido uma única
vez pelo cliente, com sugestão opcional por IA, e **controle de créditos
mensais** (30 artes / 8 vídeos por empresa).

Construído em Python com **CrewAI** (agentes + orquestração), **SQLAlchemy**
(banco SQL) e **Streamlit** (interface).

## Classificação automática do nicho

O cliente nunca escolhe um "setor" numa lista - ele digita o próprio nicho
(`interali_ai/nichos.py::classificar_nicho`). Nos bastidores, esse texto é
classificado por palavra-chave (ou via LLM, quando configurada) em 1 de 5
perfis visuais/éticos internos, que adaptam goal/prompt de cada agente:

| Perfil interno | Imagem (Agente 1) | Copy (Agente 2) | Layout (Agente 3) | Vídeo (Agente 4) |
|---|---|---|---|---|
| Saude | Cenario limpo, luz soft, acolhedor | Empatico/educativo, **sem promessas de cura** | Clean, minimalista, muito espaco em branco | Barra de marca discreta |
| Beleza | Brilho/tom de pele, editorial | Inspirador, autoestima, chamada p/ agendamento | Sofisticado, linha fina de destaque | Barra de marca com acabamento fino |
| Marketing | Visual tech, grid corporativo | B2B, autoridade, ROI, dor do cliente | Dinamico, bloco de dado/metrica em destaque | Barra de marca robusta |
| Gastronomia | Suculencia/textura, cenario rustico | Fome visual, escassez, urgencia | Promocional vibrante, prato em destaque | Barra de marca vibrante |
| Generico | Cenario neutro e profissional | Claro e persuasivo | Layout limpo e versatil | Barra de marca neutra |

O **Agente 5 (QA Specialist)** roda a **Trava de Etica**: para o perfil
Saude (`bloqueio_etico=True`), se o texto gerado contiver termos proibidos
pelos conselhos de classe (ex: "garantia de cura", "desconto imperdivel em
procedimento medico"), a geração inteira é **cancelada antes de gastar
crédito**, e o usuário é avisado com o motivo. As diretrizes éticas
específicas do nicho digitado são sempre geradas pelo sistema - **nunca
editáveis pelo cliente**.

## Estrutura do projeto

```
interali_ai/
  config.py                   # variaveis de ambiente, LLM (Groq/OpenAI), diretorios de assets
  nichos.py                   # perfis visuais/eticos + classificar_nicho() (nicho livre)
  database/
    schema.sql                # DDL de referencia (Postgres)
    models.py                 # modelos ORM `Usuario` e `Empresa` (SQLAlchemy)
    db.py                     # engine/session/init_db (+ migracoes leves)
  services/
    auth_service.py           # login/cadastro, isolamento multi-tenant (bcrypt)
    company_service.py        # CRUD de empresas / perfil da marca
    credit_manager.py         # verificacao/consumo/renovacao de creditos
    ethics_guard.py            # trava de etica (Agente 5 / perfil Saude)
  agents/
    onboarding_agent.py        # Agente 0 - Estrategista de Marca (sugestao + classificacao)
    visual_curator_agent.py     # Agente 1 - Diretor de Imagem & Estetica (+ tool Photoroom)
    copywriter_agent.py         # Agente 2 - Niche Copywriter
    designer_agent.py           # Agente 3 - Visual Composer (+ tool BannerBear)
    video_agent.py               # Agente 4 - Motion Producer AI (+ tool de edicao real via ffmpeg)
    qa_agent.py                  # Agente 5 - QA Specialist
  tools/
    photoroom_tool.py          # simulacao da API Photoroom (Pillow), adaptada por perfil
    bannerbear_tool.py         # simulacao da API BannerBear (Pillow), layout por perfil
    video_editor_tool.py        # edicao REAL (ffmpeg) do video do cliente: corta, enquadra 9:16, aplica marca
    stock_photo_tool.py         # banco de imagens gratuito (API Pexels)
  crews/
    onboarding_crew.py         # sugestao de persona + classificacao automatica do nicho
    production_crew.py         # verifica creditos + roda Agentes 1-5 + trava de etica

app.py                         # interface Streamlit (login/cadastro + Perfil da Marca + Dashboard + Gerar Peca)
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

3. Copie `.env.example` para `.env`:

   ```
   copy .env.example .env
   ```

   > **Sem nenhuma chave de LLM configurada**, o sistema roda em **modo
   > simulado**: os Agentes 0 (sugestao/classificacao), 2 (Copywriter) e 5
   > (QA) retornam respostas heuristicas em vez de chamar um LLM, para que
   > voce possa testar o fluxo completo imediatamente, sem custo. Os
   > Agentes 1, 3 e 4 (tratamento de imagem, montagem do banner e edicao do
   > video) sempre funcionam de verdade - imagem/banner via Pillow, video via
   > ffmpeg (binario gratuito obtido automaticamente pelo pacote
   > `imageio-ffmpeg`) - ja adaptados ao perfil do nicho.
   >
   > Para ativar a IA de verdade **gratuitamente**, gere uma chave em
   > [console.groq.com/keys](https://console.groq.com/keys) (sem cartao de
   > credito) e configure `GROQ_API_KEY` no `.env`. Para trocar para o plano
   > pago da OpenAI depois, basta preencher `OPENAI_API_KEY` - ela tem
   > prioridade automaticamente, sem mudar nenhum codigo.
   >
   > O banco de imagens gratuito (aba "Banco de Imagens" em Gerar Peca) usa a
   > API do Pexels - gere uma chave em
   > [pexels.com/api](https://www.pexels.com/api/) e configure
   > `PEXELS_API_KEY`. Sem essa chave, a aba fica desabilitada e o cliente so
   > pode enviar a propria foto/video.

4. Rode a interface:

   ```
   streamlit run app.py
   ```

5. No app: crie uma conta (Nome Comercial, CNPJ/CPF, E-mail, Senha) na tela
   de Cadastro, preencha o **Perfil da Marca** (nicho em texto livre,
   logo + cores, persona com sugestao opcional por IA), veja o saldo de
   creditos no topo e gere uma peca (upload proprio ou banco de imagens) na
   aba **Gerar Peca**.

## Autenticacao e isolamento multi-tenant

Cada `Usuario` (`interali_ai/database/models.py`) esta ligado a exatamente
uma `Empresa` (1:1), com senha em hash bcrypt
(`interali_ai/services/auth_service.py`). `empresa_id` deriva sempre do
usuario logado (`st.session_state["usuario_id"]`) - nao existe seletor de
empresa na UI, o que garante que um cliente jamais acesse dados de outro.

## Banco de dados

Por padrao usa SQLite local (`interali.db`, criado automaticamente por
`init_db()`, que tambem aplica migracoes leves para colunas novas). Para usar
Postgres em producao, defina `DATABASE_URL` no `.env` (ex:
`postgresql+psycopg2://usuario:senha@host:5432/interali`) — o schema em
`interali_ai/database/schema.sql` documenta as tabelas `usuarios` e
`empresas` em SQL puro.

## Regra de creditos

Antes de acionar os Agentes de producao (1 a 5), `production_crew.py`
verifica `artes_usadas_no_mes < limite_artes_mensal` (ou o equivalente para
video). O credito so e efetivamente descontado apos o **Agente 5 (QA)**
aprovar a peca final **e** a peca passar pela Trava de Etica. O ciclo mensal
e renovado automaticamente com base em `data_renovacao_creditos`.

## Adicionar um novo perfil visual/etico

Basta adicionar uma nova entrada em `SETORES` em `interali_ai/nichos.py`
(label, foco de onboarding, estilo de imagem/copy/layout/video, termos
proibidos e se tem bloqueio etico) e as palavras-chave correspondentes em
`_PALAVRAS_CHAVE_POR_SETOR`, para que `classificar_nicho()` passe a
reconhecer nichos desse tipo. Todos os agentes e tools ja consultam esse
registry automaticamente - nenhum outro arquivo precisa mudar.
