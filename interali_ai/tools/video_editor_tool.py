"""Edicao real do video enviado pelo cliente (Agente 4 - Motion Producer AI).

Diferente dos demais "tools" simulados (Photoroom/BannerBear, que usam Pillow
para nao depender de credenciais externas), aqui o video enviado pelo cliente
e de fato editado com **ffmpeg** (binario estatico obtido via `imageio-ffmpeg`,
100% gratuito, sem chave de API e sem instalacao manual): corta no limite de
`config.DURACAO_MAXIMA_VIDEO_SEGUNDOS`, enquadra no formato vertical padrao de
Reels/TikTok/Shorts (9:16) e aplica uma barra de marca (logo + nome + cores do
cliente) na base, com o mesmo layout adaptado ao `setor_macro` usado no banner
(ver bannerbear_tool.py e interali_ai/nichos.py).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from interali_ai import config
from interali_ai.nichos import obter_config_setor

# Formato vertical padrao (Reels/TikTok/Shorts).
_LARGURA_SAIDA = 1080
_ALTURA_SAIDA = 1920

# Parametros de layout por setor: (fracao da barra, fracao da fonte) -
# mesmos valores usados no banner estatico (bannerbear_tool.py), para manter
# a identidade visual consistente entre arte e video.
_LAYOUT_POR_SETOR: dict[str, tuple[float, float]] = {
    "saude": (0.14, 0.22),
    "beleza": (0.16, 0.26),
    "marketing": (0.20, 0.30),
    "gastronomia": (0.20, 0.32),
}


def _cores(cores_hex: dict | None) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    primaria = (200, 30, 30)
    secundaria = (255, 255, 255)
    if cores_hex:
        if cores_hex.get("primaria") or cores_hex.get("primary"):
            hex_str = (cores_hex.get("primaria") or cores_hex.get("primary")).lstrip("#")
            primaria = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
        if cores_hex.get("secundaria") or cores_hex.get("secondary"):
            hex_str = (cores_hex.get("secundaria") or cores_hex.get("secondary")).lstrip("#")
            secundaria = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
    return primaria, secundaria


def _fonte(tamanho: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except OSError:
        return ImageFont.load_default()


def _construir_overlay_marca(
    logo_path: str | None, cores_hex: dict | None, nome_comercial: str, setor_macro: str
) -> Image.Image:
    """Monta um PNG transparente (tamanho da saida) com a barra de marca na
    base - sobreposto em todos os frames do video via ffmpeg."""
    cfg = obter_config_setor(setor_macro)
    barra_fracao, fonte_fracao = _LAYOUT_POR_SETOR.get(cfg.valor, (0.18, 0.28))
    cor_primaria, cor_secundaria = _cores(cores_hex)

    overlay = Image.new("RGBA", (_LARGURA_SAIDA, _ALTURA_SAIDA), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    barra_altura = int(_ALTURA_SAIDA * barra_fracao)
    topo_barra = _ALTURA_SAIDA - barra_altura
    draw.rectangle(
        [(0, topo_barra), (_LARGURA_SAIDA, _ALTURA_SAIDA)],
        fill=cor_primaria + (235,),
    )

    padding = int(barra_altura * 0.25)
    texto_x = padding

    if logo_path and Path(logo_path).exists():
        with Image.open(logo_path) as logo:
            logo = logo.convert("RGBA")
            logo_tam = int(barra_altura * 0.55)
            logo.thumbnail((logo_tam, logo_tam))
            overlay.alpha_composite(
                logo, dest=(padding, topo_barra + (barra_altura - logo.height) // 2)
            )
            texto_x = padding + logo.width + padding

    fonte = _fonte(max(int(barra_altura * fonte_fracao * 0.6), 16))
    draw.text(
        (texto_x, topo_barra + barra_altura // 2),
        nome_comercial or "",
        fill=cor_secundaria,
        font=fonte,
        anchor="lm",
    )
    return overlay


def process_client_video(
    video_path: str,
    logo_path: str | None = None,
    cores_hex: dict | None = None,
    setor_macro: str = "",
    nome_comercial: str = "",
) -> str:
    """Corta o video enviado no limite de duracao do plano, enquadra em 9:16 e
    aplica a barra de marca (logo/cores/nome) adaptada ao setor.

    Retorna o caminho do .mp4 final em assets/output/.

    O ffmpeg le/escreve com padrao de I/O intensivo (muitas leituras/escritas
    pequenas), o que fica extremamente lento se o caminho estiver dentro de
    uma pasta sincronizada (Google Drive/OneDrive/Dropbox) - por isso todo o
    processamento roda numa pasta temporaria local, e so o arquivo final
    (pequeno, uma unica copia) e movido para `assets/output/`.
    """
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    origem = Path(video_path)
    nome_final = f"{origem.stem}_video.mp4"

    with tempfile.TemporaryDirectory(prefix="interali_video_") as tmp:
        tmp_dir = Path(tmp)
        origem_local = tmp_dir / origem.name
        shutil.copyfile(origem, origem_local)

        duracao_real = _duracao_segundos(ffmpeg_exe, origem_local)
        duracao_final = min(duracao_real, config.DURACAO_MAXIMA_VIDEO_SEGUNDOS)

        overlay = _construir_overlay_marca(logo_path, cores_hex, nome_comercial, setor_macro)
        overlay_local = tmp_dir / "overlay.png"
        overlay.save(overlay_local, format="PNG")

        destino_local = tmp_dir / nome_final

        filtro_enquadramento = (
            f"scale={_LARGURA_SAIDA}:{_ALTURA_SAIDA}:force_original_aspect_ratio=increase,"
            f"crop={_LARGURA_SAIDA}:{_ALTURA_SAIDA}"
        )
        filtro_complexo = f"[0:v]{filtro_enquadramento}[fundo];[fundo][1:v]overlay=0:0[saida]"

        comando = [
            ffmpeg_exe,
            "-y",
            "-i", str(origem_local),
            # -t no input da imagem em loop: limita explicitamente quantos
            # frames sao gerados, evitando um loop sem fim (o -shortest
            # sozinho nao e confiavel com `-loop 1` em todas as builds do
            # ffmpeg).
            "-loop", "1", "-t", f"{duracao_final:.2f}", "-i", str(overlay_local),
            "-t", f"{duracao_final:.2f}",
            "-filter_complex", filtro_complexo,
            "-map", "[saida]",
            "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(destino_local),
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=300)
        if resultado.returncode != 0:
            raise RuntimeError(f"Falha ao processar o video com ffmpeg: {resultado.stderr[-2000:]}")

        destino = config.OUTPUT_DIR / nome_final
        shutil.copyfile(destino_local, destino)

    return str(destino)


def _duracao_segundos(ffmpeg_exe: str, origem: Path) -> float:
    """Descobre a duracao (em segundos) do video de entrada lendo o stderr
    do proprio ffmpeg (o pacote imageio-ffmpeg nao inclui o ffprobe)."""
    resultado = subprocess.run(
        [ffmpeg_exe, "-i", str(origem)], capture_output=True, text=True, timeout=30
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", resultado.stderr)
    if not match:
        return float(config.DURACAO_MAXIMA_VIDEO_SEGUNDOS)
    horas, minutos, segundos = match.groups()
    return int(horas) * 3600 + int(minutos) * 60 + float(segundos)
