"""
Definición de colores y estilos para la aplicación Inverter.
Paleta con acento rojo #ab2722 y textos blancos puros de alto contraste.
"""

COLORS = {
    # Fondos (Modo Claro)
    "bg_dark": "#f4f5f8",
    "bg_light": "#f4f5f8",
    
    # Contenedores / Tarjetas
    "card_dark": "#ffffff",
    "card_light": "#ffffff",
    "card_border_dark": "#e2e6ea",
    "card_border_light": "#e2e6ea",
    
    # Acentos principales (Rojo personalizado)
    "primary": "#ab2722",
    "primary_hover": "#8f1f1b",
    "primary_soft": "#FDE8E7",
    
    # Éxito
    "success": "#10B981",
    "success_hover": "#059669",
    "success_soft": "#D1FAE5",
    
    # Textos (Blanco puro #ffffff en vez de grises apagados)
    "text_white": "#ffffff",
    "text_dark": "#ffffff",
    "text_light": "#1E293B",
    "text_muted_dark": "#e2e8f0",
    "text_muted_light": "#64748B",
    
    # Botones secundarios
    "btn_secondary_dark": "#EAEFF5",
    "btn_secondary_light": "#EAEFF5",
    "btn_secondary_hover_dark": "#DEE4EC",
    "btn_secondary_hover_light": "#DEE4EC",
    
    # Indicadores
    "accent_subtle": "#ab2722",
    "progress_bg_dark": "#e2e8f0",
    "progress_bg_light": "#e2e8f0",
    "error": "#EF4444",
}

FONTS = {
    "title": ("SF Pro Display", 27, "bold"),
    "section": ("SF Pro Text", 16, "bold"),
    "body": ("SF Pro Text", 16),
    "body_bold": ("SF Pro Text", 16, "bold"),
    "button": ("SF Pro Text", 17, "bold"),
    "button_sm": ("SF Pro Text", 15, "bold"),
    "caption": ("SF Pro Text", 14),
    "detail": ("SF Pro Text", 15),
}
