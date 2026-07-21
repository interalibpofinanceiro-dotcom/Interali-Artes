"""Simulacao da API BannerBear (usada pelo Agente 3 - Designer Grafico / Visual Composer).

Em producao seria uma chamada a API do BannerBear com um template. Aqui
montamos o banner final com Pillow: aplica uma barra de marca com as
`cores_hex` do cliente, o logotipo (se houver) e o texto gerado pelo
Agente 2 (Copywriter), com o LAYOUT adaptado ao `setor_macro` do cliente
(ver interali_ai/nichos.py):
 - Saude: clean/minimalista, muito espaco em branco, logo/texto discretos.
 - Beleza: sofisticado, com linha fina de destaque (accent line).
 - Marketing: dinamico, com bloco de destaque (estilo dado/metrica).
 - Gastronomia: promocional vibrante, barra grande e texto em destaque.
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


def _fonte(tamanho: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except OSError:
        return ImageFont.load_default()


# Parametros de layout por setor: (fracao da barra, fracao da fonte, linha fina de destaque, bloco de destaque)
_LAYOUT_POR_SETOR: dict[str, tuple[float, float, bool, bool]] = {
    "saude": (0.14, 0.22, False, False),        # clean/minimalista, barra menor, fonte leve
    "beleza": (0.16, 0.26, True, False),        # sofisticado, com linha fina de destaque
    "marketing": (0.20, 0.30, False, True),     # dinamico, com bloco de destaque
    "gastronomia": (0.20, 0.32, False, False),  # promocional vibrante, texto grande
}


def simulate_bannerbear(
    image_path: str,
    texto_banner: str,
    logo_path: str | None = None,
    cores_hex: dict | None = None,
    setor_macro: str = "",
) -> str:
    """Monta o banner final: imagem + barra de marca + logotipo + texto de impacto."""
    cfg = obter_config_setor(setor_macro)
    barra_fracao, fonte_fracao, linha_fina, bloco_destaque = _LAYOUT_POR_SETOR.get(
        cfg.valor, (0.18, 0.28, False, False)
    )

    origem = Path(image_path)
    cor_primaria, cor_secundaria, cor_destaque = _cores(cores_hex)

    with Image.open(origem) as base:
        base = base.convert("RGBA")
        w, h = base.size

        barra_altura = max(int(h * barra_fracao), 100)
        banner = Image.new("RGBA", (w, h + barra_altura), cor_primaria + (255,))
        banner.paste(base, (0, 0))

        draw = ImageDraw.Draw(banner)

        if linha_fina:
            draw.line([(0, h), (w, h)], fill=cor_destaque + (255,), width=3)

        if bloco_destaque:
            bloco_largura = int(w * 0.22)
            draw.rectangle(
                [(w - bloco_largura, h), (w, h + barra_altura)],
                fill=cor_destaque + (255,),
            )

        padding = int(barra_altura * (0.35 if cfg.valor == "saude" else 0.15))

        if logo_path and Path(logo_path).exists():
            with Image.open(logo_path) as logo:
                logo = logo.convert("RGBA")
                logo_tam = int(barra_altura * (0.55 if cfg.valor == "saude" else 0.7))
                logo.thumbnail((logo_tam, logo_tam))
                banner.alpha_composite(logo, dest=(padding, h + (barra_altura - logo.height) // 2))
                texto_x = padding + logo_tam + padding
        else:
            texto_x = padding

        fonte = _fonte(max(int(barra_altura * fonte_fracao), 16))
        texto_y = h + barra_altura // 2
        draw.text(
            (texto_x, texto_y),
            texto_banner,
            fill=cor_secundaria,
            font=fonte,
            anchor="lm",
        )

    destino = config.OUTPUT_DIR / f"{origem.stem}_banner.png"
    banner.convert("RGB").save(destino, format="PNG")
    return str(destino)
