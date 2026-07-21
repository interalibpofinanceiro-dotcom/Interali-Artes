"""Registry central dos 4 setores (nichos macro) da plataforma multi-nicho.

Cada agente (Onboarding, Diretor de Imagem, Copywriter, Designer, Motion
Producer e QA) consulta este registry, a partir de `empresa.setor_macro`,
para adaptar sua skill (goal/backstory/prompt) sem precisar de `if`s
espalhados pelo codigo. Adicionar um novo setor = adicionar uma nova
entrada em `SETORES`.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigSetor:
    valor: str
    label: str
    sub_nicho_exemplos: tuple[str, ...]

    # Agente 0 - Onboarding (Branding Profiler)
    onboarding_foco: str
    pergunta_inicial: str

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
        pergunta_inicial=(
            "Oi! Sou a IA de onboarding da Interali. Para montar o perfil da sua "
            "marca, me conta: qual sua especialidade e linha de atuacao, voce "
            "atende particular, convenio ou os dois, e como gostaria que seus "
            "pacientes se sentissem ao ler seu conteudo?"
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
        pergunta_inicial=(
            "Oi! Sou a IA de onboarding da Interali. Me conta: quais servicos "
            "voce mais vende (cabelo, unhas, estetica...), qual o estilo/conceito "
            "do seu espaco (luxo, moderno, popular) e o que te diferencia da "
            "concorrencia?"
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
        pergunta_inicial=(
            "Oi! Sou a IA de onboarding da Interali. Me conta: quais servicos "
            "voce oferece (trafego pago, social media, consultoria...), quem e "
            "seu cliente ideal e qual a principal dor que ele tem antes de te "
            "contratar?"
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
        pergunta_inicial=(
            "Oi! Sou a IA de onboarding da Interali. Me conta: quem e o seu "
            "publico, quais os principais itens do seu cardapio e como voce "
            "costuma falar com seus clientes? (Ex: 'Sou o Ze, vendo pizza "
            "barata para estudantes a noite')"
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
}

SETOR_PADRAO = "gastronomia"


def obter_config_setor(setor_macro: str | None) -> ConfigSetor:
    """Retorna a config do setor; cai para Gastronomia se vier vazio/invalido."""
    return SETORES.get((setor_macro or "").strip().lower(), SETORES[SETOR_PADRAO])


def listar_setores() -> list[tuple[str, str]]:
    """Lista (valor, label) na ordem definida, para uso em selectboxes."""
    return [(cfg.valor, cfg.label) for cfg in SETORES.values()]
