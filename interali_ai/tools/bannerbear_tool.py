"""Simulacao da API BannerBear (Agente 3 - Designer Grafico / Visual Composer).

Composicao de designer: o texto fica SOBREPOSTO na propria foto (nao numa
barra separada abaixo dela), com um degrade de contraste na base para
garantir legibilidade sobre qualquer imagem, tipografia em negrito com
sombra, um "chip" de destaque na cor da marca e o logotipo como selo
discreto no canto - layout pronto para Instagram/Reels, adaptado ao perfil
do nicho (ver interali_ai/nichos.py):
 - Saude: degrade suave e curto, tipografia menor, sem chip (clean).
 - Beleza: degrade elegante, chip fino de destaque acima do texto.
 - Marketing: area de texto maior, chip de destaque mais presente.
 - Gastronomia: degrade generoso e vibrante, texto grande e impactante.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def _cores(
    cores_hex: dict | None,
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    primaria = (200, 30, 30)
    secundaria = (255, 255, 255)
    destaque = secundaria
    if cores_hex:
        if cores_hex.get("primaria") or cores_hex.get("primary"):
            hex_str = (cores_hex.get("primaria") or cores_hex.get("primary")).lstrip("#")
            primaria = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
        if cores_hex.get("secundaria") or cores_hex.get("secondary"):
            hex_str = (cores_hex.get("secundaria") or cores_hex.get("secondary")).lstrip("#")
            secundaria = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
            destaque = secundaria
        if cores_hex.get("destaque") or cores_hex.get("accent"):
            hex_str = (cores_hex.get("destaque") or cores_hex.get("accent")).lstrip("#")
            destaque = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
    return primaria, secundaria, destaque


def _fonte(tamanho: int, negrito: bool = False) -> ImageFont.ImageFont:
    candidatos = ("arialbd.ttf", "Arial Bold.ttf") if negrito else ("arial.ttf",)
    for nome in candidatos:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except OSError:
        return ImageFont.load_default()


# Parametros de layout por setor: (fracao da area de texto/degrade sobre a
# imagem, fracao da fonte do headline em relacao a largura, mostra chip de
# destaque acima do texto)
_LAYOUT_POR_SETOR: dict[str, tuple[float, float, bool]] = {
    "saude": (0.38, 0.065, False),        # clean/minimalista, degrade curto, sem chip
    "beleza": (0.42, 0.075, True),        # elegante, com chip fino de destaque
    "marketing": (0.46, 0.080, True),     # area maior, chip mais presente
    "gastronomia": (0.52, 0.090, True),   # vibrante, texto grande
}
_LAYOUT_PADRAO = (0.42, 0.072, False)


def obter_layout_padrao(setor_macro: str = "") -> tuple[float, float]:
    """(area_texto_fracao, fonte_fracao) padrao do perfil - usado para
    prefencher o painel "Ajustar arte" ja sincronizado com o que foi gerado."""
    cfg = obter_config_setor(setor_macro)
    area_fracao, fonte_fracao, _chip = _LAYOUT_POR_SETOR.get(cfg.valor, _LAYOUT_PADRAO)
    return area_fracao, fonte_fracao


def _degrade_vertical(
    tamanho: tuple[int, int], altura_fracao: float, cor_base: tuple[int, int, int], alpha_maximo: int = 225
) -> Image.Image:
    """Degrade transparente->escuro na base da imagem, para o texto ficar
    legivel por cima de qualquer foto."""
    w, h = tamanho
    overlay = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    altura_degrade = max(int(h * altura_fracao), 1)
    topo = h - altura_degrade
    for y in range(topo, h):
        t = (y - topo) / max(altura_degrade - 1, 1)
        alpha = int(alpha_maximo * (t ** 1.3))
        draw.line([(0, y), (w, y)], fill=cor_base + (alpha,))
    return overlay


def _quebrar_texto(draw: ImageDraw.ImageDraw, texto: str, fonte: ImageFont.ImageFont, largura_maxima: float) -> list[str]:
    palavras = texto.split()
    linhas: list[str] = []
    linha_atual = ""
    for palavra in palavras:
        tentativa = f"{linha_atual} {palavra}".strip()
        if draw.textlength(tentativa, font=fonte) <= largura_maxima or not linha_atual:
            linha_atual = tentativa
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    if len(linhas) > 3:
        linhas = linhas[:3]
        linhas[-1] = linhas[-1].rstrip(".") + "…"
    return linhas


def simulate_bannerbear(
    image_path: str,
    texto_banner: str,
    logo_path: str | None = None,
    cores_hex: dict | None = None,
    setor_macro: str = "",
    area_texto_fracao: float | None = None,
    fonte_fracao: float | None = None,
    alinhamento: str = "esquerda",
) -> str:
    """Monta o banner final: texto sobreposto na foto (com degrade de
    contraste), chip de destaque e logo como selo no canto.

    `area_texto_fracao`/`fonte_fracao`/`alinhamento` ("esquerda"/"centro"/
    "direita") sobrescrevem o padrao do perfil visual do nicho quando
    informados - usado pelo painel "Ajustar arte" (Gerar Peca) para o
    cliente afinar cor/fonte/posicao sem rodar os agentes de novo nem gastar
    credito."""
    cfg = obter_config_setor(setor_macro)
    area_padrao, fonte_padrao, mostrar_chip = _LAYOUT_POR_SETOR.get(cfg.valor, _LAYOUT_PADRAO)
    area_texto_fracao = area_padrao if area_texto_fracao is None else area_texto_fracao
    fonte_fracao = fonte_padrao if fonte_fracao is None else fonte_fracao

    origem = Path(image_path)
    cor_primaria, cor_secundaria, cor_destaque = _cores(cores_hex)
    # Degrade sempre escuro (tingido pela cor primaria da marca) para garantir
    # contraste com o texto claro, independente da cor escolhida pelo cliente.
    cor_degrade = tuple(int(c * 0.28) for c in cor_primaria)

    with Image.open(origem) as base:
        banner = base.convert("RGBA")
        w, h = banner.size

        overlay = _degrade_vertical((w, h), area_texto_fracao, cor_degrade)
        banner.alpha_composite(overlay)

        draw = ImageDraw.Draw(banner)
        margem = max(int(w * 0.06), 24)

        fonte_headline = _fonte(max(int(w * fonte_fracao), 22), negrito=True)
        largura_maxima = w - 2 * margem
        linhas = _quebrar_texto(draw, texto_banner, fonte_headline, largura_maxima)

        bbox_linha = draw.textbbox((0, 0), "Ag", font=fonte_headline)
        altura_linha = (bbox_linha[3] - bbox_linha[1]) * 1.25
        altura_bloco = altura_linha * len(linhas)

        y_topo_bloco = h - margem - altura_bloco

        if mostrar_chip:
            chip_largura = max(int(w * 0.12), 40)
            chip_altura = max(int(altura_linha * 0.12), 5)
            chip_y = y_topo_bloco - chip_altura - int(altura_linha * 0.35)
            chip_x = margem if alinhamento != "direita" else w - margem - chip_largura
            if alinhamento == "centro":
                chip_x = (w - chip_largura) // 2
            draw.rounded_rectangle(
                [(chip_x, chip_y), (chip_x + chip_largura, chip_y + chip_altura)],
                radius=chip_altura // 2,
                fill=cor_destaque + (255,),
            )

        y_cursor = y_topo_bloco
        for linha in linhas:
            texto_largura = draw.textlength(linha, font=fonte_headline)
            if alinhamento == "centro":
                x = (w - texto_largura) / 2
            elif alinhamento == "direita":
                x = w - margem - texto_largura
            else:
                x = margem
            sombra_offset = max(int(getattr(fonte_headline, "size", 16) * 0.04), 2)
            draw.text((x + sombra_offset, y_cursor + sombra_offset), linha, font=fonte_headline, fill=(0, 0, 0, 160))
            draw.text((x, y_cursor), linha, font=fonte_headline, fill=cor_secundaria + (255,))
            y_cursor += altura_linha

        if logo_path and Path(logo_path).exists():
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_tam = max(int(min(w, h) * 0.11), 48)
            logo_img.thumbnail((logo_tam, logo_tam))
            pad = max(int(logo_img.width * 0.22), 8)
            selo_w, selo_h = logo_img.width + pad * 2, logo_img.height + pad * 2
            draw.rounded_rectangle(
                [(margem, margem), (margem + selo_w, margem + selo_h)],
                radius=int(selo_h * 0.22),
                fill=(255, 255, 255, 235),
            )
            banner.alpha_composite(logo_img, dest=(margem + pad, margem + pad))

    destino = config.OUTPUT_DIR / f"{origem.stem}_banner.png"
    banner.convert("RGB").save(destino, format="PNG")
    return str(destino)
