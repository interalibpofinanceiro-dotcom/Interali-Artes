"""Registry central dos perfis visuais/eticos usados pelos agentes.

O cliente digita o proprio nicho em texto livre (ex: "Doceria Gourmet") no
Perfil da Marca - nunca escolhe um setor numa lista. Nos bastidores,
`classificar_nicho()` mapeia esse texto para 1 destes perfis internos (por
palavra-chave em modo simulado, ou via LLM quando USE_LLM), que os agentes
(Onboarding, Diretor de Imagem, Copywriter, Designer, Motion Producer e QA)
consultam para adaptar sua skill (goal/backstory/prompt) sem precisar de
`if`s espalhados pelo codigo. Adicionar um novo perfil = adicionar uma nova
entrada em `SETORES` (+ palavras-chave em `_PALAVRAS_CHAVE_POR_SETOR`).
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigSetor:
    valor: str
    label: str
    sub_nicho_exemplos: tuple[str, ...]

    # Agente 0 - Onboarding (Branding Profiler) / sugestao de persona
    onboarding_foco: str

    # Agente 1 - Diretor de Imagem & Estetica (Visual Specialist AI)
    estilo_imagem: str
    cor_fundo_base: tuple[int, int, int]

    # Agente 2 - Copywriter (Niche Copywriter)
    tom_copywriting: str
    regra_de_ouro: str | None

    # Agente 3 - Designer Grafico (Visual Composer)
    estilo_layout: str

    # Agente 4 - Editor de Video (Motion Producer AI)
    estilo_video: str

    # Agente 5 - QA / Etica
    termos_proibidos: tuple[str, ...] = field(default_factory=tuple)
    bloqueio_etico: bool = False
    diretrizes_eticas_padrao: str = ""


SETORES: dict[str, ConfigSetor] = {
    "saude": ConfigSetor(
        valor="saude",
        label="Saude & Bem-Estar",
        sub_nicho_exemplos=(
            "Clinica Medica",
            "Psicologia Infantil",
            "Odontologia",
            "Nutricao",
            "Fisioterapia",
        ),
        onboarding_foco=(
            "Extraia obrigatoriamente: (1) a especialidade e a linha de atuacao do "
            "profissional/clinica, (2) o publico atendido (particular, convenio ou "
            "ambos) e (3) o posicionamento desejado (acolhedor, tecnico, "
            "educativo). Com base nisso, gere diretrizes eticas estritas alinhadas "
            "as normas dos conselhos de classe (ex: CFM para medicos, CFP para "
            "psicologos, CFO para dentistas): proibir promessas de cura, "
            "comparacoes com concorrentes, sensacionalismo e qualquer apelo que "
            "explore o medo ou a vaidade do paciente."
        ),
        estilo_imagem=(
            "Remova fundos poluidos e posicione o profissional/clinica em um "
            "ambiente limpo, bem iluminado, humanizado e acolhedor, com "
            "iluminacao suave (soft light) e cores neutras que transmitam "
            "confianca e cuidado."
        ),
        cor_fundo_base=(235, 240, 238),
        tom_copywriting=(
            "Tom empatico, educativo e humanizado. Foque em conscientizacao, "
            "sintomas, bem-estar e autoridade tecnica. NUNCA prometa cura, "
            "resultado garantido ou use ganchos apelativos/sensacionalistas."
        ),
        regra_de_ouro=(
            "Regra de Ouro: nao faz promessas milagrosas, nao usa ganchos "
            "apelativos nem sensacionalistas. O objetivo e conscientizacao e "
            "autoridade, nunca urgencia ou medo."
        ),
        estilo_layout=(
            "Layouts clean e minimalistas, com bastante espaco em branco, "
            "tipografia leve e aplicacao discreta do logo e do registro "
            "profissional (CRM/CRP/CRO)."
        ),
        estilo_video=(
            "Videos educativos curtos, com transicoes suaves, legendas "
            "acessiveis (alto contraste, fonte legivel) e trilha instrumental "
            "relaxante de fundo."
        ),
        termos_proibidos=(
            "garantia de cura",
            "cura garantida",
            "resultado garantido",
            "sem risco",
            "cura definitiva",
            "o melhor medico",
            "a melhor clinica",
            "numero 1 em",
            "desconto imperdivel",
            "promocao imperdivel",
            "antes e depois chocante",
            "melhor da cidade",
        ),
        bloqueio_etico=True,
        diretrizes_eticas_padrao=(
            "Seguir normas do respectivo conselho de classe (CFM/CFP/CFO/CREFITO): "
            "proibido prometer cura ou resultado, comparar-se a concorrentes, usar "
            "depoimentos como prova de eficacia ou explorar medo/vaidade do paciente."
        ),
    ),
    "beleza": ConfigSetor(
        valor="beleza",
        label="Beleza & Estetica",
        sub_nicho_exemplos=(
            "Salao de Beleza",
            "Barbearia",
            "Esteticista",
            "Harmonizacao Facial",
            "Manicure/Nail Designer",
        ),
        onboarding_foco=(
            "Extraia obrigatoriamente: (1) os servicos mais lucrativos do "
            "negocio (cabelo, unhas, estetica, barba etc.), (2) o estilo/conceito "
            "do salao (luxo, conceito/moderno ou popular) e (3) o diferencial "
            "competitivo percebido pelo cliente."
        ),
        estilo_imagem=(
            "Aplique correcao de cor voltada para brilho de cabelo, tom de pele "
            "natural e uniforme, e acabamento de estetica editorial/revista, "
            "realcando textura e luminosidade."
        ),
        cor_fundo_base=(235, 210, 205),
        tom_copywriting=(
            "Tom inspirador, focado em autoimagem, transformacao, tendencia e "
            "autoestima, sempre com uma chamada clara para agendamento."
        ),
        regra_de_ouro=None,
        estilo_layout=(
            "Layouts sofisticados e elegantes, com linhas finas, contrastes "
            "modernos e elementos visuais de tendencia."
        ),
        estilo_video=(
            "Transicoes dinamicas de ritmo (estilo antes/depois elegante ou "
            "processo de trabalho), audio em alta e legendas estilosas."
        ),
        termos_proibidos=(
            "resultado garantido",
            "sem risco nenhum",
            "efeito milagroso",
        ),
        bloqueio_etico=False,
    ),
    "marketing": ConfigSetor(
        valor="marketing",
        label="Marketing & Social Media",
        sub_nicho_exemplos=(
            "Agencia de Trafego Pago",
            "Social Media Freelancer",
            "Consultor B2B",
            "Copywriter",
        ),
        onboarding_foco=(
            "Extraia obrigatoriamente: (1) os servicos oferecidos (gestao de "
            "trafego, social media, consultoria...), (2) o publico-alvo B2B ou "
            "B2C atendido e (3) a principal dor que o cliente ideal enfrenta "
            "antes de contratar."
        ),
        estilo_imagem=(
            "Crie composicoes modernas com visual tech, graficos elegantes, "
            "mockups de tela/dispositivo e paleta de cores corporativa."
        ),
        cor_fundo_base=(25, 30, 45),
        tom_copywriting=(
            "Tom B2B de autoridade, focado em ROI, dor do cliente, organizacao, "
            "posicionamento de mercado e atracao de leads qualificados."
        ),
        regra_de_ouro=None,
        estilo_layout=(
            "Layouts dinamicos, estilo carrossel informativo, dados/numeros em "
            "destaque e design focado em retencao de atencao."
        ),
        estilo_video=(
            "Cortes dinamicos estilo 'fala pra camera', legendas "
            "palavra-por-palavra (estilo Hormozi) e elementos graficos caindo "
            "na tela."
        ),
        termos_proibidos=(
            "resultado garantido",
            "ficar rico rapido",
            "sem esforco",
        ),
        bloqueio_etico=False,
    ),
    "gastronomia": ConfigSetor(
        valor="gastronomia",
        label="Gastronomia",
        sub_nicho_exemplos=(
            "Restaurante",
            "Hamburgueria",
            "Confeitaria",
            "Pizzaria",
            "Cafeteria",
        ),
        onboarding_foco=(
            "Extraia obrigatoriamente: (1) os principais itens do cardapio e o "
            "prato/produto carro-chefe, (2) o horario de funcionamento e canais "
            "de pedido e (3) o publico e a ocasiao de consumo (delivery, "
            "jantar, evento)."
        ),
        estilo_imagem=(
            "Aplique melhoria de suculencia e textura dos alimentos, realce de "
            "cor e cenario de fundo rustico/aconchegante."
        ),
        cor_fundo_base=(60, 40, 30),
        tom_copywriting=(
            "Gatilhos mentais de fome visual, escassez e urgencia, com "
            "linguagem proxima e calorosa."
        ),
        regra_de_ouro=None,
        estilo_layout=(
            "Layouts promocionais vibrantes, foco na imagem do prato em grande "
            "escala e chamadas (precos/promocoes) em destaque."
        ),
        estilo_video=(
            "Movimento de camera em aproximacao (zoom in), efeito de fumaca "
            "animada e trilha alegre."
        ),
        termos_proibidos=(
            "cura garantida",
            "emagrecimento garantido",
        ),
        bloqueio_etico=False,
    ),
    "generico": ConfigSetor(
        valor="generico",
        label="Negocio Geral",
        sub_nicho_exemplos=(
            "Loja de Roupas",
            "Petshop",
            "Escritorio de Advocacia",
            "Imobiliaria",
        ),
        onboarding_foco=(
            "Extraia obrigatoriamente: (1) o principal produto/servico vendido, "
            "(2) o publico-alvo e (3) o principal diferencial percebido pelo "
            "cliente em relacao a concorrencia."
        ),
        estilo_imagem=(
            "Cenario neutro e profissional, boa iluminacao e cores equilibradas "
            "que nao brigam com a paleta da marca do cliente."
        ),
        cor_fundo_base=(40, 40, 45),
        tom_copywriting=(
            "Tom claro e persuasivo, adaptado ao publico descrito na persona, "
            "sem jargao tecnico desnecessario."
        ),
        regra_de_ouro=None,
        estilo_layout=(
            "Layout limpo e versatil, com boa hierarquia entre imagem, texto de "
            "impacto e logo."
        ),
        estilo_video=(
            "Ritmo neutro (zoom suave), legendas legiveis e trilha discreta de "
            "fundo."
        ),
        termos_proibidos=(
            "resultado garantido",
            "sem risco nenhum",
        ),
        bloqueio_etico=False,
    ),
}

SETOR_PADRAO = "generico"

# Palavras-chave (ja sem acento, minusculas) usadas por `classificar_nicho`
# para mapear o texto livre do cliente a um dos perfis acima, sem depender de
# LLM (modo simulado). Cada nicho novo digitado passa por aqui.
_PALAVRAS_CHAVE_POR_SETOR: dict[str, tuple[str, ...]] = {
    "saude": (
        "saude", "clinica", "medic", "psicolog", "fisioterap", "odont",
        "dentist", "nutri", "terapia", "fonoaudi", "veterinari", "hospital",
        "enferm", "consultorio", "psiquiatr", "pediatr",
    ),
    "beleza": (
        "cabelo", "salao", "beleza", "estetic", "barbearia", "unha",
        "manicure", "maquiag", "sobrancel", "depilac", "spa",
        "harmonizacao facial", "nail",
    ),
    "marketing": (
        "marketing", "trafego", "agencia", "consultoria", "b2b",
        "copywriter", "social media", "redes sociais", "seo", "publicidade",
        "branding", "consultor",
    ),
    "gastronomia": (
        "comida", "restaurante", "doceria", "confeitaria", "pizza",
        "hamburgu", "cafeteria", "padaria", "gastronomia", "docer",
        "sorvete", "food", "buffet", "churrasc", "bar ", "lanchonete",
    ),
}


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower()


def classificar_nicho(nicho_texto: str) -> str:
    """Classifica o nicho em texto livre (ex: "Doceria Gourmet") em uma das
    chaves de `SETORES`, por correspondencia de palavras-chave. Nao usa LLM -
    e o fallback usado em modo simulado e a base do modo com LLM (ver
    crews/onboarding_crew.py, que refina a classificacao via LLM quando
    config.USE_LLM)."""
    texto_normalizado = _normalizar(nicho_texto or "")
    if not texto_normalizado.strip():
        return SETOR_PADRAO

    melhor_setor = SETOR_PADRAO
    maior_pontuacao = 0
    for setor, palavras in _PALAVRAS_CHAVE_POR_SETOR.items():
        pontuacao = sum(1 for palavra in palavras if palavra in texto_normalizado)
        if pontuacao > maior_pontuacao:
            maior_pontuacao = pontuacao
            melhor_setor = setor
    return melhor_setor


def obter_config_setor(setor_macro: str | None) -> ConfigSetor:
    """Retorna a config do setor; cai para o perfil Generico se vier vazio/invalido."""
    return SETORES.get((setor_macro or "").strip().lower(), SETORES[SETOR_PADRAO])
