import os
import sys
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

import downloader
from ui.theme import COLORS

# Aplicación fija siempre en Modo Claro
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class InverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de ventana
        self.title("Inverter • Convertidor YouTube a MP3")
        self.geometry("920x760")
        self.minsize(700, 720)
        self.configure(fg_color=COLORS["bg_light"])

        # Estado de la aplicación
        self.download_folder = str(Path.home() / "Downloads")
        self.current_video_info = None
        self.last_downloaded_file = None
        self.is_downloading = False
        self.is_fetching_info = False
        self._url_debounce_timer = None
        self._last_processed_url = ""

        # Variable reactiva para el campo de URL
        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self._on_url_text_changed)

        # Construir Interfaz
        self._build_ui()
        self._check_ffmpeg_status()
        self._set_app_icon()

        # Forzar redibujado inicial en macOS
        self.after(100, self._force_initial_redraw)

    def _set_app_icon(self):
        try:
            assets_dir = Path(__file__).parent.parent / "assets"
            if sys.platform == "win32":
                ico_file = assets_dir / "Inverter.ico"
                if ico_file.exists():
                    self.iconbitmap(str(ico_file))
            else:
                png_file = assets_dir / "Inverter.png"
                if png_file.exists():
                    from PIL import ImageTk
                    img = Image.open(png_file)
                    photo = ImageTk.PhotoImage(img)
                    self.iconphoto(False, photo)
        except Exception:
            pass

    def _force_initial_redraw(self):
        try:
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            self.geometry(f"{w}x{h+1}")
            self.geometry(f"{w}x{h}")
        except Exception:
            pass

    def _build_ui(self):
        self.main_container = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_light"],
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True, padx=24, pady=18)

        # 1. HEADER
        self._build_header()

        # 2. ENTRADA DE URL
        self._build_url_section()

        # 3. PREVIEW CARD
        self._build_preview_section()

        # 4. CARPETA DE DESTINO
        self._build_folder_section()

        # 5. PROGRESO Y ESTADO
        self._build_progress_section()

        # 6. BOTONES DE ACCIÓN
        self._build_action_buttons()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="y")

        title_label = ctk.CTkLabel(
            title_box,
            text="Inverter MP3",
            font=ctk.CTkFont(family="SF Pro Display", size=27, weight="bold"),
            text_color=COLORS["text_light"]
        )
        title_label.pack(anchor="w")

    def _build_url_section(self):
        card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["card_light"],
            border_color=COLORS["card_border_light"],
            border_width=1,
            corner_radius=14
        )
        card.pack(fill="x", pady=(0, 15), ipady=10)

        lbl = ctk.CTkLabel(
            card,
            text="Enlace del video de YouTube:",
            font=ctk.CTkFont(family="SF Pro Text", size=16, weight="bold"),
            text_color=COLORS["text_light"]
        )
        lbl.pack(anchor="w", padx=20, pady=(12, 8))

        input_row = ctk.CTkFrame(card, fg_color="transparent")
        input_row.pack(fill="x", padx=20, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(family="SF Pro Text", size=16),
            height=46,
            corner_radius=10,
            border_width=1,
            border_color=COLORS["card_border_light"]
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Botón Pegar
        btn_paste = ctk.CTkButton(
            input_row,
            text="Pegar",
            width=90,
            height=46,
            corner_radius=10,
            fg_color=COLORS["btn_secondary_light"],
            hover_color=COLORS["btn_secondary_hover_light"],
            text_color=COLORS["text_light"],
            font=ctk.CTkFont(family="SF Pro Text", size=15, weight="bold"),
            command=self._paste_from_clipboard
        )
        btn_paste.pack(side="left", padx=(0, 8))

        # Botón Limpiar
        btn_clear = ctk.CTkButton(
            input_row,
            text="✕",
            width=46,
            height=46,
            corner_radius=10,
            fg_color=COLORS["btn_secondary_light"],
            hover_color=COLORS["btn_secondary_hover_light"],
            text_color=COLORS["text_muted_light"],
            font=ctk.CTkFont(family="SF Pro Text", size=16, weight="bold"),
            command=self._clear_url
        )
        btn_clear.pack(side="left")

    def _build_preview_section(self):
        self.preview_card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["card_light"],
            border_color=COLORS["card_border_light"],
            border_width=1,
            corner_radius=14
        )
        self.preview_card.pack(fill="x", pady=(0, 15), ipady=10)

        p_header = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        p_header.pack(fill="x", padx=20, pady=(12, 10))

        lbl_section = ctk.CTkLabel(
            p_header,
            text="Vista Previa del Video",
            font=ctk.CTkFont(family="SF Pro Text", size=16, weight="bold"),
            text_color=COLORS["text_light"]
        )
        lbl_section.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            p_header,
            text="Esperando enlace...",
            font=ctk.CTkFont(family="SF Pro Text", size=14),
            text_color=COLORS["text_muted_light"]
        )
        self.status_badge.pack(side="right")

        self.preview_body = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.preview_body.pack(fill="x", padx=20, pady=(0, 12))

        # Miniatura o placeholder
        self.thumb_label = ctk.CTkLabel(
            self.preview_body,
            text="",
            width=160,
            height=90,
            corner_radius=10,
            fg_color=COLORS["btn_secondary_light"],
            font=ctk.CTkFont(size=28)
        )
        self.thumb_label.pack(side="left", padx=(0, 18))

        # Información del video
        info_frame = ctk.CTkFrame(self.preview_body, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        self.video_title_label = ctk.CTkLabel(
            info_frame,
            text="Pega un enlace de YouTube arriba para previsualizar el título",
            font=ctk.CTkFont(family="SF Pro Text", size=17, weight="bold"),
            text_color=COLORS["text_light"],
            wraplength=600,
            justify="left",
            anchor="w"
        )
        self.video_title_label.pack(fill="x", anchor="w", pady=(0, 6))

        self.video_duration_label = ctk.CTkLabel(
            info_frame,
            text="Duración: --:--",
            font=ctk.CTkFont(family="SF Pro Text", size=15),
            text_color=COLORS["text_muted_light"],
            anchor="w"
        )
        self.video_duration_label.pack(fill="x", anchor="w")

        # Calidad de audio (informativo fijo)
        quality_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        quality_frame.pack(fill="x", padx=20, pady=(4, 8))

        lbl_qual = ctk.CTkLabel(
            quality_frame,
            text="Calidad de audio:",
            font=ctk.CTkFont(family="SF Pro Text", size=15),
            text_color=COLORS["text_muted_light"]
        )
        lbl_qual.pack(side="left", padx=(0, 8))

        lbl_qual_val = ctk.CTkLabel(
            quality_frame,
            text="MP3 • 192 kbps",
            font=ctk.CTkFont(family="SF Pro Text", size=15, weight="bold"),
            text_color=COLORS["text_light"]
        )
        lbl_qual_val.pack(side="left")

    def _build_folder_section(self):
        card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["card_light"],
            border_color=COLORS["card_border_light"],
            border_width=1,
            corner_radius=14
        )
        card.pack(fill="x", pady=(0, 15), ipady=10)

        lbl = ctk.CTkLabel(
            card,
            text="Carpeta de almacenamiento:",
            font=ctk.CTkFont(family="SF Pro Text", size=16, weight="bold"),
            text_color=COLORS["text_light"]
        )
        lbl.pack(anchor="w", padx=20, pady=(12, 8))

        folder_row = ctk.CTkFrame(card, fg_color="transparent")
        folder_row.pack(fill="x", padx=20, pady=(0, 12))

        self.folder_label = ctk.CTkLabel(
            folder_row,
            text=self._shorten_path(self.download_folder),
            font=ctk.CTkFont(family="SF Pro Text", size=15),
            text_color=COLORS["text_muted_light"],
            anchor="w"
        )
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(0, 12))

        btn_browse = ctk.CTkButton(
            folder_row,
            text="Elegir Carpeta",
            height=40,
            corner_radius=10,
            fg_color=COLORS["btn_secondary_light"],
            hover_color=COLORS["btn_secondary_hover_light"],
            text_color=COLORS["text_light"],
            font=ctk.CTkFont(family="SF Pro Text", size=15, weight="bold"),
            command=self._select_folder
        )
        btn_browse.pack(side="left", padx=(0, 8))

        btn_open_folder = ctk.CTkButton(
            folder_row,
            text="Ver carpeta",
            height=40,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["card_border_light"],
            text_color=COLORS["text_muted_light"],
            font=ctk.CTkFont(family="SF Pro Text", size=14),
            command=self._open_current_folder
        )
        btn_open_folder.pack(side="left")

    def _build_progress_section(self):
        card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["card_light"],
            border_color=COLORS["card_border_light"],
            border_width=1,
            corner_radius=14
        )
        card.pack(fill="x", pady=(0, 15), ipady=8)

        p_info = ctk.CTkFrame(card, fg_color="transparent")
        p_info.pack(fill="x", padx=20, pady=(12, 8))

        self.status_detail_label = ctk.CTkLabel(
            p_info,
            text="Listo para convertir",
            font=ctk.CTkFont(family="SF Pro Text", size=15),
            text_color=COLORS["text_muted_light"],
            anchor="w"
        )
        self.status_detail_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            p_info,
            text="0%",
            font=ctk.CTkFont(family="SF Pro Text", size=15, weight="bold"),
            text_color=COLORS["text_light"]
        )
        self.percent_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            card,
            height=12,
            corner_radius=6,
            progress_color=COLORS["primary"]
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 14))

    def _build_action_buttons(self):
        action_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        action_frame.pack(fill="x", pady=(5, 12))

        # Botón 1: Descargar MP3 (Rojo #ab2722 con texto blanco puro #ffffff)
        self.btn_download = ctk.CTkButton(
            action_frame,
            text="Descargar MP3",
            height=52,
            corner_radius=12,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#ffffff",
            font=ctk.CTkFont(family="SF Pro Text", size=17, weight="bold"),
            command=self._start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Botón 2: Se activa cuando la descarga esté lista
        self.btn_ready = ctk.CTkButton(
            action_frame,
            text="Abrir Archivo MP3",
            height=52,
            corner_radius=12,
            state="disabled",
            fg_color=COLORS["btn_secondary_light"],
            hover_color=COLORS["success_hover"],
            text_color_disabled=COLORS["text_muted_light"],
            font=ctk.CTkFont(family="SF Pro Text", size=17, weight="bold"),
            command=self._open_ready_file
        )
        self.btn_ready.pack(side="left", fill="x", expand=True)

    # -------------------------------------------------------------
    # GESTIÓN REACTIVA DE ENLACE Y METADATA
    # -------------------------------------------------------------
    def _on_url_text_changed(self, *args):
        raw_url = self.url_var.get().strip()

        if self._url_debounce_timer:
            self.after_cancel(self._url_debounce_timer)

        if not raw_url:
            self._clear_preview_state()
            return

        if downloader.is_valid_youtube_url(raw_url):
            clean_url = downloader.clean_youtube_url(raw_url)
            if clean_url != self._last_processed_url:
                self._url_debounce_timer = self.after(350, lambda: self._fetch_metadata_async(clean_url))

    def _paste_from_clipboard(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_var.set(clipboard)
        except Exception:
            pass

    def _clear_url(self):
        self.url_var.set("")
        self._clear_preview_state()

    def _clear_preview_state(self):
        self._last_processed_url = ""
        self.current_video_info = None
        self.video_title_label.configure(text="Pega un enlace de YouTube arriba para previsualizar el título")
        self.video_duration_label.configure(text="Duración: --:--")
        self.status_badge.configure(text="Esperando enlace...", text_color=COLORS["text_muted_light"])
        self.thumb_label.configure(image=None, text="")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.status_detail_label.configure(text="Listo para convertir", text_color=COLORS["text_muted_light"])
        self.btn_download.configure(state="normal", text="Descargar MP3")

    def _fetch_metadata_async(self, clean_url: str):
        if self.is_fetching_info or self.is_downloading:
            return

        self._last_processed_url = clean_url
        self.is_fetching_info = True

        self.status_badge.configure(text="Obteniendo datos...", text_color=COLORS["accent_subtle"])
        self.status_detail_label.configure(text="Consultando título y duración del video...")
        self.video_title_label.configure(text="Cargando información del video...")
        self.btn_download.configure(state="disabled", text="Cargando información...")

        def worker():
            try:
                info = downloader.fetch_video_metadata(clean_url)
                thumb_img = None
                if info.get('thumbnail_url'):
                    thumb_img = downloader.download_thumbnail_image(info['thumbnail_url'])
                self.after(0, lambda: self._on_metadata_success(info, thumb_img))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._on_metadata_error(err_msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_metadata_success(self, info: dict, thumb_img):
        self.is_fetching_info = False
        self.current_video_info = info
        self.status_badge.configure(text="✓ Video encontrado", text_color=COLORS["success"])
        self.video_title_label.configure(text=info['title'])
        self.video_duration_label.configure(text=f"Duración: {info['duration']}")
        self.status_detail_label.configure(text="Listo para descargar y convertir a MP3")
        self.btn_download.configure(state="normal", text="Descargar MP3")

        if thumb_img:
            ctk_img = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(160, 90))
            self.thumb_label.configure(image=ctk_img, text="")
        else:
            self.thumb_label.configure(image=None, text="")

    def _on_metadata_error(self, err_msg: str):
        self.is_fetching_info = False
        self.status_badge.configure(text="Error al consultar video", text_color=COLORS["error"])
        self.video_title_label.configure(text="No se pudo obtener información de este video")
        self.status_detail_label.configure(text="Verifica tu conexión o el enlace de YouTube")
        self.btn_download.configure(state="normal", text="Descargar MP3")

    def _check_ffmpeg_status(self):
        ffmpeg_path = downloader.get_ffmpeg_binary_path()
        if not ffmpeg_path:
            self.status_detail_label.configure(
                text="⚠️ FFmpeg no encontrado. Conversión a MP3 podría fallar.",
                text_color=COLORS["error"]
            )

    def _shorten_path(self, path: str, max_chars=55) -> str:
        if len(path) <= max_chars:
            return path
        return "..." + path[-(max_chars - 3):]

    def _select_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.download_folder,
            title="Selecciona la carpeta donde guardar los archivos MP3"
        )
        if folder:
            self.download_folder = folder
            self.folder_label.configure(text=self._shorten_path(self.download_folder))

    def _open_current_folder(self):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", self.download_folder])
            elif sys.platform == "win32":
                os.startfile(self.download_folder)
            else:
                subprocess.Popen(["xdg-open", self.download_folder])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")

    # -------------------------------------------------------------
    # DESCARGA Y CONVERSIÓN
    # -------------------------------------------------------------
    def _start_download(self):
        raw_url = self.url_var.get().strip()
        if not raw_url:
            messagebox.showwarning("Atención", "Por favor ingresa un enlace de YouTube.")
            return

        if not downloader.is_valid_youtube_url(raw_url):
            messagebox.showwarning("Enlace inválido", "El enlace no corresponde a un video válido de YouTube.")
            return

        if self.is_downloading:
            return

        clean_url = downloader.clean_youtube_url(raw_url)
        bitrate = "192"

        self.is_downloading = True
        self.btn_download.configure(state="disabled", text="Descargando...")
        self.btn_ready.configure(
            state="disabled",
            text="Esperando descarga...",
            fg_color=COLORS["btn_secondary_light"]
        )
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.status_detail_label.configure(text="Iniciando descarga de audio...")

        def progress_cb(percent, speed_str, eta_str):
            frac = max(0.0, min(1.0, percent / 100.0))
            def update():
                self.progress_bar.set(frac)
                self.percent_label.configure(text=f"{int(percent)}%")
                if eta_str or speed_str:
                    self.status_detail_label.configure(text=f"Descargando audio: {speed_str} • {eta_str}")
                else:
                    self.status_detail_label.configure(text="Procesando...")
            self.after(0, update)

        def completion_cb(filepath):
            self.after(0, lambda: self._on_download_complete(filepath))

        def error_cb(err):
            self.after(0, lambda: self._on_download_error(err))

        def worker():
            downloader.download_mp3(
                url=clean_url,
                output_folder=self.download_folder,
                bitrate=bitrate,
                progress_callback=progress_cb,
                completion_callback=completion_cb,
                error_callback=error_cb
            )

        threading.Thread(target=worker, daemon=True).start()

    def _on_download_complete(self, filepath: str):
        self.is_downloading = False
        self.last_downloaded_file = filepath

        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")
        self.status_detail_label.configure(
            text="¡Descarga y conversión completadas con éxito!",
            text_color=COLORS["success"]
        )

        self.btn_download.configure(state="normal", text="Descargar Otro")

        self.btn_ready.configure(
            state="normal",
            text="¡Listo! Abrir Archivo MP3",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            text_color="#ffffff"
        )

    def _on_download_error(self, error_msg: str):
        self.is_downloading = False
        self.btn_download.configure(state="normal", text="Reintentar Descarga")
        self.status_detail_label.configure(
            text=f"Error: {error_msg[:60]}...",
            text_color=COLORS["error"]
        )
        messagebox.showerror("Error al descargar", f"Ocurrió un error durante la descarga o conversión:\n{error_msg}")

    def _open_ready_file(self):
        if not self.last_downloaded_file or not os.path.exists(self.last_downloaded_file):
            self._open_current_folder()
            return

        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", self.last_downloaded_file])
            elif sys.platform == "win32":
                os.startfile(self.last_downloaded_file)
            else:
                subprocess.Popen(["xdg-open", self.last_downloaded_file])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")


def launch():
    app = InverterApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
