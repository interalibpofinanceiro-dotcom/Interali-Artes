"""Orquestracao do Agente 0 (Onboarding Inteligente / Branding Profiler).

Recebe as respostas brutas do cliente e ja salva persona_deduzida,
tom_de_voz_deduzido e diretrizes_eticas_nicho diretamente no banco. O foco
da entrevista e da deducao muda de acordo com `setor_macro` (Saude, Beleza,
Marketing ou Gastronomia) - ver interali_ai/nichos.py.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from interali_ai import config
from interali_ai.nichos import obter_config_setor
from interali_ai.services import company_service

_PROMPT_TASK = """
Com base nas respostas brutas abaixo, fornecidas por um cliente do setor \
"{setor_label}" (sub-nicho: "{sub_nicho}"), gere um perfil de marca \
estruturado contendo:

1. Perfil Demografico e Psicografico da Persona (publico-alvo).
2. Tres pilares do Tom de Voz da marca.
3. Diretrizes eticas e de comunicacao (o que pode e o que NAO pode ser dito) \
adequadas a este setor especifico.

Foco obrigatorio da entrevista/deducao para este setor:
\"\"\"
{foco_setor}
\"\"\"

Respostas brutas do cliente:
\"\"\"
{respostas}
\"\"\"

Responda SOMENTE no formato estruturado solicitado.
"""


class PerfilDeMarca(BaseModel):
    persona_deduzida: str = Field(
        ..., description="Perfil demografico e psicografico da persona-alvo."
    )
    tom_de_voz_deduzido: str = Field(
        ..., description="Os tres pilares do tom de voz da marca."
    )
    diretrizes_eticas_nicho: str = Field(
        ..., description="Diretrizes eticas e de comunicacao (palavras proibidas/permitidas) do nicho."
    )


def _perfil_simulado(setor_macro: str, respostas: str) -> PerfilDeMarca:
    """Fallback sem LLM (usado quando OPENAI_API_KEY nao esta configurada),
    para permitir testar o fluxo completo do MVP imediatamente."""
    cfg = obter_config_setor(setor_macro)
    diretrizes = cfg.regra_de_ouro or cfg.diretrizes_eticas_padrao or (
        "Evite promessas irreais, comparacoes agressivas com concorrentes e "
        "linguagem sensacionalista; priorize clareza e honestidade."
    )
    return PerfilDeMarca(
        persona_deduzida=(
            f"[Modo simulado] Publico-alvo tipico do setor '{cfg.label}', "
            f"inferido a partir de: \"{respostas.strip()[:200]}\". "
            "Configure OPENAI_API_KEY no .env para uma deducao real via LLM."
        ),
        tom_de_voz_deduzido=(
            "1) Proximo e proximo da linguagem do cliente; 2) Direto e sem "
            "enrolacao; 3) Consistente com o posicionamento do setor "
            f"'{cfg.label}'."
        ),
        diretrizes_eticas_nicho=diretrizes,
    )


def _perfil_via_llm(setor_macro: str, respostas: str) -> PerfilDeMarca:
    from crewai import Crew, Process, Task

    from interali_ai.agents.onboarding_agent import build_onboarding_agent

    cfg = obter_config_setor(setor_macro)
    agente = build_onboarding_agent(setor_macro)
    task = Task(
        description=_PROMPT_TASK.format(
            setor_label=cfg.label,
            sub_nicho=", ".join(cfg.sub_nicho_exemplos[:3]),
            foco_setor=cfg.onboarding_foco,
            respostas=respostas,
        ),
        expected_output=(
            "Um objeto estruturado com persona_deduzida, tom_de_voz_deduzido e "
            "diretrizes_eticas_nicho."
        ),
        agent=agente,
        output_pydantic=PerfilDeMarca,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=True)
    crew.kickoff()

    perfil = task.output.pydantic if task.output else None
    return perfil or _perfil_simulado(setor_macro, respostas)


def run_onboarding(empresa_id: str, respostas_brutas: str, setor_macro: str = "") -> dict:
    """Executa o Agente 0 e persiste o resultado nos campos da empresa."""
    if config.USE_LLM:
        perfil = _perfil_via_llm(setor_macro, respostas_brutas)
    else:
        perfil = _perfil_simulado(setor_macro, respostas_brutas)

    empresa = company_service.salvar_perfil_ia(
        empresa_id=empresa_id,
        persona_deduzida=perfil.persona_deduzida,
        tom_de_voz_deduzido=perfil.tom_de_voz_deduzido,
        diretrizes_eticas_nicho=perfil.diretrizes_eticas_nicho,
    )
    return {
        "persona_deduzida": empresa.persona_deduzida,
        "tom_de_voz_deduzido": empresa.tom_de_voz_deduzido,
        "diretrizes_eticas_nicho": empresa.diretrizes_eticas_nicho,
    }
