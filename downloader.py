import os
import shutil
import io
import re
import urllib.parse
import requests
from PIL import Image
import yt_dlp

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


def get_ffmpeg_binary_path():
    """Localiza el binario de FFmpeg en el sistema o en imageio-ffmpeg."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    if imageio_ffmpeg:
        try:
            bundled = imageio_ffmpeg.get_ffmpeg_exe()
            if bundled and os.path.exists(bundled):
                return bundled
        except Exception:
            pass
    return None


def clean_youtube_url(url: str) -> str:
    """
    Limpia la URL para extraer ÚNICAMENTE el video individual,
    removiendo listas de reproducción, mixes (list=RD...), índices, radios, etc.
    """
    if not url:
        return ""
    
    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
        
        # Caso youtu.be/<id>
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.strip("/").split("/")[0].split("?")[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
                
        # Caso youtube.com/watch?v=<id>
        if "youtube.com" in parsed.netloc:
            # Caso youtube.com/shorts/<id>
            if "/shorts/" in parsed.path:
                parts = parsed.path.split("/shorts/")
                if len(parts) > 1:
                    video_id = parts[1].strip("/").split("?")[0]
                    return f"https://www.youtube.com/watch?v={video_id}"
            
            qs = urllib.parse.parse_qs(parsed.query)
            if "v" in qs and qs["v"]:
                video_id = qs["v"][0]
                return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass

    # Si no tiene formato reconocible especial, limpiamos parámetros de playlist con regex
    cleaned = re.sub(r'([&?])(list=[^&]+|index=[^&]+|start_radio=[^&]+)', '', url)
    cleaned = cleaned.rstrip('?&')
    return cleaned


def is_valid_youtube_url(url: str) -> bool:
    """Valida si la cadena parece ser un enlace válido de YouTube."""
    if not url:
        return False
    cleaned = clean_youtube_url(url)
    patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+',
        r'youtu\.be/[a-zA-Z0-9_-]+',
    ]
    return any(re.search(p, cleaned) for p in patterns)


def fetch_video_metadata(url: str):
    """
    Extrae la información básica de un ÚNICO video sin descargarlo.
    """
    clean_url = clean_youtube_url(url)
    
    ydl_opts = {
        'skip_download': True,
        'noplaylist': True,           # NUNCA descargar ni parsear playlists
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_url, download=False)
        if not info:
            raise ValueError("No se pudo obtener la información del video.")

        # Si aún así viniera envuelto en una entrada, tomar solo la primera
        if 'entries' in info and info['entries']:
            info = info['entries'][0]

        title = info.get('title', 'Video sin título')
        uploader = info.get('uploader') or info.get('channel') or 'Canal desconocido'
        duration = info.get('duration', 0)

        if duration:
            m, s = divmod(int(duration), 60)
            h, m = divmod(m, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        else:
            duration_str = "--:--"

        thumbnail_url = info.get('thumbnail')
        thumbnails = info.get('thumbnails', [])
        if thumbnails:
            preferred = [t['url'] for t in thumbnails if 'url' in t]
            if preferred:
                thumbnail_url = preferred[-1]

        return {
            'title': title,
            'channel': uploader,
            'duration': duration_str,
            'thumbnail_url': thumbnail_url,
            'url': clean_url,
            'id': info.get('id', '')
        }


def download_thumbnail_image(url: str, size=(160, 90)):
    """Descarga la miniatura del video."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=6)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img = img.convert("RGBA")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def download_mp3(url: str, output_folder: str, bitrate="192",
                 progress_callback=None, completion_callback=None, error_callback=None):
    """
    Descarga el audio de UN SOLO video de YouTube y lo convierte a MP3.
    Garantiza 'noplaylist': True para evitar descargar mezclas o recomendaciones.
    """
    clean_url = clean_youtube_url(url)
    ffmpeg_path = get_ffmpeg_binary_path()
    if not ffmpeg_path:
        if error_callback:
            error_callback("No se encontró el motor de conversión FFmpeg.")
        return

    os.makedirs(output_folder, exist_ok=True)
    final_file = {"path": None}

    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = (downloaded / total * 100) if total > 0 else 0
            speed = d.get('speed')
            speed_str = f"{(speed / 1024 / 1024):.1f} MB/s" if speed else ""
            eta = d.get('eta')
            eta_str = f"{eta}s restantes" if eta is not None else ""

            if progress_callback:
                progress_callback(percent, speed_str, eta_str)

        elif d['status'] == 'finished':
            if progress_callback:
                progress_callback(100.0, "Conversión", "Convirtiendo audio a MP3 con FFmpeg...")

    out_tmpl = os.path.join(output_folder, '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'noplaylist': True,           # ESTRICTO: Descargar SOLO el video solicitado
        'ffmpeg_location': ffmpeg_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(bitrate),
        }],
        'progress_hooks': [hook],
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            temp_name = ydl.prepare_filename(info)
            base, _ = os.path.splitext(temp_name)
            expected_mp3 = f"{base}.mp3"

            if os.path.exists(expected_mp3):
                final_file["path"] = expected_mp3
            else:
                final_file["path"] = output_folder

        if completion_callback:
            completion_callback(final_file["path"])

    except Exception as e:
        if error_callback:
            error_callback(str(e))
