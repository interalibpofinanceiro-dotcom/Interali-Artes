"""Simulacao da API Photoroom (usada pelo Agente 1 - Diretor de Imagem & Estetica).

Em producao isto seria uma chamada HTTP a API real do Photoroom (remocao de
fundo + reiluminacao). Aqui simulamos o resultado com Pillow para que o MVP
seja executavel de ponta a ponta sem credenciais externas.

O tratamento e adaptado ao `setor_macro` do cliente (ver interali_ai/nichos.py):
 - Saude: cenario limpo, iluminacao soft, cores neutras acolhedoras.
 - Beleza: realce de brilho/tom de pele, acabamento editorial.
 - Marketing: cenario tech escuro com leve grid corporativo.
 - Gastronomia: cenario rustico/aconchegante, realce de suculencia/textura.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from interali_ai import config
from interali_ai.nichos import obter_config_setor


def _cor_primaria(cores_hex: dict | None, cor_fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if cores_hex:
        for chave in ("primaria", "primary", "principal"):
            if chave in cores_hex:
                hex_str = cores_hex[chave].lstrip("#")
                if len(hex_str) == 6:
                    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
    return cor_fallback


def _gerar_cenario(tamanho: tuple[int, int], cor_base: tuple[int, int, int]) -> Image.Image:
    """Gera um fundo em degrade simulando um cenario realista de estudio."""
    w, h = tamanho
    fundo = Image.new("RGB", (w, h), cor_base)
    draw = ImageDraw.Draw(fundo)
    claro = tuple(min(255, c + 90) for c in cor_base)
    for y in range(h):
        t = y / max(h - 1, 1)
        cor = tuple(int(cor_base[i] * (1 - t) + claro[i] * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=cor)
    return fundo.filter(ImageFilter.GaussianBlur(radius=8))


def _aplicar_grid_tech(cenario: Image.Image, cor_linha: tuple[int, int, int] = (90, 110, 150)) -> Image.Image:
    """Leve grid corporativo/tech, usado no setor Marketing."""
    draw = ImageDraw.Draw(cenario, "RGBA")
    w, h = cenario.size
    passo = max(w, h) // 12 or 1
    for x in range(0, w, passo):
        draw.line([(x, 0), (x, h)], fill=cor_linha + (40,), width=1)
    for y in range(0, h, passo):
        draw.line([(0, y), (w, y)], fill=cor_linha + (40,), width=1)
    return cenario


# Ajustes de realce (contraste, saturacao, brilho) por setor.
_REALCE_POR_SETOR: dict[str, tuple[float, float, float]] = {
    "saude": (1.05, 1.0, 1.12),        # soft light: baixo contraste/saturacao, mais brilho
    "beleza": (1.12, 1.25, 1.08),      # brilho de cabelo/pele, cores vivas
    "marketing": (1.2, 0.95, 1.0),     # visual tech: contraste alto, saturacao neutra
    "gastronomia": (1.15, 1.2, 1.05),  # suculencia/textura
}


def simulate_photoroom(image_path: str, cores_hex: dict | None = None, setor_macro: str = "") -> str:
    """Recorta a foto bruta e a recontextualiza num cenario adaptado ao setor.

    Retorna o caminho do arquivo processado (PNG) em assets/processed/.
    """
    cfg = obter_config_setor(setor_macro)
    origem = Path(image_path)
    with Image.open(origem) as img:
        img = img.convert("RGBA")

        largura_cenario = max(img.width, 1200)
        altura_cenario = max(img.height, 1200)
        cor_base = _cor_primaria(cores_hex, cfg.cor_fundo_base)
        cenario = _gerar_cenario((largura_cenario, altura_cenario), cor_base)
        if cfg.valor == "marketing":
            cenario = _aplicar_grid_tech(cenario)
        cenario = cenario.convert("RGBA")

        escala = min(largura_cenario * 0.75 / img.width, altura_cenario * 0.75 / img.height)
        novo_tamanho = (int(img.width * escala), int(img.height * escala))
        assunto = img.resize(novo_tamanho)

        # Realce de iluminacao/contraste adaptado ao setor
        contraste, saturacao, brilho = _REALCE_POR_SETOR.get(cfg.valor, (1.15, 1.2, 1.05))
        assunto = ImageEnhance.Contrast(assunto).enhance(contraste)
        assunto = ImageEnhance.Color(assunto).enhance(saturacao)
        assunto = ImageEnhance.Brightness(assunto).enhance(brilho)

        pos = (
            (largura_cenario - assunto.width) // 2,
            (altura_cenario - assunto.height) // 2,
        )
        cenario.alpha_composite(assunto, dest=pos)

    destino = config.PROCESSED_DIR / f"{origem.stem}_styled.png"
    cenario.convert("RGB").save(destino, format="PNG")
    return str(destino)
