"""Simulacao do Editor de Video (Agente 4 - Motion Producer AI).

Sem dependencias pesadas de video (moviepy/ffmpeg), simulamos o resultado
gerando um GIF animado a partir da imagem final, com o RITMO e os efeitos
adaptados ao `setor_macro` do cliente (ver interali_ai/nichos.py):
 - Saude: zoom lento e suave, ~5s (transicoes suaves, tom relaxante).
 - Beleza: zoom mais rapido e pronunciado (ritmo dinamico de transformacao).
 - Marketing: cortes rapidos + elementos graficos "caindo" na tela.
 - Gastronomia: zoom in classico + "fumaca" animada (circulos translucidos subindo).
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from interali_ai import config
from interali_ai.nichos import obter_config_setor

# (fps, duracao_segundos, zoom_maximo) por setor
_MOTION_POR_SETOR: dict[str, tuple[int, int, float]] = {
    "saude": (10, 5, 1.08),
    "beleza": (15, 4, 1.22),
    "marketing": (18, 3, 1.10),
    "gastronomia": (12, 4, 1.15),
}


def _aplicar_fumaca(frame: Image.Image, t: float) -> Image.Image:
    """Simula fumaca/vapor: circulos translucidos brancos subindo (Gastronomia)."""
    frame = frame.convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = frame.size
    random.seed(42)
    for i in range(6):
        raio = int(w * 0.05 * (1 + i * 0.15))
        x = int(w * (0.2 + 0.12 * i))
        y = int(h * (1.0 - t) - i * h * 0.08) % h
        alpha = int(60 * (1 - t))
        draw.ellipse([x - raio, y - raio, x + raio, y + raio], fill=(255, 255, 255, max(alpha, 0)))
    return Image.alpha_composite(frame, overlay)


def _aplicar_elementos_graficos(frame: Image.Image, t: float, cor: tuple[int, int, int]) -> Image.Image:
    """Simula pequenos elementos graficos caindo na tela (Marketing)."""
    frame = frame.convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = frame.size
    random.seed(7)
    for i in range(5):
        tam = int(w * 0.025)
        x = int(w * (0.1 + 0.18 * i))
        y = int((h + tam) * t) - tam
        draw.rectangle([x, y, x + tam, y + tam], fill=cor + (200,))
    return Image.alpha_composite(frame, overlay)


def simulate_motion(image_path: str, setor_macro: str = "") -> str:
    """Gera um take dinamico (GIF) a partir de uma imagem estatica, com
    ritmo e efeitos adaptados ao setor do cliente."""
    cfg = obter_config_setor(setor_macro)
    fps, duracao_segundos, zoom_maximo = _MOTION_POR_SETOR.get(cfg.valor, (12, 4, 1.15))
    total_frames = fps * duracao_segundos

    origem = Path(image_path)
    with Image.open(origem) as img:
        img = img.convert("RGB")
        w, h = img.size
        frames = []

        for i in range(total_frames):
            t = i / max(total_frames - 1, 1)
            escala = 1.0 + (zoom_maximo - 1.0) * t
            novo_w, novo_h = int(w * escala), int(h * escala)
            frame = img.resize((novo_w, novo_h))

            esquerda = (novo_w - w) // 2
            topo = (novo_h - h) // 2
            frame = frame.crop((esquerda, topo, esquerda + w, topo + h))

            if cfg.valor == "gastronomia":
                frame = _aplicar_fumaca(frame, t).convert("RGB")
            elif cfg.valor == "marketing":
                frame = _aplicar_elementos_graficos(frame, t, (255, 200, 40)).convert("RGB")

            frames.append(frame)

    destino = config.OUTPUT_DIR / f"{origem.stem}_video.gif"
    frames[0].save(
        destino,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),
        loop=0,
    )
    return str(destino)
