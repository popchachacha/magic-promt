from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    """Design tokens for the pink/snowy UI theme."""

    color_background: str = "#F7F9FB"
    color_panel: str = "#FFFFFFCC"
    color_primary: str = "#FF76B8"
    color_primary_dark: str = "#E0539C"
    color_text: str = "#2F2A38"
    color_text_muted: str = "#6C5E79"
    color_border: str = "#E3E7ED"
    shadow: str = "0px 10px 30px rgba(255, 118, 184, 0.1)"
    radius: str = "14px"


def build_stylesheet(tokens: ThemeTokens | None = None) -> str:
    """Generate a Qt Style Sheet based on design tokens."""
    tokens = tokens or ThemeTokens()
    return f"""
        QMainWindow {{
            background-color: {tokens.color_background};
        }}
        QWidget#Panel {{
            background-color: {tokens.color_panel};
            border: 1px solid {tokens.color_border};
            border-radius: {tokens.radius};
        }}
        QLabel {{
            color: {tokens.color_text};
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}
        QListWidget {{
            background-color: transparent;
            border: none;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 10px;
        }}
        QListWidget::item:selected {{
            background-color: {tokens.color_primary};
            color: white;
        }}
        QPushButton {{
            background-color: {tokens.color_primary};
            color: white;
            border-radius: 12px;
            padding: 10px 16px;
            font-weight: 600;
        }}
        QPushButton#GhostButton {{
            background-color: transparent;
            color: {tokens.color_primary};
            border: 1px solid {tokens.color_primary};
        }}
    """
