import streamlit as st
from pathlib import Path

def get_nexa_logo() -> str:
    """Return the file path to the appropriate Nexa logo SVG.
    Streamlit exposes the selected theme via ``st.get_option('theme.base')``
    when a theme is configured in ``.streamlit/config.toml`` or via the UI.
    If the theme is ``dark`` we use the dark logo, otherwise the light logo.
    """
    assets_dir = Path(__file__).parent / "assets" / "images"
    # Default to light logo
    logo_path = assets_dir / "logo_nexa_light.svg"
    try:
        if st.get_option("theme.base") == "dark":
            logo_path = assets_dir / "logo_nexa_dark.svg"
    except Exception:
        # Fallback: keep default light logo
        pass
    return str(logo_path)
